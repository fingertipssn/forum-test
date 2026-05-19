from typing import Optional
from pydantic import BaseModel


class UploadOut(BaseModel):
    id: int
    url: str
    original_filename: str
    filesize: int
    width: Optional[int] = None
    height: Optional[int] = None
    extension: Optional[str] = None
    thumbnail_width: Optional[int] = None
    thumbnail_height: Optional[int] = None

    model_config = {"from_attributes": True}
