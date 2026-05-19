from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

_camel = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)


class UserOut(BaseModel):
    model_config = _camel

    id: int
    username: str
    name: Optional[str] = None
    trust_level: int
    admin: bool
    moderator: bool
    active: bool
    staged: bool
    created_at: datetime
    last_seen_at: Optional[datetime] = None
    avatar_url: str
    email: Optional[str] = None

    @classmethod
    def from_orm(cls, user, email: Optional[str] = None, avatar_url: Optional[str] = None):
        return cls(
            id=user.id,
            username=user.username,
            name=user.name,
            trust_level=user.trust_level,
            admin=user.admin,
            moderator=user.moderator,
            active=user.active,
            staged=user.staged,
            created_at=user.created_at,
            last_seen_at=user.last_seen_at,
            avatar_url=avatar_url or user.avatar_url,
            email=email,
        )


class UserSummary(BaseModel):
    model_config = _camel

    id: int
    username: str
    name: Optional[str] = None
    avatar_url: str
    trust_level: int
    admin: bool
    moderator: bool
