from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.database import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    name_lower: Mapped[str] = mapped_column(String(50), nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    color: Mapped[str] = mapped_column(String(6), default="0088CC", nullable=False)
    text_color: Mapped[str] = mapped_column(String(6), default="FFFFFF", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    topic_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    topic_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    post_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    topics_year: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    topics_month: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    topics_week: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    topics_day: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    posts_year: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    posts_month: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    posts_week: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    posts_day: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    read_restricted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    parent_category_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latest_post_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latest_topic_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    allow_badges: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    topic_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sort_ascending: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    search_priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    default_view: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    emoji: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    locale: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)


class CategoryGroup(Base):
    __tablename__ = "category_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(Integer, nullable=False)
    group_id: Mapped[int] = mapped_column(Integer, nullable=False)
    permission_type: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
