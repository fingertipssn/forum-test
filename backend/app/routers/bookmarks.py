from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..core.security import require_current_user
from ..models.post_action import PostAction, BOOKMARK_TYPE_ID
from ..models.post import Post
from ..models.topic import Topic
from ..models.user import User
from ..models.upload import Upload

router = APIRouter()


@router.get("/bookmarks")
async def get_bookmarks(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    """Return all posts bookmarked by the current user, grouped by topic."""

    # 1. Fetch all active bookmarks for the user
    actions_result = await db.execute(
        select(PostAction)
        .where(
            PostAction.user_id == current_user.id,
            PostAction.post_action_type_id == BOOKMARK_TYPE_ID,
            PostAction.deleted_at.is_(None),
        )
        .order_by(PostAction.created_at.desc())
    )
    actions = actions_result.scalars().all()
    if not actions:
        return {"bookmarks": []}

    post_ids = [a.post_id for a in actions]

    # 2. Fetch the posts
    posts_result = await db.execute(
        select(Post).where(Post.id.in_(post_ids), Post.deleted_at.is_(None))
    )
    posts_by_id = {p.id: p for p in posts_result.scalars()}

    # 3. Fetch the topics
    topic_ids = list({p.topic_id for p in posts_by_id.values()})
    topics_result = await db.execute(
        select(Topic).where(Topic.id.in_(topic_ids), Topic.deleted_at.is_(None))
    )
    topics_by_id = {t.id: t for t in topics_result.scalars()}

    # 4. Fetch topic authors (for avatar)
    author_ids = list({t.user_id for t in topics_by_id.values() if t.user_id})
    authors_by_id: dict[int, User] = {}
    if author_ids:
        authors_result = await db.execute(select(User).where(User.id.in_(author_ids)))
        for u in authors_result.scalars():
            authors_by_id[u.id] = u

    # 5. Resolve avatar URLs
    upload_ids = {u.uploaded_avatar_id for u in authors_by_id.values() if u.uploaded_avatar_id}
    uploads_map: dict[int, str] = {}
    if upload_ids:
        up_result = await db.execute(select(Upload).where(Upload.id.in_(upload_ids)))
        for up in up_result.scalars():
            uploads_map[up.id] = up.url

    def _avatar(user: User) -> str:
        if user.uploaded_avatar_id and user.uploaded_avatar_id in uploads_map:
            return uploads_map[user.uploaded_avatar_id]
        return user.avatar_url

    # 6. Build response — one entry per bookmarked post
    items = []
    for action in actions:
        post = posts_by_id.get(action.post_id)
        if not post:
            continue
        topic = topics_by_id.get(post.topic_id)
        if not topic:
            continue
        author = authors_by_id.get(topic.user_id) if topic.user_id else None

        # Short excerpt from the bookmarked post
        excerpt = post.raw[:120].replace("\n", " ") + ("…" if len(post.raw) > 120 else "")

        items.append({
            "postId": post.id,
            "postNumber": post.post_number,
            "topicId": topic.id,
            "topicTitle": topic.title,
            "topicSlug": topic.slug,
            "categoryId": topic.category_id,
            "excerpt": excerpt,
            "bookmarkedAt": action.created_at,
            "authorUsername": author.username if author else None,
            "authorName": author.name if author else None,
            "authorAvatarUrl": _avatar(author) if author else None,
        })

    return {"bookmarks": items}
