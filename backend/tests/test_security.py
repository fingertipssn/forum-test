"""
Tests for app.core.security — JWT creation and validation helpers.
No real network calls or database.
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException

# Env vars must be set before importing the security module
os.environ.setdefault("DEV_MODE", "true")
os.environ.setdefault("DEV_JWT_SECRET", "test-secret-do-not-use-in-prod")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")
os.environ.setdefault("AZURE_AD_TENANT_ID", "00000000-0000-0000-0000-000000000000")
os.environ.setdefault("AZURE_AD_CLIENT_ID", "test-client-id")
os.environ.setdefault("JWKS_URI", "https://example.com/.well-known/jwks")

from app.core.security import (
    create_dev_jwt,
    validate_dev_token,
    _is_dev_token,
    DEV_ISSUER,
)

SECRET = os.environ["DEV_JWT_SECRET"]


# ── create_dev_jwt ────────────────────────────────────────────────────────────


class TestCreateDevJwt:
    def test_returns_string(self):
        token = create_dev_jwt(1, "alice")
        assert isinstance(token, str)

    def test_has_three_parts(self):
        token = create_dev_jwt(1, "alice")
        assert token.count(".") == 2

    def test_payload_contains_sub(self):
        token = create_dev_jwt(42, "bob")
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        assert payload["sub"] == "42"

    def test_payload_contains_username(self):
        token = create_dev_jwt(1, "charlie")
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        assert payload["username"] == "charlie"

    def test_payload_issuer(self):
        token = create_dev_jwt(1, "alice")
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        assert payload["iss"] == DEV_ISSUER

    def test_token_not_expired(self):
        token = create_dev_jwt(1, "alice")
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        assert payload["exp"] > time.time()

    def test_expiry_30_days(self):
        token = create_dev_jwt(1, "alice")
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        diff = payload["exp"] - payload["iat"]
        # 30 days = 2592000 seconds (allow ±5 s tolerance)
        assert abs(diff - 30 * 24 * 3600) < 5


# ── _is_dev_token ─────────────────────────────────────────────────────────────


class TestIsDevToken:
    def test_valid_dev_token(self):
        token = create_dev_jwt(1, "alice")
        assert _is_dev_token(token) is True

    def test_random_string_not_dev_token(self):
        assert _is_dev_token("not.a.token") is False

    def test_azure_rs256_token_not_dev(self):
        # Build a minimal HS256 token with wrong issuer
        payload = {"iss": "https://sts.windows.net/x/", "sub": "1"}
        token = jwt.encode(payload, SECRET, algorithm="HS256")
        # iss is wrong → _is_dev_token returns False
        assert _is_dev_token(token) is False

    def test_empty_string_not_dev_token(self):
        assert _is_dev_token("") is False


# ── validate_dev_token ────────────────────────────────────────────────────────


class TestValidateDevToken:
    def test_valid_token_returns_payload(self):
        token = create_dev_jwt(7, "tester")
        payload = validate_dev_token(token)
        assert payload["sub"] == "7"

    def test_expired_token_raises_401(self):
        now = datetime.now(timezone.utc)
        expired_payload = {
            "iss": DEV_ISSUER,
            "sub": "1",
            "iat": now - timedelta(days=31),
            "exp": now - timedelta(days=1),
        }
        token = jwt.encode(expired_payload, SECRET, algorithm="HS256")
        with pytest.raises(HTTPException) as exc:
            validate_dev_token(token)
        assert exc.value.status_code == 401
        assert "expired" in exc.value.detail.lower()

    def test_wrong_secret_raises_401(self):
        token = jwt.encode(
            {"iss": DEV_ISSUER, "sub": "1", "exp": time.time() + 9999},
            "WRONG_SECRET",
            algorithm="HS256",
        )
        with pytest.raises(HTTPException) as exc:
            validate_dev_token(token)
        assert exc.value.status_code == 401

    def test_wrong_issuer_raises_401(self):
        token = jwt.encode(
            {"iss": "hacker", "sub": "1", "exp": time.time() + 9999},
            SECRET,
            algorithm="HS256",
        )
        with pytest.raises(HTTPException) as exc:
            validate_dev_token(token)
        assert exc.value.status_code == 401
        assert "issuer" in exc.value.detail.lower()
