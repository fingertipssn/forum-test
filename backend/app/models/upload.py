from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, Boolean, Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base


class Upload(Base):
    """Tabla uploads de Discourse — registro de cada archivo subido."""
    __tablename__ = "uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    filesize: Mapped[int] = mapped_column(BigInteger, nullable=False)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    url: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    sha1: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    origin: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    retain_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extension: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    thumbnail_width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    thumbnail_height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    etag: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    secure: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    access_control_post_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    original_sha1: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    animated: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    verification_status: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    security_last_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    security_last_changed_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    dominant_color: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class OptimizedImage(Base):
    """Tabla optimized_images — versiones redimensionadas/optimizadas de uploads."""
    __tablename__ = "optimized_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sha1: Mapped[str] = mapped_column(String, nullable=False)
    extension: Mapped[str] = mapped_column(String, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    upload_id: Mapped[int] = mapped_column(Integer, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    filesize: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    etag: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class UploadReference(Base):
    """Tabla upload_references — relación N:N entre uploads y posts/temas."""
    __tablename__ = "upload_references"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    upload_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    target_type: Mapped[str] = mapped_column(String, nullable=False)  # 'Post' | 'Topic'
    target_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
