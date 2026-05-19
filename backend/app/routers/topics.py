from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update
from sqlalchemy.orm import selectinload

from ..core.database import get_db
from ..core.security import get_current_user, require_current_user
from ..core.guardian import Guardian
from ..core.config import settings
from ..models.topic import Topic
from ..models.post import Post
from ..models.user import User
from ..models.category import Category
from ..models.upload import Upload
from ..models.post_action import PostAction, LIKE_TYPE_ID, BOOKMARK_TYPE_ID
from ..schemas.topic import TopicCreate, TopicUpdate, TopicOut, TopicListResponse
from ..schemas.post import TopicWithPostsResponse, TopicWithDetails, PostOut
from ..services.topic_creator import TopicCreatorService

router = APIRouter()


def _enrich_topic(topic: Topic, author: Optional[User], avatar_url: Optional[str] = None) -> TopicOut:
    data = TopicOut.model_validate(topic)
    if author:
        data.author_username = author.username
        data.author_name = author.name
        data.author_avatar_url = avatar_url or author.avatar_url
    return data


async def _resolve_avatar_urls(db: AsyncSession, users_map: dict) -> dict[int, str]:
    """Batch-resolve real avatar URLs for a map of user_id → User."""
    upload_ids = {u.uploaded_avatar_id for u in users_map.values() if u.uploaded_avatar_id}
    uploads_by_id: dict[int, str] = {}
    if upload_ids:
        up_result = await db.execute(select(Upload).where(Upload.id.in_(upload_ids)))
        for up in up_result.scalars():
            uploads_by_id[up.id] = up.url
    result: dict[int, str] = {}
    for uid, u in users_map.items():
        if u.uploaded_avatar_id and u.uploaded_avatar_id in uploads_by_id:
            result[uid] = uploads_by_id[u.uploaded_avatar_id]
        else:
            result[uid] = u.avatar_url
    return result


@router.get("/topics/latest", response_model=TopicListResponse)
async def latest_topics(
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    guardian = Guardian(current_user)
    per_page = settings.TOPICS_PER_PAGE
    offset = (page - 1) * per_page

    stmt = (
        select(Topic)
        .where(Topic.deleted_at.is_(None), Topic.visible == True, Topic.archetype == "regular")
        .order_by(desc(Topic.bumped_at))
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    topics = result.scalars().all()

    user_ids = list({t.user_id for t in topics if t.user_id})
    users_map: dict[int, User] = {}
    if user_ids:
        users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        for u in users_result.scalars():
            users_map[u.id] = u

    avatar_url_map = await _resolve_avatar_urls(db, users_map)

    from sqlalchemy import func
    count_result = await db.execute(
        select(func.count(Topic.id)).where(
            Topic.deleted_at.is_(None), Topic.visible == True, Topic.archetype == "regular"
        )
    )
    total = count_result.scalar_one()

    enriched = [
        _enrich_topic(t, users_map.get(t.user_id), avatar_url_map.get(t.user_id))
        for t in topics if guardian.can_see_topic(t)
    ]
    return TopicListResponse(topics=enriched, total=total, page=page, per_page=per_page)


@router.get("/c/{slug}/topics", response_model=TopicListResponse)
async def category_topics(
    slug: str,
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from sqlalchemy import func

    cat_result = await db.execute(select(Category).where(Category.slug == slug))
    category = cat_result.scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    guardian = Guardian(current_user)
    if not guardian.can_see_category(category):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    per_page = settings.TOPICS_PER_PAGE
    offset = (page - 1) * per_page

    stmt = (
        select(Topic)
        .where(
            Topic.category_id == category.id,
            Topic.deleted_at.is_(None),
            Topic.visible == True,
            Topic.archetype == "regular",
        )
        .order_by(desc(Topic.bumped_at))
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    topics = result.scalars().all()

    user_ids = list({t.user_id for t in topics if t.user_id})
    users_map: dict[int, User] = {}
    if user_ids:
        users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        for u in users_result.scalars():
            users_map[u.id] = u

    avatar_url_map = await _resolve_avatar_urls(db, users_map)

    count_result = await db.execute(
        select(func.count(Topic.id)).where(
            Topic.category_id == category.id,
            Topic.deleted_at.is_(None),
            Topic.visible == True,
            Topic.archetype == "regular",
        )
    )
    total = count_result.scalar_one()

    enriched = [
        _enrich_topic(t, users_map.get(t.user_id), avatar_url_map.get(t.user_id))
        for t in topics
    ]
    return TopicListResponse(topics=enriched, total=total, page=page, per_page=per_page)


@router.get("/t/{topic_id}", response_model=TopicWithPostsResponse)
async def get_topic(
    topic_id: int,
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from sqlalchemy import func

    topic_result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = topic_result.scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    category = None
    if topic.category_id:
        cat_result = await db.execute(select(Category).where(Category.id == topic.category_id))
        category = cat_result.scalar_one_or_none()

    guardian = Guardian(current_user)
    guardian.ensure_can_see_topic(topic, category)

    per_page = settings.POSTS_PER_PAGE
    offset = (page - 1) * per_page

    posts_stmt = (
        select(Post)
        .where(Post.topic_id == topic_id, Post.deleted_at.is_(None), Post.hidden == False)
        .order_by(Post.post_number)
        .offset(offset)
        .limit(per_page)
    )
    posts_result = await db.execute(posts_stmt)
    posts = posts_result.scalars().all()

    user_ids = {p.user_id for p in posts if p.user_id}
    if topic.user_id:
        user_ids.add(topic.user_id)
    users_map: dict[int, User] = {}
    if user_ids:
        ur = await db.execute(select(User).where(User.id.in_(user_ids)))
        for u in ur.scalars():
            users_map[u.id] = u

    # Resolve uploaded avatar URLs (users with a custom avatar)
    avatar_url_map = await _resolve_avatar_urls(db, users_map)

    count_result = await db.execute(
        select(func.count(Post.id)).where(
            Post.topic_id == topic_id,
            Post.deleted_at.is_(None),
            Post.hidden == False,
        )
    )
    total_posts = count_result.scalar_one()

    await db.execute(update(Topic).where(Topic.id == topic_id).values(views=Topic.views + 1))

    author = users_map.get(topic.user_id) if topic.user_id else None
    topic_out = TopicWithDetails(
        id=topic.id,
        title=topic.title,
        fancy_title=topic.fancy_title,
        slug=topic.slug,
        posts_count=topic.posts_count,
        reply_count=topic.reply_count,
        views=topic.views + 1,
        like_count=topic.like_count,
        category_id=topic.category_id,
        user_id=topic.user_id,
        visible=topic.visible,
        closed=topic.closed,
        archived=topic.archived,
        pinned_globally=topic.pinned_globally,
        archetype=topic.archetype,
        created_at=topic.created_at,
        updated_at=topic.updated_at,
        bumped_at=topic.bumped_at,
        last_posted_at=topic.last_posted_at,
        author_username=author.username if author else None,
        author_avatar_url=avatar_url_map.get(author.id) if author else None,
        can_edit=guardian.can_edit_topic(topic),
        can_close=guardian.is_staff,
    )

    # Fetch post actions for current user (liked/bookmarked)
    liked_post_ids: set[int] = set()
    bookmarked_post_ids: set[int] = set()
    if current_user and posts:
        post_ids = [p.id for p in posts]
        actions_result = await db.execute(
            select(PostAction).where(
                PostAction.post_id.in_(post_ids),
                PostAction.user_id == current_user.id,
                PostAction.post_action_type_id.in_([LIKE_TYPE_ID, BOOKMARK_TYPE_ID]),
                PostAction.deleted_at.is_(None),
            )
        )
        for action in actions_result.scalars():
            if action.post_action_type_id == LIKE_TYPE_ID:
                liked_post_ids.add(action.post_id)
            elif action.post_action_type_id == BOOKMARK_TYPE_ID:
                bookmarked_post_ids.add(action.post_id)

    posts_out = []
    for p in posts:
        post_author = users_map.get(p.user_id) if p.user_id else None
        posts_out.append(
            PostOut(
                id=p.id,
                user_id=p.user_id,
                topic_id=p.topic_id,
                post_number=p.post_number,
                raw=p.raw,
                cooked=p.cooked,
                reply_to_post_number=p.reply_to_post_number,
                reply_count=p.reply_count,
                like_count=p.like_count,
                reads=p.reads,
                post_type=p.post_type,
                version=p.version,
                wiki=p.wiki,
                hidden=p.hidden,
                user_deleted=p.user_deleted,
                created_at=p.created_at,
                updated_at=p.updated_at,
                deleted_at=p.deleted_at,
                edit_reason=p.edit_reason,
                author_username=post_author.username if post_author else None,
                author_name=post_author.name if post_author else None,
                author_avatar_url=avatar_url_map.get(post_author.id) if post_author else None,
                can_edit=guardian.can_edit_post(p),
                can_delete=guardian.can_delete_post(p),
                liked_by_me=p.id in liked_post_ids,
                bookmarked_by_me=p.id in bookmarked_post_ids,
            )
        )

    return TopicWithPostsResponse(
        topic=topic_out,
        posts=posts_out,
        total_posts=total_posts,
        page=page,
        per_page=per_page,
    )


@router.post("/t", response_model=TopicOut, status_code=status.HTTP_201_CREATED)
async def create_topic(
    payload: TopicCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    guardian = Guardian(current_user)
    svc = TopicCreatorService(
        db=db,
        user=current_user,
        guardian=guardian,
        title=payload.title,
        raw=payload.raw,
        category_id=payload.category_id,
    )
    ctx = await svc.call()
    if not ctx.success:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=ctx.errors)

    topic = ctx.result["topic"]
    return _enrich_topic(topic, current_user)


@router.put("/t/{topic_id}", response_model=TopicOut)
async def update_topic(
    topic_id: int,
    payload: TopicUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    guardian = Guardian(current_user)
    if not guardian.can_edit_topic(topic):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot edit this topic")

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    updates = {"updated_at": now}
    if payload.title:
        from ..services.topic_creator import _slugify
        updates["title"] = payload.title
        updates["fancy_title"] = payload.title
        updates["slug"] = _slugify(payload.title)
    if payload.category_id is not None:
        updates["category_id"] = payload.category_id

    await db.execute(update(Topic).where(Topic.id == topic_id).values(**updates))
    await db.flush()

    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one()
    return _enrich_topic(topic, current_user)


@router.delete("/t/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(
    topic_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    guardian = Guardian(current_user)
    if not guardian.can_delete_topic(topic):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete this topic")

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.execute(
        update(Topic).where(Topic.id == topic_id).values(
            deleted_at=now,
            deleted_by_id=current_user.id,
            updated_at=now,
        )
    )
