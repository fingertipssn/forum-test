import hashlib
import io
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update
from sqlalchemy.orm import selectinload

from ..core.database import get_db
from ..core.security import get_current_user, require_current_user
from ..core.config import settings
from ..models.user import User
from ..models.topic import Topic
from ..models.post import Post
from ..models.upload import Upload
from ..schemas.user import UserOut
from ..schemas.topic import TopicOut
from ..schemas.post import PostOut

router = APIRouter()

ALLOWED_AVATAR_MIME = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5 MB


async def _get_avatar_url(db: AsyncSession, user: User) -> str:
    """Resolve the avatar URL: uploaded custom avatar or fallback letter avatar."""
    if user.uploaded_avatar_id:
        result = await db.execute(select(Upload).where(Upload.id == user.uploaded_avatar_id))
        upload = result.scalar_one_or_none()
        if upload:
            return upload.url
    return user.avatar_url


@router.get("/u/{username}", response_model=UserOut)
async def get_user(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(User)
        .options(selectinload(User.emails))
        .where(User.username_lower == username.lower())
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Only expose email to the user themselves
    email = None
    if current_user and current_user.id == user.id:
        email = user.primary_email

    avatar_url = await _get_avatar_url(db, user)
    return UserOut.from_orm(user, email=email, avatar_url=avatar_url)


class UpdateProfileBody(BaseModel):
    name: Optional[str] = None


@router.put("/u/{username}", response_model=UserOut)
async def update_profile(
    username: str,
    body: UpdateProfileBody,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    result = await db.execute(
        select(User)
        .options(selectinload(User.emails))
        .where(User.username_lower == username.lower())
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Only the user themselves can update their profile
    if current_user.id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot edit another user's profile")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    updates: dict = {"updated_at": now}

    if body.name is not None:
        name = body.name.strip()[:255]
        updates["name"] = name if name else None

    await db.execute(update(User).where(User.id == user.id).values(**updates))
    await db.flush()

    # Re-fetch
    result = await db.execute(
        select(User)
        .options(selectinload(User.emails))
        .where(User.id == user.id)
    )
    user = result.scalar_one()
    email = user.primary_email
    avatar_url = await _get_avatar_url(db, user)
    return UserOut.from_orm(user, email=email, avatar_url=avatar_url)


@router.post("/u/{username}/avatar", response_model=UserOut)
async def upload_avatar(
    username: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    result = await db.execute(
        select(User)
        .options(selectinload(User.emails))
        .where(User.username_lower == username.lower())
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if current_user.id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot change another user's avatar")

    content_type = file.content_type or ""
    if content_type not in ALLOWED_AVATAR_MIME:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Solo se permiten imágenes JPEG, PNG, GIF o WebP",
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="El archivo está vacío")
    if len(data) > MAX_AVATAR_SIZE:
        raise HTTPException(status_code=413, detail="La imagen no puede superar 5 MB")

    # Resize to avatar size (200x200) using Pillow
    try:
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = 40_000_000  # prevent decompression bomb DoS
        img = Image.open(io.BytesIO(data))
        img = img.convert("RGB")
        img.thumbnail((200, 200), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        data = buf.getvalue()
    except Exception:
        pass  # Use original if PIL fails

    sha1 = hashlib.sha256(data).hexdigest()
    ext = "jpg"

    # Check for existing upload with same sha1
    existing = await db.execute(select(Upload).where(Upload.sha1 == sha1))
    upload = existing.scalar_one_or_none()

    if upload is None:
        # Save to disk
        p1, p2 = sha1[:2], sha1[2:4]
        sub = os.path.join(settings.UPLOADS_PATH, "avatars", p1, p2)
        os.makedirs(sub, exist_ok=True)
        fname = f"{sha1}.{ext}"
        full_path = os.path.join(sub, fname)
        if not os.path.exists(full_path):
            with open(full_path, "wb") as f:
                f.write(data)
        url = f"{settings.SITE_BASE_URL}/uploads/avatars/{p1}/{p2}/{fname}"

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        upload = Upload(
            user_id=user.id,
            original_filename=f"avatar.{ext}",
            filesize=len(data),
            url=url,
            created_at=now,
            updated_at=now,
            sha1=sha1,
            extension=ext,
            secure=False,
            verification_status=1,
        )
        db.add(upload)
        await db.flush()

    # Update user's uploaded_avatar_id
    await db.execute(
        update(User).where(User.id == user.id).values(uploaded_avatar_id=upload.id)
    )
    await db.flush()

    # Re-fetch user
    result = await db.execute(
        select(User)
        .options(selectinload(User.emails))
        .where(User.id == user.id)
    )
    user = result.scalar_one()
    return UserOut.from_orm(user, email=user.primary_email, avatar_url=upload.url)


@router.get("/u/{username}/topics")
async def user_topics(
    username: str,
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from ..core.config import settings

    result = await db.execute(select(User).where(User.username_lower == username.lower()))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    per_page = settings.TOPICS_PER_PAGE
    offset = (page - 1) * per_page

    topics_result = await db.execute(
        select(Topic)
        .where(
            Topic.user_id == user.id,
            Topic.deleted_at.is_(None),
            Topic.visible == True,
            Topic.archetype == "regular",
        )
        .order_by(desc(Topic.created_at))
        .offset(offset)
        .limit(per_page)
    )
    topics = topics_result.scalars().all()
    avatar_url = await _get_avatar_url(db, user)
    enriched = []
    for t in topics:
        d = t.__dict__.copy()
        d.pop("_sa_instance_state", None)
        d["author_username"] = user.username
        d["author_avatar_url"] = avatar_url
        enriched.append(TopicOut.model_validate(d))
    return {"topics": enriched, "page": page, "per_page": per_page}
