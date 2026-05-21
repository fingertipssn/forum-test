import logging
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ..core.database import get_db
from ..core.security import get_current_user, require_current_user
from ..schemas.post import SearchResponse, SearchResult
from ..core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)
logger = logging.getLogger(__name__)


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=2, description="Search query"),
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = q.strip()
    if not q:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Query cannot be empty")

    per_page = 20
    offset = (page - 1) * per_page
    q_like = f"%{q}%"  # para búsqueda ILIKE de fallback

    # Estrategia dual:
    # 1. Si post_search_data tiene tsvector indexado → usa @@ websearch_to_tsquery (rápido)
    # 2. Siempre añade fallback ILIKE en título y cuerpo del primer post
    # LEFT JOIN garantiza que la búsqueda funciona aunque post_search_data esté vacía.

    sql = text("""
        SELECT DISTINCT ON (t.id)
            t.id              AS topic_id,
            t.title,
            t.slug,
            t.category_id,
            t.created_at,
            t.posts_count,
            u.username        AS author_username,
            left(p.raw, 300)  AS excerpt,
            CASE
                WHEN psd.search_data IS NOT NULL
                     AND psd.search_data @@ websearch_to_tsquery('english', :q)
                THEN ts_rank_cd(psd.search_data, websearch_to_tsquery('english', :q)) + 1.0
                ELSE 0.0
            END AS rank
        FROM topics t
        JOIN posts p
            ON p.topic_id = t.id
            AND p.post_number = 1
            AND p.deleted_at IS NULL
        LEFT JOIN post_search_data psd
            ON psd.post_id = p.id
        LEFT JOIN users u
            ON u.id = t.user_id
        WHERE
            t.deleted_at IS NULL
            AND t.visible  = true
            AND t.archetype = 'regular'
            AND (
                (psd.search_data IS NOT NULL
                 AND psd.search_data @@ websearch_to_tsquery('english', :q))
                OR t.title ILIKE :q_like
                OR p.raw   ILIKE :q_like
            )
        ORDER BY t.id, rank DESC
        LIMIT :limit OFFSET :offset
    """)

    count_sql = text("""
        SELECT COUNT(DISTINCT t.id)
        FROM topics t
        JOIN posts p
            ON p.topic_id = t.id
            AND p.post_number = 1
            AND p.deleted_at IS NULL
        LEFT JOIN post_search_data psd
            ON psd.post_id = p.id
        WHERE
            t.deleted_at IS NULL
            AND t.visible  = true
            AND t.archetype = 'regular'
            AND (
                (psd.search_data IS NOT NULL
                 AND psd.search_data @@ websearch_to_tsquery('english', :q))
                OR t.title ILIKE :q_like
                OR p.raw   ILIKE :q_like
            )
    """)

    try:
        params = {"q": q, "q_like": q_like, "limit": per_page, "offset": offset}
        rows = (await db.execute(sql, params)).fetchall()
        count_row = (await db.execute(count_sql, {"q": q, "q_like": q_like})).fetchone()
    except Exception as exc:
        # websearch_to_tsquery puede fallar con sintaxis especial → fallback solo ILIKE
        logger.warning("Search tsvector query failed (%s), falling back to ILIKE only", exc)
        sql_fallback = text("""
            SELECT DISTINCT ON (t.id)
                t.id              AS topic_id,
                t.title,
                t.slug,
                t.category_id,
                t.created_at,
                t.posts_count,
                u.username        AS author_username,
                left(p.raw, 300)  AS excerpt,
                0.0               AS rank
            FROM topics t
            JOIN posts p
                ON p.topic_id = t.id
                AND p.post_number = 1
                AND p.deleted_at IS NULL
            LEFT JOIN users u ON u.id = t.user_id
            WHERE
                t.deleted_at IS NULL
                AND t.visible  = true
                AND t.archetype = 'regular'
                AND (t.title ILIKE :q_like OR p.raw ILIKE :q_like)
            ORDER BY t.id DESC
            LIMIT :limit OFFSET :offset
        """)
        count_fallback = text("""
            SELECT COUNT(DISTINCT t.id)
            FROM topics t
            JOIN posts p
                ON p.topic_id = t.id AND p.post_number = 1 AND p.deleted_at IS NULL
            WHERE t.deleted_at IS NULL AND t.visible = true AND t.archetype = 'regular'
              AND (t.title ILIKE :q_like OR p.raw ILIKE :q_like)
        """)
        rows = (await db.execute(sql_fallback, {"q_like": q_like, "limit": per_page, "offset": offset})).fetchall()
        count_row = (await db.execute(count_fallback, {"q_like": q_like})).fetchone()

    total = count_row[0] if count_row else 0

    results = [
        SearchResult(
            topic_id=row.topic_id,
            title=row.title,
            slug=row.slug,
            excerpt=row.excerpt or "",
            category_id=row.category_id,
            created_at=row.created_at,
            posts_count=row.posts_count,
            author_username=row.author_username,
            rank=float(row.rank),
        )
        for row in rows
    ]

    return SearchResponse(results=results, total=total, query=q)


@router.post("/search/reindex")
async def reindex_all(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    """
    Reconstruye post_search_data y topic_search_data para todos los posts existentes.
    Solo disponible en DEV_MODE.
    """
    if not settings.DEV_MODE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo disponible en modo desarrollo")

    # Indexar posts que aún no tienen entrada en post_search_data
    result = await db.execute(text("""
        INSERT INTO post_search_data (post_id, search_data, raw_data, locale, version, private_message)
        SELECT
            p.id,
            to_tsvector('english', COALESCE(t.title, '') || ' ' || COALESCE(p.raw, '')),
            COALESCE(t.title, '') || ' ' || COALESCE(p.raw, ''),
            'english',
            1,
            false
        FROM posts p
        JOIN topics t ON t.id = p.topic_id
        WHERE p.deleted_at IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM post_search_data psd WHERE psd.post_id = p.id
          )
    """))
    posts_indexed = result.rowcount

    # Indexar topics que aún no tienen entrada en topic_search_data
    result2 = await db.execute(text("""
        INSERT INTO topic_search_data (topic_id, search_data, raw_data, locale, version)
        SELECT
            t.id,
            to_tsvector('english', COALESCE(t.title, '') || ' ' || COALESCE(p.raw, '')),
            COALESCE(t.title, '') || ' ' || COALESCE(p.raw, ''),
            'english',
            1
        FROM topics t
        JOIN posts p ON p.topic_id = t.id AND p.post_number = 1
        WHERE t.deleted_at IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM topic_search_data tsd WHERE tsd.topic_id = t.id
          )
    """))
    topics_indexed = result2.rowcount

    logger.info("Reindex: %d posts, %d topics indexed", posts_indexed, topics_indexed)
    return {
        "status": "ok",
        "posts_indexed": posts_indexed,
        "topics_indexed": topics_indexed,
    }
