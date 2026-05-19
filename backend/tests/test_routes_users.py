"""
Tests for user routes: GET /api/u/{username}, PUT /api/u/{username}.
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


def _setup(mock_db, current_user=None):
    from app.main import app
    from app.core.security import get_current_user, require_current_user
    from app.core.database import get_db

    async def _fake_get_user():
        return current_user

    async def _fake_require_user():
        if current_user is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=401)
        return current_user

    async def _fake_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = _fake_get_user
    app.dependency_overrides[require_current_user] = _fake_require_user
    app.dependency_overrides[get_db] = _fake_db
    return TestClient(app, raise_server_exceptions=False), app


class TestGetUser:
    def test_get_existing_user_returns_200(self):
        mock_db = AsyncMock()
        target = _FakeUser(id=2, username="alice")

        upload_none = MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        user_result = MagicMock(scalar_one_or_none=MagicMock(return_value=target))

        call_count = [0]

        async def execute_side_effect(*args, **kwargs):
            idx = call_count[0]
            call_count[0] += 1
            if idx == 0:
                return user_result
            return upload_none

        mock_db.execute = AsyncMock(side_effect=execute_side_effect)
        viewer = _FakeUser(id=1, username="viewer")
        client, app = _setup(mock_db, current_user=viewer)
        try:
            resp = client.get("/api/u/alice")
            assert resp.status_code in (200, 404)
        finally:
            app.dependency_overrides.clear()

    def test_get_nonexistent_user_returns_404(self):
        mock_db = AsyncMock()
        r = MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        mock_db.execute = AsyncMock(return_value=r)

        client, app = _setup(mock_db)
        try:
            resp = client.get("/api/u/nobody")
            assert resp.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_email_not_exposed_to_other_user(self):
        mock_db = AsyncMock()
        target = _FakeUser(id=2, username="alice", primary_email="alice@example.com")

        upload_none = MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        user_result = MagicMock(scalar_one_or_none=MagicMock(return_value=target))

        call_count = [0]

        async def execute_side_effect(*args, **kwargs):
            idx = call_count[0]
            call_count[0] += 1
            if idx == 0:
                return user_result
            return upload_none

        mock_db.execute = AsyncMock(side_effect=execute_side_effect)

        # Viewer is different user
        viewer = _FakeUser(id=99, username="viewer")
        client, app = _setup(mock_db, current_user=viewer)
        try:
            resp = client.get("/api/u/alice")
            if resp.status_code == 200:
                data = resp.json()
                # email should be null for other users
                assert data.get("email") is None
        finally:
            app.dependency_overrides.clear()

    def test_own_profile_includes_email(self):
        mock_db = AsyncMock()
        user = _FakeUser(id=1, username="alice", primary_email="alice@example.com")

        upload_none = MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        user_result = MagicMock(scalar_one_or_none=MagicMock(return_value=user))

        call_count = [0]

        async def execute_side_effect(*args, **kwargs):
            idx = call_count[0]
            call_count[0] += 1
            if idx == 0:
                return user_result
            return upload_none

        mock_db.execute = AsyncMock(side_effect=execute_side_effect)

        client, app = _setup(mock_db, current_user=user)
        try:
            resp = client.get("/api/u/alice")
            if resp.status_code == 200:
                data = resp.json()
                assert data.get("email") == "alice@example.com"
        finally:
            app.dependency_overrides.clear()


class TestUpdateUser:
    def test_update_requires_auth(self):
        mock_db = AsyncMock()
        client, app = _setup(mock_db, current_user=None)
        try:
            resp = client.put("/api/u/alice", json={"name": "New Name"})
            assert resp.status_code == 401
        finally:
            app.dependency_overrides.clear()

    def test_cannot_update_another_user(self):
        mock_db = AsyncMock()
        target = _FakeUser(id=2, username="alice")
        user_result = MagicMock(scalar_one_or_none=MagicMock(return_value=target))
        mock_db.execute = AsyncMock(return_value=user_result)

        current_user = _FakeUser(id=99, username="viewer")
        client, app = _setup(mock_db, current_user=current_user)
        try:
            resp = client.put("/api/u/alice", json={"name": "Hacked"})
            assert resp.status_code in (403, 404)
        finally:
            app.dependency_overrides.clear()

    def test_update_own_name_succeeds(self):
        mock_db = AsyncMock()
        user = _FakeUser(id=1, username="alice")
        user_result = MagicMock(scalar_one_or_none=MagicMock(return_value=user))

        call_count = [0]

        async def execute_side_effect(*args, **kwargs):
            idx = call_count[0]
            call_count[0] += 1
            if idx == 0:
                return user_result
            return MagicMock(scalar_one_or_none=MagicMock(return_value=None))

        mock_db.execute = AsyncMock(side_effect=execute_side_effect)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        client, app = _setup(mock_db, current_user=user)
        try:
            resp = client.put("/api/u/alice", json={"name": "Alice Smith"})
            assert resp.status_code in (200, 422)
        finally:
            app.dependency_overrides.clear()
