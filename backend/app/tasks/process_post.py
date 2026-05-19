import logging
from datetime import datetime, timezone

from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import sessionmaker

from .celery_app import celery_app
from ..core.config import settings
from ..services.markdown_renderer import render, count_words

logger = logging.getLogger(__name__)

_engine = None
_Session = None


def _get_session():
    global _engine, _Session
    if _engine is None:
        _engine = create_engine(settings.DATABASE_URL_SYNC, pool_pre_ping=True)
        _Session = sessionmaker(_engine)
    return _Session()


@celery_app.task(name="process_post", bind=True, max_retries=3)
def process_post_task(self, post_id: int):
    from ..models.post import Post, PostSearchData

    logger.info("ProcessPost: post_id=%d", post_id)
    session = _get_session()
    try:
        post = session.execute(select(Post).where(Post.id == post_id)).scalar_one_or_none()
        if post is None:
            logger.warning("ProcessPost: post %d not found (probably deleted)", post_id)
            return

        new_cooked = render(post.raw)
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        updates = {
            "cooked": new_cooked,
            "word_count": count_words(post.raw),
            "baked_at": now,
            "baked_version": (post.baked_version or 0) + 1,
            "updated_at": now,
        }
        session.execute(update(Post).where(Post.id == post_id).values(**updates))

        psd = session.execute(
            select(PostSearchData).where(PostSearchData.post_id == post_id)
        ).scalar_one_or_none()
        if psd is None:
            psd = PostSearchData(
                post_id=post_id,
                raw_data=post.raw,
                locale="english",
                version=1,
            )
            session.add(psd)
        else:
            session.execute(
                update(PostSearchData)
                .where(PostSearchData.post_id == post_id)
                .values(raw_data=post.raw, version=(psd.version or 0) + 1)
            )

        session.commit()
        logger.info("ProcessPost: completed post_id=%d", post_id)

        if _has_external_images(post.raw):
            from .pull_hotlinked_images import pull_hotlinked_images_task
            pull_hotlinked_images_task.delay(post_id)

    except Exception as exc:
        session.rollback()
        logger.exception("ProcessPost: failed post_id=%d", post_id)
        raise self.retry(exc=exc, countdown=60)
    finally:
        session.close()


def _has_external_images(raw: str) -> bool:
    import re
    pattern = re.compile(r"!\[.*?\]\((https?://[^)]+)\)", re.IGNORECASE)
    return bool(pattern.search(raw))
