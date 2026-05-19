from datetime import datetime, timezone
import logging
import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text

from ..core.database import get_db
from ..core.security import get_current_user, require_current_user, create_dev_jwt
from ..core.config import settings
from ..schemas.user import UserOut

logger = logging.getLogger(__name__)
router = APIRouter()


async def _create_user_support_rows(db: AsyncSession, user_id: int, now: datetime):
    """Crea user_stats y user_options usando savepoints para no revertir el usuario."""
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
            {"uid": user_id, "now": now},
            "user_stats",
        ),
        (
            text("INSERT INTO user_options (user_id) VALUES (:uid) ON CONFLICT (user_id) DO NOTHING"),
            {"uid": user_id},
            "user_options",
        ),
    ]:
        try:
            await db.execute(text("SAVEPOINT sp_support"))
            await db.execute(stmt, params)
            await db.execute(text("RELEASE SAVEPOINT sp_support"))
        except Exception as e:
            await db.execute(text("ROLLBACK TO SAVEPOINT sp_support"))
            logger.warning("No se pudo crear %s para user_id=%d: %s", label, user_id, e)


@router.get("/me", response_model=UserOut)
async def get_me(
    user=Depends(require_current_user),
    db: AsyncSession = Depends(get_db),
):
    from ..models.upload import Upload

    # Resolve avatar URL
    avatar_url = user.avatar_url
    if user.uploaded_avatar_id:
        upload_result = await db.execute(
            select(Upload).where(Upload.id == user.uploaded_avatar_id)
        )
        upload = upload_result.scalar_one_or_none()
        if upload:
            avatar_url = upload.url

    return UserOut.from_orm(user, email=user.primary_email, avatar_url=avatar_url)


@router.post("/sync")
async def sync_user(
    user=Depends(require_current_user),
    db: AsyncSession = Depends(get_db),
):
    from ..models.user import User

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.execute(
        update(User).where(User.id == user.id).values(last_seen_at=now)
    )
    return {"status": "ok"}


class DevLoginBody(BaseModel):
    username: str
    email: str = ""
    name: str = ""


@router.post("/dev-login")
async def dev_login(
    body: DevLoginBody,
    db: AsyncSession = Depends(get_db),
):
    if not settings.DEV_MODE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    from ..models.user import User, UserEmail

    username_clean = re.sub(r"[^a-zA-Z0-9_]", "_", body.username.strip())[:50] or "user"
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    result = await db.execute(
        select(User).where(User.username_lower == username_clean.lower())
    )
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            username=username_clean,
            username_lower=username_clean.lower(),
            name=body.name or username_clean,
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

        if body.email:
            try:
                await db.execute(text("SAVEPOINT sp_email"))
                db.add(UserEmail(
                    user_id=user.id,
                    email=body.email.lower(),
                    primary=True,
                    created_at=now,
                    updated_at=now,
                ))
                await db.flush()
                await db.execute(text("RELEASE SAVEPOINT sp_email"))
            except Exception as e:
                await db.execute(text("ROLLBACK TO SAVEPOINT sp_email"))
                logger.warning("No se pudo crear user_email para user_id=%d: %s", user.id, e)

        await _create_user_support_rows(db, user.id, now)

    token = create_dev_jwt(user.id, user.username)

    # Reload with emails for response
    from sqlalchemy.orm import selectinload
    result2 = await db.execute(
        select(User).options(selectinload(User.emails)).where(User.id == user.id)
    )
    user_full = result2.scalar_one()
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserOut.from_orm(user_full, email=user_full.primary_email),
    }
