import sys
import asyncio

# asyncpg no es compatible con ProactorEventLoop (default en Windows)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .core.config import settings
from .routers import auth, categories, topics, posts, search, users, uploads, bookmarks


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
