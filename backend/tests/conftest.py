"""
Shared pytest fixtures for the discourse-forum backend.

Strategy
--------
* Pure-logic tests (guardian, markdown, schemas, security) need NO database.
* Route tests use a real FastAPI TestClient with an overridden `get_db` dependency
  that injects an AsyncMock session — no live database connection required.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

# ── Make sure we are in DEV mode so dev-tokens are accepted ──────────────────
os.environ.setdefault("DEV_MODE", "true")
os.environ.setdefault("DEV_JWT_SECRET", "test-secret-do-not-use-in-prod")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")
os.environ.setdefault("AZURE_AD_TENANT_ID", "00000000-0000-0000-0000-000000000000")
os.environ.setdefault("AZURE_AD_CLIENT_ID", "test-client-id")
os.environ.setdefault("JWKS_URI", "https://example.com/.well-known/jwks")


# ── Minimal model stubs (avoid importing SQLAlchemy models in pure tests) ────


class _FakeUser:
    def __init__(
        self,
        *,
        id: int = 1,
        username: str = "testuser",
        name: str = "Test User",
        admin: bool = False,
        moderator: bool = False,
        trust_level: int = 1,
        active: bool = True,
        staged: bool = False,
        silenced_till=None,
        suspended_till=None,
        avatar_url: str = "https://example.com/avatar.png",
        uploaded_avatar_id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        last_seen_at: Optional[datetime] = None,
        primary_email: str = "test@example.com",
    ):
        self.id = id
        self.username = username
        self.username_lower = username.lower()
        self.name = name
        self.admin = admin
        self.moderator = moderator
        self.trust_level = trust_level
        self.active = active
        self.staged = staged
        self.silenced_till = silenced_till
        self.suspended_till = suspended_till
        self.avatar_url = avatar_url
        self.uploaded_avatar_id = uploaded_avatar_id
        self.created_at = created_at or datetime(2024, 1, 1)
        self.last_seen_at = last_seen_at or datetime(2024, 6, 1)
        self.primary_email = primary_email
        self.emails = []
        self.associated_accounts = []


class _FakeTopic:
    def __init__(
        self,
        *,
        id: int = 1,
        user_id: int = 1,
        deleted_at=None,
        visible: bool = True,
        closed: bool = False,
        archived: bool = False,
    ):
        self.id = id
        self.user_id = user_id
        self.deleted_at = deleted_at
        self.visible = visible
        self.closed = closed
        self.archived = archived


class _FakePost:
    def __init__(
        self,
        *,
        id: int = 1,
        user_id: int = 1,
        topic_id: int = 1,
        deleted_at=None,
    ):
        self.id = id
        self.user_id = user_id
        self.topic_id = topic_id
        self.deleted_at = deleted_at


class _FakeCategory:
    def __init__(self, *, id: int = 1, read_restricted: bool = False):
        self.id = id
        self.read_restricted = read_restricted


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def anon_user():
    """No authenticated user."""
    return None


@pytest.fixture
def regular_user():
    return _FakeUser()


@pytest.fixture
def admin_user():
    return _FakeUser(id=2, username="admin", admin=True)


@pytest.fixture
def mod_user():
    return _FakeUser(id=3, username="mod", moderator=True)


@pytest.fixture
def other_user():
    return _FakeUser(id=99, username="other")


@pytest.fixture
def open_topic():
    return _FakeTopic()


@pytest.fixture
def deleted_topic():
    return _FakeTopic(deleted_at=datetime(2024, 1, 1))


@pytest.fixture
def closed_topic():
    return _FakeTopic(closed=True)


@pytest.fixture
def open_post():
    return _FakePost()


@pytest.fixture
def deleted_post():
    return _FakePost(deleted_at=datetime(2024, 1, 1))


@pytest.fixture
def open_category():
    return _FakeCategory()


@pytest.fixture
def restricted_category():
    return _FakeCategory(read_restricted=True)


# ── Async DB session mock ─────────────────────────────────────────────────────


@pytest.fixture
def mock_db():
    """Returns an AsyncMock that behaves like an AsyncSession."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    return db


# ── FastAPI TestClient with mocked DB ────────────────────────────────────────


@pytest.fixture
def client(mock_db):
    """
    TestClient with the `get_db` dependency overridden to yield our mock_db.
    Import here to avoid module-level side effects before env vars are set.
    """
    from app.main import app
    from app.core.database import get_db

    async def _override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()
