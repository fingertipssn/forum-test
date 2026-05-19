import logging
import os
import re
import hashlib
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import sessionmaker

from .celery_app import celery_app
from ..core.config import settings

logger = logging.getLogger(__name__)

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}

_engine = None
_Session = None


def _get_session():
    global _engine, _Session
    if _engine is None:
        _engine = create_engine(settings.DATABASE_URL_SYNC, pool_pre_ping=True)
        _Session = sessionmaker(_engine)
    return _Session()


@celery_app.task(name="pull_hotlinked_images", bind=True, max_retries=3)
def pull_hotlinked_images_task(self, post_id: int):
    from ..models.post import Post
    from ..services.markdown_renderer import render

    logger.info("PullHotlinkedImages: post_id=%d", post_id)

    if not _check_disk_space():
        logger.warning("PullHotlinkedImages: insufficient disk space, skipping")
        return

    session = _get_session()
    try:
        post = session.execute(select(Post).where(Post.id == post_id)).scalar_one_or_none()
        if post is None:
            return

        raw = post.raw
        pattern = re.compile(r"(!\[.*?\])\((https?://[^)]+)\)", re.IGNORECASE)
        changed = False

        def replace_url(match):
            nonlocal changed
            alt_text = match.group(1)
            url = match.group(2)
            local_url = _download_image(url)
            if local_url:
                changed = True
                return f"{alt_text}({local_url})"
            return match.group(0)

        new_raw = pattern.sub(replace_url, raw)

        if changed:
            new_cooked = render(new_raw)
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            session.execute(
                update(Post)
                .where(Post.id == post_id)
                .values(raw=new_raw, cooked=new_cooked, updated_at=now)
            )
            session.commit()
            logger.info("PullHotlinkedImages: updated post_id=%d with %d local images", post_id, changed)

    except Exception as exc:
        session.rollback()
        logger.exception("PullHotlinkedImages: failed post_id=%d", post_id)
        raise self.retry(exc=exc, countdown=120)
    finally:
        session.close()


def _check_disk_space(min_free_mb: int = 200) -> bool:
    try:
        stat = os.statvfs(settings.UPLOADS_PATH)
        free_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
        return free_mb >= min_free_mb
    except Exception:
        return True  # assume ok on Windows


def _download_image(url: str) -> str | None:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return None

        if parsed.netloc in _get_blocked_domains():
            return None

        resp = requests.get(url, timeout=15, stream=True)
        resp.raise_for_status()

        content_type = resp.headers.get("content-type", "").split(";")[0].strip()
        if content_type not in ALLOWED_CONTENT_TYPES:
            logger.debug("PullHotlinkedImages: skipping %s (content-type=%s)", url, content_type)
            return None

        content = b""
        for chunk in resp.iter_content(65536):
            content += chunk
            if len(content) > MAX_IMAGE_SIZE:
                logger.warning("PullHotlinkedImages: image too large: %s", url)
                return None

        ext = mimetypes.guess_extension(content_type) or ".jpg"
        filename = hashlib.sha256(content).hexdigest()[:16] + ext
        uploads_dir = Path(settings.UPLOADS_PATH) / "hotlinked"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        dest = uploads_dir / filename

        if not dest.exists():
            dest.write_bytes(content)

        return f"{settings.SITE_BASE_URL}/uploads/hotlinked/{filename}"

    except requests.RequestException as exc:
        logger.warning("PullHotlinkedImages: failed to download %s: %s", url, exc)
        return None


def _get_blocked_domains() -> set[str]:
    return {"spam.example.com"}
