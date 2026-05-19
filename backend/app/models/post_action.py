from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, Integer, BigInteger, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base

# post_action_type_id constants (same as Discourse)
LIKE_TYPE_ID = 2
BOOKMARK_TYPE_ID = 7


class PostAction(Base):
    __tablename__ = "post_actions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    post_action_type_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_by_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    related_post_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    staff_took_action: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    deferred_by_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    targets_topic: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    agreed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    agreed_by_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    deferred_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    disagreed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    disagreed_by_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
