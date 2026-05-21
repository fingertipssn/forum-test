import sys
import asyncio

# asyncpg no es compatible con ProactorEventLoop (default en Windows)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .core.config import settings
from .routers import auth, categories, topics, posts, search, users, uploads, bookmarks

_docs_url = "/api/docs" if settings.DEBUG else None
_redoc_url = "/api/redoc" if settings.DEBUG else None
_openapi_url = "/api/openapi.json" if settings.DEBUG else None

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self' https://login.microsoftonline.com; "
        "frame-ancestors 'none';"
    )
    return response

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(categories.router, prefix="/api", tags=["categories"])
app.include_router(topics.router, prefix="/api", tags=["topics"])
app.include_router(posts.router, prefix="/api", tags=["posts"])
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(uploads.router, prefix="/api", tags=["uploads"])
app.include_router(bookmarks.router, prefix="/api", tags=["bookmarks"])

uploads_path = settings.UPLOADS_PATH
os.makedirs(uploads_path, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
