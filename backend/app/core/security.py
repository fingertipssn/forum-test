from datetime import datetime, timedelta, timezone
from typing import Optional
import json
import logging

import httpx
import jwt
from jwt.algorithms import RSAAlgorithm
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import get_db

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)

_jwks_cache: dict | None = None
_jwks_cache_expiry: datetime | None = None

DEV_ISSUER = "discourse-dev"


async def _get_jwks() -> dict:
    global _jwks_cache, _jwks_cache_expiry
    now = datetime.now(timezone.utc)
    if _jwks_cache is None or (_jwks_cache_expiry and now > _jwks_cache_expiry):
        async with httpx.AsyncClient() as client:
            resp = await client.get(settings.jwks_uri, timeout=10.0)
            resp.raise_for_status()
            _jwks_cache = resp.json()
            _jwks_cache_expiry = now + timedelta(hours=24)
    return _jwks_cache


def _is_dev_token(token: str) -> bool:
    try:
        header = jwt.get_unverified_header(token)
        unverified = jwt.decode(token, options={"verify_signature": False})
        return header.get("alg") == "HS256" and unverified.get("iss") == DEV_ISSUER
    except Exception:
        return False


def validate_dev_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.DEV_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": True},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {exc}")

    if payload.get("iss") != DEV_ISSUER:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token issuer")

    return payload


async def validate_azure_token(token: str) -> dict:
    try:
        header = jwt.get_unverified_header(token)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token header") from exc

    jwks = await _get_jwks()
    public_key = None
    for key in jwks.get("keys", []):
        if key.get("kid") == header.get("kid"):
            public_key = RSAAlgorithm.from_jwk(json.dumps(key))
            break

    if public_key is None:
        # Limpiar cache y reintentar una vez (las claves rotan)
        global _jwks_cache
        _jwks_cache = None
        jwks = await _get_jwks()
        for key in jwks.get("keys", []):
            if key.get("kid") == header.get("kid"):
                public_key = RSAAlgorithm.from_jwk(json.dumps(key))
                break
        if public_key is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token signing key not found")

    audience = settings.AZURE_AD_AUDIENCE or settings.AZURE_AD_CLIENT_ID

    # Azure AD emite tokens con dos posibles issuers según la versión del endpoint:
    # v1 → https://sts.windows.net/{tenant}/
    # v2 → https://login.microsoftonline.com/{tenant}/v2.0
    valid_issuers = [
        f"https://sts.windows.net/{settings.AZURE_AD_TENANT_ID}/",
        f"https://login.microsoftonline.com/{settings.AZURE_AD_TENANT_ID}/v2.0",
    ]

    try:
        # Desactivamos verify_iss de PyJWT para validarlo manualmente (acepta ambos)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=audience,
            options={"verify_exp": True, "verify_iss": False},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token inválido: {exc}")

    # Validar issuer manualmente
    token_iss = payload.get("iss", "")
    if token_iss not in valid_issuers:
        logger.warning("Token issuer inesperado: %s", token_iss)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token issuer no reconocido")

    # Validar que el token es del tenant correcto
    token_tid = payload.get("tid", "")
    if token_tid and token_tid != settings.AZURE_AD_TENANT_ID:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de tenant incorrecto")

    return payload


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    if credentials is None:
        return None

    token = credentials.credentials

    if _is_dev_token(token):
        if not settings.DEV_MODE:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Dev tokens not accepted in production")
        return await _get_user_from_dev_token(db, token)

    payload = await validate_azure_token(token)
    return await _get_or_create_user_from_azure(db, payload)


async def require_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(credentials, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user


async def _get_user_from_dev_token(db: AsyncSession, token: str):
    from ..models.user import User
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    payload = validate_dev_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing user identifier")

    result = await db.execute(
        select(User)
        .options(selectinload(User.emails), selectinload(User.associated_accounts))
        .where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def _get_or_create_user_from_azure(db: AsyncSession, payload: dict):
    from ..models.user import User, UserAssociatedAccount
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    oid = payload.get("oid") or payload.get("sub")
    if not oid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing user identifier")

    stmt = (
        select(User)
        .options(selectinload(User.emails), selectinload(User.associated_accounts))
        .join(UserAssociatedAccount, UserAssociatedAccount.user_id == User.id)
        .where(
            UserAssociatedAccount.provider_name == "entra_id",
            UserAssociatedAccount.provider_uid == oid,
        )
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        user = await _create_user_from_token(db, payload, oid)

    return user


def create_dev_jwt(user_id: int, username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "iss": DEV_ISSUER,
        "sub": str(user_id),
        "username": username,
        "iat": now,
        "exp": now + timedelta(days=30),
    }
    return jwt.encode(payload, settings.DEV_JWT_SECRET, algorithm="HS256")


async def _create_user_from_token(db: AsyncSession, payload: dict, oid: str):
    from ..models.user import User, UserEmail, UserAssociatedAccount
    from sqlalchemy import select, text
    import re

    name = payload.get("name", "")
    email = payload.get("preferred_username") or payload.get("upn") or payload.get("email") or ""
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    raw_username = re.sub(r"[^a-zA-Z0-9_]", "_", (email.split("@")[0] if email else name or oid[:20]))
    base_username = raw_username[:50] or "user"

    username = base_username
    suffix = 1
    while True:
        exists = await db.execute(select(User).where(User.username_lower == username.lower()))
        if exists.scalar_one_or_none() is None:
            break
        username = f"{base_username}{suffix}"
        suffix += 1

    # 1. Crear usuario principal
    user = User(
        username=username,
        username_lower=username.lower(),
        name=name,
        active=True,
        trust_level=1,
        admin=False,
        moderator=False,
        approved=True,
        approved_at=now,
        staged=False,
        created_at=now,
        updated_at=now,
        first_seen_at=now,
        last_seen_at=now,
    )
    db.add(user)
    await db.flush()

    # 2. Email
    if email:
        db.add(UserEmail(
            user_id=user.id,
            email=email.lower(),
            primary=True,
            created_at=now,
            updated_at=now,
        ))

    # 3. Cuenta asociada Entra ID
    db.add(UserAssociatedAccount(
        provider_name="entra_id",
        provider_uid=oid,
        user_id=user.id,
        last_used=now,
        info={"name": name, "email": email},  # columna jsonb
        created_at=now,
        updated_at=now,
    ))

    await db.flush()

    # 4. user_stats y user_options: SQL raw con savepoints para tolerar diferencias
    #    de schema entre versiones de Discourse (no usamos ORM para evitar columnas inexistentes)
    for stmt, params, label in [
        (
            text("""
                INSERT INTO user_stats (
                    user_id, topics_entered, time_read, days_visited,
                    posts_read_count, likes_given, likes_received,
                    new_since, first_unread_at, first_unread_pm_at,
                    post_count, topic_count, bounce_score,
                    flags_agreed, flags_disagreed, flags_ignored
                ) VALUES (
                    :uid, 0, 0, 0, 0, 0, 0,
                    :now, :now, :now,
                    0, 0, 0.0, 0, 0, 0
                ) ON CONFLICT (user_id) DO NOTHING
            """),
            {"uid": user.id, "now": now},
            "user_stats",
        ),
        (
            text("INSERT INTO user_options (user_id) VALUES (:uid) ON CONFLICT (user_id) DO NOTHING"),
            {"uid": user.id},
            "user_options",
        ),
    ]:
        try:
            await db.execute(text("SAVEPOINT sp_support"))
            await db.execute(stmt, params)
            await db.execute(text("RELEASE SAVEPOINT sp_support"))
        except Exception as e:
            await db.execute(text("ROLLBACK TO SAVEPOINT sp_support"))
            logger.warning("No se pudo crear %s para user_id=%d: %s", label, user.id, e)

    logger.info("Created new user %s from EntraID oid=%s", username, oid)
    return user
