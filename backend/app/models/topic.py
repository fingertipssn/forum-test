from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.database import Base


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    fancy_title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    slug: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    excerpt: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_post_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    deleted_by_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    posts_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reply_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    highest_post_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    highest_staff_post_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    incoming_link_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    participant_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    moderator_posts_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notify_moderators_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    spam_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_summary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    pinned_globally: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    archetype: Mapped[str] = mapped_column(String, default="regular", nullable=False)
    subtype: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    percent_rank: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    reviewable_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    pinned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    pinned_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    bumped_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    featured_link: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    external_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    slow_mode_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locale: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    featured_user1_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    featured_user2_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    featured_user3_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    featured_user4_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
