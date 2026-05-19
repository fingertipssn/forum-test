"""
Tests for Pydantic schemas — validation, alias generation, and factory methods.
No database required.
"""
from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.category import CategoryOut, CategoryCreate, CategoryRecentTopic
from app.schemas.topic import TopicCreate, TopicOut, TopicListResponse
from app.schemas.post import PostCreate, PostUpdate, PostOut
from app.schemas.user import UserOut
from tests.conftest import _FakeUser


_NOW = datetime(2024, 1, 1, 12, 0, 0)


# ── CategoryCreate validation ────────────────────────────────────────────────


class TestCategoryCreate:
    def test_valid_minimal(self):
        c = CategoryCreate(name="Tech")
        assert c.name == "Tech"
        assert c.color == "0088CC"

    def test_name_stripped(self):
        c = CategoryCreate(name="  Python  ")
        assert c.name == "Python"

    def test_name_empty_raises(self):
        with pytest.raises(ValidationError):
            CategoryCreate(name="   ")

    def test_name_too_long_raises(self):
        with pytest.raises(ValidationError):
            CategoryCreate(name="x" * 51)

    def test_name_exactly_50_ok(self):
        c = CategoryCreate(name="x" * 50)
        assert len(c.name) == 50

    def test_color_normalised_uppercase(self):
        c = CategoryCreate(name="Test", color="abc123")
        assert c.color == "ABC123"

    def test_color_hash_stripped(self):
        c = CategoryCreate(name="Test", color="#FF0000")
        assert c.color == "FF0000"

    def test_color_3char_padded(self):
        c = CategoryCreate(name="Test", color="f00")
        # Pads to 6 with zfill → "000f00"
        assert len(c.color) == 6

    def test_invalid_color_raises(self):
        with pytest.raises(ValidationError):
            CategoryCreate(name="Test", color="ZZZZZZ")

    def test_invalid_color_length_raises(self):
        with pytest.raises(ValidationError):
            CategoryCreate(name="Test", color="FF00")


# ── CategoryOut alias generation ─────────────────────────────────────────────


class TestCategoryOut:
    def _make(self, **kw):
        defaults = dict(
            id=1, name="Python", slug="python", color="0088CC",
            text_color="FFFFFF", description=None,
            topic_count=5, post_count=10,
            parent_category_id=None, read_restricted=False,
            position=1, topic_template=None, emoji=None, icon=None,
            created_at=_NOW, latest_topics=[],
        )
        defaults.update(kw)
        return CategoryOut(**defaults)

    def test_creates_ok(self):
        c = self._make()
        assert c.id == 1
        assert c.name == "Python"

    def test_camel_alias_in_json(self):
        c = self._make()
        data = c.model_dump(by_alias=True)
        assert "topicCount" in data
        assert "postCount" in data

    def test_latest_topics_default_empty(self):
        c = self._make()
        assert c.latest_topics == []


# ── TopicCreate ───────────────────────────────────────────────────────────────


class TestTopicCreate:
    def test_minimal(self):
        t = TopicCreate(title="Hello", raw="Some content")
        assert t.title == "Hello"
        assert t.category_id is None

    def test_with_category(self):
        t = TopicCreate(title="Hello", raw="Content", category_id=5)
        assert t.category_id == 5

    def test_tags_default_empty(self):
        t = TopicCreate(title="Hello", raw="Content")
        assert t.tags == []

    def test_missing_title_raises(self):
        with pytest.raises(ValidationError):
            TopicCreate(raw="Content")


# ── TopicOut ──────────────────────────────────────────────────────────────────


class TestTopicOut:
    def _make(self, **kw):
        defaults = dict(
            id=1, title="Test Topic", fancy_title=None, slug="test-topic",
            excerpt=None, posts_count=3, reply_count=2, views=100,
            like_count=5, category_id=1, user_id=1,
            visible=True, closed=False, archived=False,
            pinned_globally=False, pinned_at=None,
            archetype="regular", created_at=_NOW, updated_at=_NOW,
            bumped_at=_NOW, last_posted_at=None,
            author_username="user1", author_name=None, author_avatar_url=None,
        )
        defaults.update(kw)
        return TopicOut(**defaults)

    def test_creates_ok(self):
        t = self._make()
        assert t.id == 1

    def test_author_name_optional(self):
        t = self._make(author_name="Display Name")
        assert t.author_name == "Display Name"

    def test_camel_alias(self):
        t = self._make()
        data = t.model_dump(by_alias=True)
        assert "postsCount" in data
        assert "authorUsername" in data


# ── PostCreate / PostUpdate ───────────────────────────────────────────────────


class TestPostCreate:
    def test_minimal(self):
        p = PostCreate(topic_id=1, raw="Hello!")
        assert p.topic_id == 1

    def test_reply_to_optional(self):
        p = PostCreate(topic_id=1, raw="Reply", reply_to_post_number=3)
        assert p.reply_to_post_number == 3

    def test_missing_raw_raises(self):
        with pytest.raises(ValidationError):
            PostCreate(topic_id=1)


class TestPostUpdate:
    def test_minimal(self):
        u = PostUpdate(raw="Updated content")
        assert u.raw == "Updated content"

    def test_edit_reason_optional(self):
        u = PostUpdate(raw="Content", edit_reason="typo")
        assert u.edit_reason == "typo"


# ── PostOut ───────────────────────────────────────────────────────────────────


class TestPostOut:
    def _make(self, **kw):
        defaults = dict(
            id=1, user_id=1, topic_id=1, post_number=1,
            raw="Hello", cooked="<p>Hello</p>",
            reply_to_post_number=None, reply_count=0,
            like_count=0, reads=10, post_type=1,
            version=1, wiki=False, hidden=False, user_deleted=False,
            created_at=_NOW, updated_at=_NOW,
            deleted_at=None, edit_reason=None,
            author_username="user1", author_name=None,
            author_avatar_url=None,
            can_edit=False, can_delete=False,
            liked_by_me=False, bookmarked_by_me=False,
        )
        defaults.update(kw)
        return PostOut(**defaults)

    def test_creates_ok(self):
        p = self._make()
        assert p.id == 1

    def test_liked_by_me_default_false(self):
        p = self._make()
        assert p.liked_by_me is False

    def test_bookmarked_by_me_default_false(self):
        p = self._make()
        assert p.bookmarked_by_me is False

    def test_camel_alias(self):
        p = self._make()
        data = p.model_dump(by_alias=True)
        assert "likedByMe" in data
        assert "bookmarkedByMe" in data


# ── UserOut ───────────────────────────────────────────────────────────────────


class TestUserOut:
    def test_from_orm(self):
        user = _FakeUser()
        out = UserOut.from_orm(user)
        assert out.id == user.id
        assert out.username == user.username
        assert out.email is None  # not passed → None

    def test_from_orm_with_email(self):
        user = _FakeUser()
        out = UserOut.from_orm(user, email="me@example.com")
        assert out.email == "me@example.com"

    def test_from_orm_with_avatar_url(self):
        user = _FakeUser()
        out = UserOut.from_orm(user, avatar_url="https://cdn.example.com/photo.jpg")
        assert out.avatar_url == "https://cdn.example.com/photo.jpg"

    def test_from_orm_fallback_avatar(self):
        user = _FakeUser(avatar_url="https://fallback.example.com/x.png")
        out = UserOut.from_orm(user)
        assert out.avatar_url == "https://fallback.example.com/x.png"

    def test_camel_alias(self):
        user = _FakeUser()
        out = UserOut.from_orm(user)
        data = out.model_dump(by_alias=True)
        assert "trustLevel" in data
        assert "avatarUrl" in data
