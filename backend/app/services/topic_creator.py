from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from .base import Service
from .markdown_renderer import render, extract_excerpt, count_words
from ..models.topic import Topic
from ..models.post import Post
from ..models.user import User
from ..models.category import Category
from ..core.guardian import Guardian


def _slugify(title: str) -> str:
    import re
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:80] or "topic"


class TopicCreatorService(Service):
    steps = [
        "validate_params",
        "check_permissions",
        "load_category",
        "create_topic",
        "create_first_post",
        "update_counters",
        "index_search",
        "enqueue_jobs",
    ]

    def __init__(
        self,
        *,
        db: AsyncSession,
        user: User,
        guardian: Guardian,
        title: str,
        raw: str,
        category_id: Optional[int] = None,
    ):
        super().__init__()
        self.db = db
        self.user = user
        self.guardian = guardian
        self.title = title
        self.raw = raw
        self.category_id = category_id
        self.category: Optional[Category] = None
        self.topic: Optional[Topic] = None
        self.post: Optional[Post] = None

    async def validate_params(self):
        from ..core.config import settings

        title = (self.title or "").strip()
        if len(title) < settings.MIN_TOPIC_TITLE_LENGTH:
            self.fail(f"Title is too short (minimum {settings.MIN_TOPIC_TITLE_LENGTH} characters)")
        if len(title) > settings.MAX_TOPIC_TITLE_LENGTH:
            self.fail(f"Title is too long (maximum {settings.MAX_TOPIC_TITLE_LENGTH} characters)")

        raw = (self.raw or "").strip()
        if not raw:
            self.fail("Post body cannot be empty")
        if len(raw) > settings.MAX_POST_LENGTH:
            self.fail(f"Post is too long (maximum {settings.MAX_POST_LENGTH} characters)")

        self.title = title
        self.raw = raw

    async def check_permissions(self):
        self.guardian.ensure_can_create_topic(self.category)

    async def load_category(self):
        if self.category_id is not None:
            result = await self.db.execute(
                select(Category).where(Category.id == self.category_id)
            )
            self.category = result.scalar_one_or_none()
            if self.category is None:
                self.fail("Category not found")
        else:
            # La tabla topics tiene un CHECK constraint has_category_id que exige
            # category_id NOT NULL. Si no se envía categoría, usamos la primera disponible.
            result = await self.db.execute(
                select(Category)
                .where(Category.parent_category_id.is_(None))
                .order_by(Category.position.asc(), Category.id.asc())
                .limit(1)
            )
            self.category = result.scalar_one_or_none()
            if self.category is None:
                self.fail("No hay categorías disponibles en el foro")
            self.category_id = self.category.id

    async def create_topic(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        cooked = render(self.raw)
        slug = _slugify(self.title)

        self.topic = Topic(
            title=self.title,
            fancy_title=self.title,
            slug=slug,
            excerpt=extract_excerpt(cooked),
            user_id=self.user.id,
            last_post_user_id=self.user.id,
            category_id=self.category_id,
            posts_count=1,
            reply_count=0,
            highest_post_number=1,
            highest_staff_post_number=1,
            views=0,
            like_count=0,
            visible=True,
            closed=False,
            archived=False,
            pinned_globally=False,
            archetype="regular",
            bumped_at=now,
            last_posted_at=now,
            created_at=now,
            updated_at=now,
        )
        self.db.add(self.topic)
        await self.db.flush()

    async def create_first_post(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        cooked = render(self.raw)

        self.post = Post(
            user_id=self.user.id,
            topic_id=self.topic.id,
            post_number=1,
            raw=self.raw,
            cooked=cooked,
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

    async def update_counters(self):
        from sqlalchemy import update

        await self.db.execute(
            update(User)
            .where(User.id == self.user.id)
            .values(updated_at=datetime.now(timezone.utc).replace(tzinfo=None))
        )
        if self.category is not None:
            await self.db.execute(
                update(Category)
                .where(Category.id == self.category.id)
                .values(
                    topic_count=Category.topic_count + 1,
                    post_count=Category.post_count + 1,
                    latest_topic_id=self.topic.id,
                    updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
                )
            )

    async def index_search(self):
        raw_data = f"{self.title} {self.raw}"
        # search_data es tsvector: usamos to_tsvector() y savepoints para no revertir el topic
        for stmt, params, label in [
            (
                text("""
                    INSERT INTO post_search_data (post_id, search_data, raw_data, locale, version, private_message)
                    VALUES (:post_id, to_tsvector('english', :raw_data), :raw_data, 'english', 1, false)
                """),
                {"post_id": self.post.id, "raw_data": raw_data},
                "post_search_data",
            ),
            (
                text("""
                    INSERT INTO topic_search_data (topic_id, search_data, raw_data, locale, version)
                    VALUES (:topic_id, to_tsvector('english', :raw_data), :raw_data, 'english', 1)
                """),
                {"topic_id": self.topic.id, "raw_data": raw_data},
                "topic_search_data",
            ),
        ]:
            try:
                await self.db.execute(text("SAVEPOINT sp_search"))
                await self.db.execute(stmt, params)
                await self.db.execute(text("RELEASE SAVEPOINT sp_search"))
            except Exception as e:
                await self.db.execute(text("ROLLBACK TO SAVEPOINT sp_search"))
                import logging
                logging.getLogger(__name__).warning("No se pudo indexar %s: %s", label, e)

    async def enqueue_jobs(self):
        from ..core.config import settings
        if settings.CELERY_ENABLED:
            try:
                from ..tasks.process_post import process_post_task
                process_post_task.delay(self.post.id)
            except Exception:
                pass

        self.context.result = {"topic": self.topic, "post": self.post}
