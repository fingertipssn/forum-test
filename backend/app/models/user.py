from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean, DateTime, Float, Integer, String, Text, BigInteger, Date, ForeignKey
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    username_lower: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    moderator: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trust_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved_by_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_emailed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    first_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    previous_visit_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    suspended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    suspended_till: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    silenced_till: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    staged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    uploaded_avatar_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    primary_group_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    flair_group_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    locale: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    emails: Mapped[list["UserEmail"]] = relationship("UserEmail", back_populates="user", lazy="raise")
    associated_accounts: Mapped[list["UserAssociatedAccount"]] = relationship(
        "UserAssociatedAccount", back_populates="user", lazy="raise"
    )

    @property
    def primary_email(self) -> Optional[str]:
        for e in self.emails:
            if e.primary:
                return e.email
        return None

    @property
    def avatar_url(self) -> str:
        # uploaded_avatar_id is set when the user has a custom avatar;
        # the URL is resolved by the router after fetching the upload record.
        # This fallback is used everywhere the upload URL is not separately fetched.
        return f"/letter_avatar_proxy/v4/letter/{self.username[0].lower()}/6d82ef/48.png"


class UserEmail(Base):
    __tablename__ = "user_emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="emails")


class UserStats(Base):
    __tablename__ = "user_stats"
    # user_stats usa user_id como PK (Discourse no tiene columna 'id' en esta tabla)
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topics_entered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    time_read: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    days_visited: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    posts_read_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    likes_given: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    likes_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_since: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    first_unread_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    first_unread_pm_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    post_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    topic_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bounce_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    flags_agreed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    flags_disagreed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    flags_ignored: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class UserOptions(Base):
    __tablename__ = "user_options"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)


class UserAssociatedAccount(Base):
    __tablename__ = "user_associated_accounts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    provider_name: Mapped[str] = mapped_column(String, nullable=False)
    provider_uid: Mapped[str] = mapped_column(String, nullable=False)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    info: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    credentials: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    extra: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="associated_accounts")
