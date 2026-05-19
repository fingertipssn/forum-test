from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    topic_id: Mapped[int] = mapped_column(Integer, nullable=False)
    post_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw: Mapped[str] = mapped_column(Text, nullable=False)
    cooked: Mapped[str] = mapped_column(Text, nullable=False)

    reply_to_post_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reply_to_user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reply_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quote_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    like_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    incoming_link_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bookmark_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    percent_rank: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    off_topic_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notify_moderators_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    spam_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    illegal_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    inappropriate_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notify_user_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    post_type: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    sort_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cook_method: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    public_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    self_edits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hidden_reason_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    wiki: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reply_quoted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    via_email: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    last_editor_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    locked_by_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    deleted_by_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    edit_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    action_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    outbound_message_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    locale: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    image_upload_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    last_version_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    baked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    hidden_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    baked_version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class PostSearchData(Base):
    __tablename__ = "post_search_data"

    post_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    search_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    locale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class TopicSearchData(Base):
    __tablename__ = "topic_search_data"

    topic_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    search_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    locale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
