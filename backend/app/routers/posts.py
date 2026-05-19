from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from ..core.database import get_db
from ..core.security import require_current_user
from ..core.guardian import Guardian
from ..models.post import Post
from ..models.topic import Topic
from ..models.user import User
from ..models.upload import Upload
from ..models.post_action import PostAction, LIKE_TYPE_ID, BOOKMARK_TYPE_ID
from ..schemas.post import PostCreate, PostUpdate, PostOut
from ..services.post_creator import PostCreatorService

router = APIRouter()


async def _resolve_avatar_url(db: AsyncSession, user) -> str:
    """Return the user's real avatar URL (custom upload or letter-avatar fallback)."""
    if user.uploaded_avatar_id:
        result = await db.execute(select(Upload).where(Upload.id == user.uploaded_avatar_id))
        upload = result.scalar_one_or_none()
        if upload:
            return upload.url
    return user.avatar_url


@router.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post(
    payload: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    guardian = Guardian(current_user)
    svc = PostCreatorService(
        db=db,
        user=current_user,
        guardian=guardian,
        topic_id=payload.topic_id,
        raw=payload.raw,
        reply_to_post_number=payload.reply_to_post_number,
    )
    ctx = await svc.call()
    if not ctx.success:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=ctx.errors)

    post = ctx.result["post"]
    avatar_url = await _resolve_avatar_url(db, current_user)
    return PostOut(
        id=post.id,
        user_id=post.user_id,
        topic_id=post.topic_id,
        post_number=post.post_number,
        raw=post.raw,
        cooked=post.cooked,
        reply_to_post_number=post.reply_to_post_number,
        reply_count=post.reply_count,
        like_count=post.like_count,
        reads=post.reads,
        post_type=post.post_type,
        version=post.version,
        wiki=post.wiki,
        hidden=post.hidden,
        user_deleted=post.user_deleted,
        created_at=post.created_at,
        updated_at=post.updated_at,
        deleted_at=post.deleted_at,
        edit_reason=post.edit_reason,
        author_username=current_user.username,
        author_name=current_user.name,
        author_avatar_url=avatar_url,
        can_edit=True,
        can_delete=True,
    )


@router.put("/posts/{post_id}", response_model=PostOut)
async def update_post(
    post_id: int,
    payload: PostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    guardian = Guardian(current_user)
    guardian.ensure_can_edit_post(post)

    from ..services.markdown_renderer import render, count_words

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    raw = payload.raw.strip()
    if not raw:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Post cannot be empty")

    cooked = render(raw)

    await db.execute(
        update(Post)
        .where(Post.id == post_id)
        .values(
            raw=raw,
            cooked=cooked,
            edit_reason=payload.edit_reason,
            version=Post.version + 1,
            self_edits=Post.self_edits + 1,
            last_editor_id=current_user.id,
            word_count=count_words(raw),
            updated_at=now,
        )
    )
    await db.flush()

    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one()

    avatar_url = await _resolve_avatar_url(db, current_user)
    return PostOut(
        id=post.id,
        user_id=post.user_id,
        topic_id=post.topic_id,
        post_number=post.post_number,
        raw=post.raw,
        cooked=post.cooked,
        reply_to_post_number=post.reply_to_post_number,
        reply_count=post.reply_count,
        like_count=post.like_count,
        reads=post.reads,
        post_type=post.post_type,
        version=post.version,
        wiki=post.wiki,
        hidden=post.hidden,
        user_deleted=post.user_deleted,
        created_at=post.created_at,
        updated_at=post.updated_at,
        deleted_at=post.deleted_at,
        edit_reason=post.edit_reason,
        author_username=current_user.username,
        author_name=current_user.name,
        author_avatar_url=avatar_url,
        can_edit=guardian.can_edit_post(post),
        can_delete=guardian.can_delete_post(post),
    )


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    guardian = Guardian(current_user)
    guardian.ensure_can_delete_post(post)

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.execute(
        update(Post)
        .where(Post.id == post_id)
        .values(deleted_at=now, deleted_by_id=current_user.id, updated_at=now)
    )


async def _toggle_post_action(
    db: AsyncSession,
    post_id: int,
    user_id: int,
    action_type_id: int,
) -> bool:
    """Toggle a post action (like/bookmark). Returns True if now active, False if removed."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    existing_result = await db.execute(
        select(PostAction).where(
            PostAction.post_id == post_id,
            PostAction.user_id == user_id,
            PostAction.post_action_type_id == action_type_id,
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing is None:
        # Create new action
        action = PostAction(
            post_id=post_id,
            user_id=user_id,
            post_action_type_id=action_type_id,
            created_at=now,
            updated_at=now,
            deleted_at=None,
            staff_took_action=False,
            targets_topic=False,
        )
        db.add(action)
        return True
    elif existing.deleted_at is not None:
        # Re-activate
        await db.execute(
            update(PostAction)
            .where(PostAction.id == existing.id)
            .values(deleted_at=None, updated_at=now)
        )
        return True
    else:
        # Soft-delete (toggle off)
        await db.execute(
            update(PostAction)
            .where(PostAction.id == existing.id)
            .values(deleted_at=now, deleted_by_id=user_id, updated_at=now)
        )
        return False


@router.post("/posts/{post_id}/like")
async def toggle_like(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    now_active = await _toggle_post_action(db, post_id, current_user.id, LIKE_TYPE_ID)

    # Update like_count on the post
    delta = 1 if now_active else -1
    await db.execute(
        update(Post)
        .where(Post.id == post_id)
        .values(like_count=Post.like_count + delta)
    )
    await db.flush()

    # Return updated like_count
    result = await db.execute(select(Post.like_count).where(Post.id == post_id))
    like_count = result.scalar_one()
    return {"liked": now_active, "likeCount": like_count}


@router.post("/posts/{post_id}/bookmark")
async def toggle_bookmark(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    now_active = await _toggle_post_action(db, post_id, current_user.id, BOOKMARK_TYPE_ID)
    await db.flush()
    return {"bookmarked": now_active}
