from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

_camel = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)


class PostCreate(BaseModel):
    topic_id: int
    raw: str
    reply_to_post_number: Optional[int] = None


class PostUpdate(BaseModel):
    raw: str
    edit_reason: Optional[str] = None


class PostOut(BaseModel):
    model_config = _camel

    id: int
    user_id: Optional[int] = None
    topic_id: int
    post_number: int
    raw: str
    cooked: str
    reply_to_post_number: Optional[int] = None
    reply_count: int
    like_count: int
    reads: int
    post_type: int
    version: int
    wiki: bool
    hidden: bool
    user_deleted: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    edit_reason: Optional[str] = None
    author_username: Optional[str] = None
    author_name: Optional[str] = None
    author_avatar_url: Optional[str] = None
    can_edit: bool = False
    can_delete: bool = False
    liked_by_me: bool = False
    bookmarked_by_me: bool = False


class TopicWithDetails(BaseModel):
    model_config = _camel

    id: int
    title: str
    fancy_title: Optional[str] = None
    slug: Optional[str] = None
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
    archetype: str
    created_at: datetime
    updated_at: datetime
    bumped_at: datetime
    last_posted_at: Optional[datetime] = None
    author_username: Optional[str] = None
    author_avatar_url: Optional[str] = None
    can_edit: bool = False
    can_close: bool = False


class TopicWithPostsResponse(BaseModel):
    model_config = _camel

    topic: TopicWithDetails
    posts: List[PostOut]
    total_posts: int
    page: int
    per_page: int


class SearchResult(BaseModel):
    model_config = _camel

    topic_id: int
    title: str
    slug: Optional[str] = None
    excerpt: str
    category_id: Optional[int] = None
    created_at: datetime
    posts_count: int
    author_username: Optional[str] = None
    rank: float


class SearchResponse(BaseModel):
    model_config = _camel

    results: List[SearchResult]
    total: int
    query: str
