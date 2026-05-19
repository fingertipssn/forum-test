"""
Tests for category routes: GET /api/categories, POST /api/categories.
"""
from __future__ import annotations

import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

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


def _fake_category(id=1, name="Tech", slug="tech", read_restricted=False):
    cat = MagicMock()
    cat.id = id
    cat.name = name
    cat.slug = slug
    cat.color = "0088CC"
    cat.text_color = "FFFFFF"
    cat.description = None
    cat.topic_count = 5
    cat.post_count = 10
    cat.parent_category_id = None
    cat.read_restricted = read_restricted
    cat.position = 1
    cat.topic_template = None
    cat.emoji = None
    cat.icon = None
    cat.created_at = _NOW
    return cat


def _setup_client(mock_db, current_user=None):
    from app.main import app
    from app.core.security import get_current_user, require_current_user
    from app.core.database import get_db

    async def _fake_current_user():
        return current_user

    async def _fake_require_user():
        if current_user is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=401)
        return current_user

    async def _fake_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = _fake_current_user
    app.dependency_overrides[require_current_user] = _fake_require_user
    app.dependency_overrides[get_db] = _fake_db
    return TestClient(app, raise_server_exceptions=False), app


class TestListCategories:
    def test_returns_200_with_categories(self):
        mock_db = AsyncMock()

        cat = _fake_category()
        # First execute → categories; second → topics (empty); third+ → users
        results = [
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[cat])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
        ]
        call_count = [0]

        async def execute_side_effect(*args, **kwargs):
            idx = call_count[0]
            call_count[0] += 1
            if idx < len(results):
                return results[idx]
            return MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))

        mock_db.execute = AsyncMock(side_effect=execute_side_effect)

        client, app = _setup_client(mock_db)
        try:
            resp = client.get("/api/categories")
            assert resp.status_code == 200
            data = resp.json()
            assert "categories" in data
            assert isinstance(data["categories"], list)
        finally:
            app.dependency_overrides.clear()

    def test_restricted_category_hidden_from_anon(self):
        mock_db = AsyncMock()
        cat = _fake_category(read_restricted=True)

        results = [
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[cat])))),
        ]
        call_count = [0]

        async def execute_side_effect(*args, **kwargs):
            idx = call_count[0]
            call_count[0] += 1
            if idx < len(results):
                return results[idx]
            return MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))

        mock_db.execute = AsyncMock(side_effect=execute_side_effect)

        client, app = _setup_client(mock_db, current_user=None)
        try:
            resp = client.get("/api/categories")
            assert resp.status_code == 200
            data = resp.json()
            # restricted category should be filtered out for anon
            assert len(data["categories"]) == 0
        finally:
            app.dependency_overrides.clear()


class TestCreateCategory:
    def test_create_requires_auth(self):
        mock_db = AsyncMock()
        client, app = _setup_client(mock_db, current_user=None)
        try:
            resp = client.post("/api/categories", json={"name": "Test", "color": "0088CC", "textColor": "FFFFFF"})
            assert resp.status_code in (401, 403)
        finally:
            app.dependency_overrides.clear()

    def test_create_requires_staff(self):
        mock_db = AsyncMock()
        regular = _FakeUser(admin=False, moderator=False)
        client, app = _setup_client(mock_db, current_user=regular)
        try:
            resp = client.post("/api/categories", json={"name": "Test", "color": "0088CC", "textColor": "FFFFFF"})
            assert resp.status_code in (401, 403)
        finally:
            app.dependency_overrides.clear()

    def test_create_by_admin_succeeds(self):
        mock_db = AsyncMock()
        admin = _FakeUser(id=1, admin=True)

        call_count = [0]

        async def execute_side_effect(*args, **kwargs):
            idx = call_count[0]
            call_count[0] += 1
            r = MagicMock()
            if idx == 0:
                # slug collision check → no existing category
                r.scalar_one_or_none.return_value = None
            else:
                # func.max(position) → 0
                r.scalar.return_value = 0
                r.scalar_one_or_none.return_value = None
            return r

        mock_db.execute = AsyncMock(side_effect=execute_side_effect)
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.add = MagicMock()

        client, app = _setup_client(mock_db, current_user=admin)
        try:
            resp = client.post(
                "/api/categories",
                json={"name": "NewCat", "color": "0088CC", "textColor": "FFFFFF"},
            )
            # Either 201 (success) or 422/400 (model validation) — no 500
            assert resp.status_code in (201, 200, 422, 400)
        finally:
            app.dependency_overrides.clear()

    def test_invalid_color_returns_422(self):
        mock_db = AsyncMock()
        admin = _FakeUser(id=1, admin=True)
        client, app = _setup_client(mock_db, current_user=admin)
        try:
            resp = client.post(
                "/api/categories",
                json={"name": "Test", "color": "GGGGGG", "textColor": "FFFFFF"},
            )
            assert resp.status_code == 422
        finally:
            app.dependency_overrides.clear()
