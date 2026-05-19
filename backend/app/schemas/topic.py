from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

_camel = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)


class TopicCreate(BaseModel):
    title: str
    raw: str
    category_id: Optional[int] = None
    tags: List[str] = []


class TopicUpdate(BaseModel):
    title: Optional[str] = None
    category_id: Optional[int] = None


class TopicOut(BaseModel):
    model_config = _camel

    id: int
    title: str
    fancy_title: Optional[str] = None
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    posts_count: int
    reply_count: int
    views: int
    like_count: int
    category_id: Optional[int] = None
    user_id: Optional[int] = None
    visible: bool
    closed: bool
    archived: bool
    pinned_globally: bool
    pinned_at: Optional[datetime] = None
    archetype: str
    created_at: datetime
    updated_at: datetime
    bumped_at: datetime
    last_posted_at: Optional[datetime] = None
    author_username: Optional[str] = None
    author_name: Optional[str] = None
    author_avatar_url: Optional[str] = None


class TopicListResponse(BaseModel):
    model_config = _camel

    topics: List[TopicOut]
    total: int
    page: int
    per_page: int
