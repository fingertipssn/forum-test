from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text

from .base import Service
from .markdown_renderer import render, count_words
from ..models.topic import Topic
from ..models.post import Post
from ..models.user import User
from ..core.guardian import Guardian


class PostCreatorService(Service):
    steps = [
        "validate_params",
        "load_topic",
        "check_permissions",
        "compute_post_number",
        "create_post",
        "update_topic",
        "update_user_stats",
        "index_search",
        "enqueue_jobs",
    ]

    def __init__(
        self,
        *,
        db: AsyncSession,
        user: User,
        guardian: Guardian,
        topic_id: int,
        raw: str,
        reply_to_post_number: Optional[int] = None,
    ):
        super().__init__()
        self.db = db
        self.user = user
        self.guardian = guardian
        self.topic_id = topic_id
        self.raw = raw
        self.reply_to_post_number = reply_to_post_number
        self.topic: Optional[Topic] = None
        self.post: Optional[Post] = None
        self.next_post_number: int = 1

    async def validate_params(self):
        from ..core.config import settings

        raw = (self.raw or "").strip()
        if not raw:
            self.fail("Post body cannot be empty")
        if len(raw) > settings.MAX_POST_LENGTH:
            self.fail(f"Post is too long (maximum {settings.MAX_POST_LENGTH} characters)")
        self.raw = raw

    async def load_topic(self):
        result = await self.db.execute(select(Topic).where(Topic.id == self.topic_id))
        self.topic = result.scalar_one_or_none()
        if self.topic is None:
            self.fail("Topic not found")

    async def check_permissions(self):
        self.guardian.ensure_can_create_post(self.topic)

    async def compute_post_number(self):
        self.next_post_number = (self.topic.highest_post_number or 0) + 1

    async def create_post(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        cooked = render(self.raw)

        reply_to_user_id: Optional[int] = None
        if self.reply_to_post_number:
            result = await self.db.execute(
                select(Post).where(
                    Post.topic_id == self.topic_id,
                    Post.post_number == self.reply_to_post_number,
                )
            )
            reply_post = result.scalar_one_or_none()
            if reply_post:
                reply_to_user_id = reply_post.user_id

        self.post = Post(
            user_id=self.user.id,
            topic_id=self.topic.id,
            post_number=self.next_post_number,
            raw=self.raw,
            cooked=cooked,
            reply_to_post_number=self.reply_to_post_number,
            reply_to_user_id=reply_to_user_id,
            post_type=1,
            version=1,
            public_version=1,
            cook_method=1,
            hidden=False,
            wiki=False,
            user_deleted=False,
            reply_quoted=False,
            via_email=False,
            reply_count=0,
            like_count=0,
            reads=0,
            word_count=count_words(self.raw),
            last_version_at=now,
            baked_at=now,
            created_at=now,
            updated_at=now,
        )
        self.db.add(self.post)
        await self.db.flush()

    async def update_topic(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.db.execute(
            update(Topic)
            .where(Topic.id == self.topic.id)
            .values(
                posts_count=Topic.posts_count + 1,
                reply_count=Topic.reply_count + 1,
                highest_post_number=self.next_post_number,
                highest_staff_post_number=self.next_post_number,
                last_post_user_id=self.user.id,
                last_posted_at=now,
                bumped_at=now,
                updated_at=now,
            )
        )

        if self.reply_to_post_number:
            await self.db.execute(
                update(Post)
                .where(
                    Post.topic_id == self.topic_id,
                    Post.post_number == self.reply_to_post_number,
                )
                .values(reply_count=Post.reply_count + 1)
            )

    async def update_user_stats(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.db.execute(
            update(User).where(User.id == self.user.id).values(updated_at=now)
        )

    async def index_search(self):
        import logging
        raw_data = self.raw
        # search_data es tsvector: usamos to_tsvector() y savepoint para no revertir el post
        try:
            await self.db.execute(text("SAVEPOINT sp_search"))
            await self.db.execute(
                text("""
                    INSERT INTO post_search_data (post_id, search_data, raw_data, locale, version, private_message)
                    VALUES (:post_id, to_tsvector('english', :raw_data), :raw_data, 'english', 1, false)
                """),
                {"post_id": self.post.id, "raw_data": raw_data},
            )
            await self.db.execute(text("RELEASE SAVEPOINT sp_search"))
        except Exception as e:
            await self.db.execute(text("ROLLBACK TO SAVEPOINT sp_search"))
            logging.getLogger(__name__).warning("No se pudo indexar post_search_data: %s", e)

    async def enqueue_jobs(self):
        from ..core.config import settings
        if settings.CELERY_ENABLED:
            try:
                from ..tasks.process_post import process_post_task
                process_post_task.delay(self.post.id)
            except Exception:
                pass

        self.context.result = {"post": self.post}
