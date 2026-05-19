from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.alias_generators import to_camel

_camel = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)


class CategoryRecentTopic(BaseModel):
    model_config = _camel

    id: int
    title: str
    slug: Optional[str] = None
    last_posted_at: Optional[datetime] = None
    posts_count: int = 0
    author_username: Optional[str] = None


class CategoryOut(BaseModel):
    model_config = _camel

    id: int
    name: str
    slug: str
    color: str
    text_color: str
    description: Optional[str] = None
    topic_count: int
    post_count: int
    parent_category_id: Optional[int] = None
    read_restricted: bool
    position: Optional[int] = None
    topic_template: Optional[str] = None
    emoji: Optional[str] = None
    icon: Optional[str] = None
    created_at: datetime
    latest_topics: List[CategoryRecentTopic] = []


class CategoryListResponse(BaseModel):
    model_config = _camel

    categories: List[CategoryOut]


class CategoryCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str
    description: Optional[str] = None
    color: str = "0088CC"
    text_color: str = "FFFFFF"
    parent_category_id: Optional[int] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El nombre no puede estar vacío")
        if len(v) > 50:
            raise ValueError("El nombre no puede superar 50 caracteres")
        return v

    @field_validator("color", "text_color")
    @classmethod
    def valid_hex(cls, v: str) -> str:
        v = v.strip().lstrip("#")
        if len(v) not in (3, 6) or not all(c in "0123456789abcdefABCDEF" for c in v):
            raise ValueError("Color debe ser un código hexadecimal válido (ej. 0088CC)")
        return v.upper().zfill(6)
