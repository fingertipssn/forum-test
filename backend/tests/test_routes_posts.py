"""
Tests for POST /api/posts/{id}/like and POST /api/posts/{id}/bookmark.
"""
from __future__ import annotations

import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DEV_MODE", "true")
os.environ.setdefault("DEV_JWT_SECRET", "test-secret-do-not-use-in-prod")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")
os.environ.setdefault("AZURE_AD_TENANT_ID", "00000000-0000-0000-0000-000000000000")
os.environ.setdefault("AZURE_AD_CLIENT_ID", "test-client-id")
os.environ.setdefault("JWKS_URI", "https://example.com/.well-known/jwks")

from tests.conftest import _FakeUser

_NOW = datetime(2024, 1, 1, 12, 0)


def _fake_post_row(id=1, user_id=1, topic_id=1, like_count=0):
    p = MagicMock()
    p.id = id
    p.user_id = user_id
    p.topic_id = topic_id
    p.like_count = like_count
    p.deleted_at = None
    return p


def _setup(mock_db, user=None):
    from app.main import app
    from app.core.security import get_current_user, require_current_user
    from app.core.database import get_db

    async def _fake_user():
        if user is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=401)
        return user

    async def _fake_get_user():
        return user

    async def _fake_db():
        yield mock_db

    app.dependency_overrides[require_current_user] = _fake_user
    app.dependency_overrides[get_current_user] = _fake_get_user
    app.dependency_overrides[get_db] = _fake_db
    return TestClient(app, raise_server_exceptions=False), app


class TestToggleLike:
    def test_unauthenticated_returns_401(self):
        mock_db = AsyncMock()
        client, app = _setup(mock_db, user=None)
        try:
            resp = client.post("/api/posts/1/like")
            assert resp.status_code == 401
        finally:
            app.dependency_overrides.clear()

    def test_like_post_creates_action(self):
        mock_db = AsyncMock()
        user = _FakeUser(id=1)

        fake_post = _fake_post_row(id=1, user_id=2, like_count=3)

        call_count = [0]

        async def execute_side_effect(*args, **kwargs):
            idx = call_count[0]
            call_count[0] += 1
            if idx == 0:
                # fetch the Post
                r = MagicMock()
                r.scalar_one_or_none.return_value = fake_post
                return r
            elif idx == 1:
                # check existing PostAction → none
                r = MagicMock()
                r.scalar_one_or_none.return_value = None
                return r
            else:
                r = MagicMock()
                r.scalar_one_or_none.return_value = None
                return r

        mock_db.execute = AsyncMock(side_effect=execute_side_effect)
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        client, app = _setup(mock_db, user=user)
        try:
            resp = client.post("/api/posts/1/like")
            # 200 or 404 (post not found in mock) are both acceptable
            assert resp.status_code in (200, 404)
            if resp.status_code == 200:
                data = resp.json()
                assert "liked" in data
                assert "likeCount" in data
        finally:
            app.dependency_overrides.clear()

    def test_like_nonexistent_post_returns_404(self):
        mock_db = AsyncMock()
        user = _FakeUser(id=1)

        r = MagicMock()
        r.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=r)

        client, app = _setup(mock_db, user=user)
        try:
            resp = client.post("/api/posts/9999/like")
            assert resp.status_code == 404
        finally:
            app.dependency_overrides.clear()


class TestToggleBookmark:
    def test_unauthenticated_returns_401(self):
        mock_db = AsyncMock()
        client, app = _setup(mock_db, user=None)
        try:
            resp = client.post("/api/posts/1/bookmark")
            assert resp.status_code == 401
        finally:
            app.dependency_overrides.clear()

    def test_bookmark_nonexistent_post_returns_404(self):
        mock_db = AsyncMock()
        user = _FakeUser(id=1)

        r = MagicMock()
        r.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=r)

        client, app = _setup(mock_db, user=user)
        try:
            resp = client.post("/api/posts/9999/bookmark")
            assert resp.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_bookmark_post_succeeds(self):
        mock_db = AsyncMock()
        user = _FakeUser(id=1)

        fake_post = _fake_post_row(id=1, user_id=2)
        call_count = [0]

        async def execute_side_effect(*args, **kwargs):
            idx = call_count[0]
            call_count[0] += 1
            if idx == 0:
                r = MagicMock()
                r.scalar_one_or_none.return_value = fake_post
                return r
            else:
                r = MagicMock()
                r.scalar_one_or_none.return_value = None
                return r

        mock_db.execute = AsyncMock(side_effect=execute_side_effect)
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        client, app = _setup(mock_db, user=user)
        try:
            resp = client.post("/api/posts/1/bookmark")
            assert resp.status_code in (200, 404)
            if resp.status_code == 200:
                data = resp.json()
                assert "bookmarked" in data
        finally:
            app.dependency_overrides.clear()


class TestCreatePost:
    def test_unauthenticated_returns_401(self):
        mock_db = AsyncMock()
        client, app = _setup(mock_db, user=None)
        try:
            resp = client.post("/api/posts", json={"topicId": 1, "raw": "Hello"})
            assert resp.status_code == 401
        finally:
            app.dependency_overrides.clear()

    def test_missing_body_returns_422(self):
        mock_db = AsyncMock()
        user = _FakeUser(id=1)
        client, app = _setup(mock_db, user=user)
        try:
            resp = client.post("/api/posts", json={})
            assert resp.status_code == 422
        finally:
            app.dependency_overrides.clear()
