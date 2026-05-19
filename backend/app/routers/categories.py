import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc, func, desc

from ..core.database import get_db
from ..core.security import get_current_user, require_current_user
from ..core.guardian import Guardian
from ..core.config import settings
from ..models.category import Category
from ..models.topic import Topic
from ..models.user import User
from ..schemas.category import CategoryOut, CategoryListResponse, CategoryCreate, CategoryRecentTopic

router = APIRouter()


def _slugify_category(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    return slug[:100] or "category"


@router.get("/categories", response_model=CategoryListResponse)
async def list_categories(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    guardian = Guardian(current_user)

    result = await db.execute(
        select(Category)
        .where(Category.parent_category_id.is_(None))
        .order_by(asc(Category.position), asc(Category.id))
    )
    categories = result.scalars().all()

    visible = [c for c in categories if guardian.can_see_category(c)]

    # Fetch latest 3 topics per visible category
    if visible:
        cat_ids = [c.id for c in visible]
        topics_result = await db.execute(
            select(Topic)
            .where(
                Topic.category_id.in_(cat_ids),
                Topic.deleted_at.is_(None),
                Topic.visible == True,
                Topic.archetype == "regular",
            )
            .order_by(desc(Topic.bumped_at))
        )
        all_topics = topics_result.scalars().all()

        # Group by category and keep only 3 per category
        topics_by_cat: dict[int, list] = defaultdict(list)
        for t in all_topics:
            if t.category_id and len(topics_by_cat[t.category_id]) < 3:
                topics_by_cat[t.category_id].append(t)

        # Fetch authors
        user_ids = {t.user_id for cats in topics_by_cat.values() for t in cats if t.user_id}
        users_map: dict[int, User] = {}
        if user_ids:
            ur = await db.execute(select(User).where(User.id.in_(user_ids)))
            for u in ur.scalars():
                users_map[u.id] = u
    else:
        topics_by_cat = {}
        users_map = {}

    category_outs = []
    for c in visible:
        c_out = CategoryOut.model_validate(c)
        latest = topics_by_cat.get(c.id, [])
        c_out.latest_topics = [
            CategoryRecentTopic(
                id=t.id,
                title=t.title,
                slug=t.slug,
                last_posted_at=t.last_posted_at,
                posts_count=t.posts_count,
                author_username=users_map[t.user_id].username if t.user_id and t.user_id in users_map else None,
            )
            for t in latest
        ]
        category_outs.append(c_out)

    return CategoryListResponse(categories=category_outs)


@router.post("/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    guardian = Guardian(current_user)
    # En modo dev cualquier usuario autenticado puede crear categorías.
    # En producción solo staff.
    if not settings.DEV_MODE and not guardian.is_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden crear categorías",
        )

    # Generar slug único
    base_slug = _slugify_category(payload.name)
    slug = base_slug
    suffix = 1
    while True:
        existing = await db.execute(select(Category).where(Category.slug == slug))
        if existing.scalar_one_or_none() is None:
            break
        slug = f"{base_slug}-{suffix}"
        suffix += 1

    # Siguiente posición
    pos_result = await db.execute(select(func.max(Category.position)))
    max_pos = pos_result.scalar() or 0

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    category = Category(
        name=payload.name.strip(),
        name_lower=payload.name.strip().lower(),
        slug=slug,
        color=payload.color,
        text_color=payload.text_color,
        description=payload.description,
        user_id=current_user.id,
        parent_category_id=payload.parent_category_id,
        read_restricted=False,
        topic_count=0,
        post_count=0,
        allow_badges=True,
        search_priority=0,
        position=max_pos + 1,
        created_at=now,
        updated_at=now,
    )
    db.add(category)
    await db.flush()
    return CategoryOut.model_validate(category)


@router.get("/categories/{slug}", response_model=CategoryOut)
async def get_category(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Category).where(Category.slug == slug))
    category = result.scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    guardian = Guardian(current_user)
    if not guardian.can_see_category(category):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return CategoryOut.model_validate(category)
