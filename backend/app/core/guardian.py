from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from fastapi import HTTPException, status

if TYPE_CHECKING:
    from ..models.user import User
    from ..models.topic import Topic
    from ..models.post import Post
    from ..models.category import Category


class PermissionDenied(HTTPException):
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class Guardian:
    def __init__(self, user: Optional["User"] = None):
        self.user = user

    # ── Identity helpers ────────────────────────────────────────────────────

    @property
    def is_authenticated(self) -> bool:
        return self.user is not None

    @property
    def is_admin(self) -> bool:
        return self.user is not None and bool(self.user.admin)

    @property
    def is_moderator(self) -> bool:
        return self.user is not None and bool(self.user.moderator)

    @property
    def is_staff(self) -> bool:
        return self.is_admin or self.is_moderator

    @property
    def is_silenced(self) -> bool:
        if self.user is None:
            return False
        till = getattr(self.user, "silenced_till", None)
        if till is None:
            return False
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        return till > now

    @property
    def is_suspended(self) -> bool:
        if self.user is None:
            return False
        till = getattr(self.user, "suspended_till", None)
        if till is None:
            return False
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        return till > now

    # ── Category permissions ─────────────────────────────────────────────────

    def can_see_category(self, category: "Category") -> bool:
        if not category.read_restricted:
            return True
        return self.is_staff

    # ── Topic permissions ────────────────────────────────────────────────────

    def can_see_topic(self, topic: "Topic", category: Optional["Category"] = None) -> bool:
        if topic.deleted_at is not None and not self.is_staff:
            return False
        if not topic.visible and not self.is_staff:
            return False
        if category is not None:
            return self.can_see_category(category)
        return True

    def can_create_topic(self, category: Optional["Category"] = None) -> bool:
        if not self.is_authenticated:
            return False
        if self.is_silenced or self.is_suspended:
            return False
        if category is not None and not self.can_see_category(category):
            return False
        return True

    def can_edit_topic(self, topic: "Topic") -> bool:
        if not self.is_authenticated:
            return False
        if self.is_staff:
            return True
        return topic.user_id == self.user.id and topic.deleted_at is None

    def can_delete_topic(self, topic: "Topic") -> bool:
        if not self.is_authenticated:
            return False
        if self.is_staff:
            return True
        return topic.user_id == self.user.id and topic.deleted_at is None

    # ── Post permissions ─────────────────────────────────────────────────────

    def can_create_post(self, topic: "Topic") -> bool:
        if not self.is_authenticated:
            return False
        if self.is_silenced or self.is_suspended:
            return False
        if topic.closed and not self.is_staff:
            return False
        if topic.archived and not self.is_staff:
            return False
        if topic.deleted_at is not None:
            return False
        return True

    def can_edit_post(self, post: "Post") -> bool:
        if not self.is_authenticated:
            return False
        if self.is_staff:
            return True
        if post.deleted_at is not None:
            return False
        return post.user_id == self.user.id

    def can_delete_post(self, post: "Post") -> bool:
        if not self.is_authenticated:
            return False
        if self.is_staff:
            return True
        if post.deleted_at is not None:
            return False
        return post.user_id == self.user.id

    # ── ensure_can helpers (raise on failure) ────────────────────────────────

    def ensure_authenticated(self) -> None:
        if not self.is_authenticated:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    def ensure_can_see_topic(self, topic: "Topic", category: Optional["Category"] = None) -> None:
        if not self.can_see_topic(topic, category):
            raise PermissionDenied("You do not have permission to view this topic")

    def ensure_can_create_topic(self, category: Optional["Category"] = None) -> None:
        if not self.can_create_topic(category):
            raise PermissionDenied("You do not have permission to create a topic here")

    def ensure_can_create_post(self, topic: "Topic") -> None:
        if not self.can_create_post(topic):
            raise PermissionDenied("You do not have permission to reply to this topic")

    def ensure_can_edit_post(self, post: "Post") -> None:
        if not self.can_edit_post(post):
            raise PermissionDenied("You do not have permission to edit this post")

    def ensure_can_delete_post(self, post: "Post") -> None:
        if not self.can_delete_post(post):
            raise PermissionDenied("You do not have permission to delete this post")

    def ensure_staff(self) -> None:
        if not self.is_staff:
            raise PermissionDenied("Staff access required")


def get_guardian(user: Optional["User"] = None) -> Guardian:
    return Guardian(user=user)
