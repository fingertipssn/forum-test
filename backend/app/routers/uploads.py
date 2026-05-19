import hashlib
import io
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.database import get_db
from ..core.security import require_current_user
from ..models.upload import Upload, OptimizedImage, UploadReference
from ..schemas.upload import UploadOut

router = APIRouter()

ALLOWED_MIME = {
    "image/jpeg", "image/png", "image/gif",
    "image/webp", "image/svg+xml",
}
ALLOWED_EXT = {"jpg", "jpeg", "png", "gif", "webp", "svg"}
MAX_SIZE_BYTES = 10 * 1024 * 1024   # 10 MB
THUMBNAIL_MAX_W = 690               # ancho máximo en posts (igual que Discourse)


def _ext_from(filename: str, content_type: str) -> str:
    if "." in (filename or ""):
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext in ALLOWED_EXT:
            return ext
    return {
        "image/jpeg": "jpg", "image/png": "png",
        "image/gif": "gif",  "image/webp": "webp",
        "image/svg+xml": "svg",
    }.get(content_type, "bin")


def _save_to_disk(data: bytes, sha1: str, ext: str) -> tuple[str, str]:
    """Guarda el archivo y devuelve (ruta_absoluta, url_relativa)."""
    p1, p2 = sha1[:2], sha1[2:4]
    sub = os.path.join(settings.UPLOADS_PATH, p1, p2)
    os.makedirs(sub, exist_ok=True)
    fname = f"{sha1}.{ext}"
    full_path = os.path.join(sub, fname)
    if not os.path.exists(full_path):
        with open(full_path, "wb") as f:
            f.write(data)
    url = f"{settings.SITE_BASE_URL}/uploads/{p1}/{p2}/{fname}"
    return full_path, url


def _process_image(data: bytes, ext: str):
    """
    Usa Pillow para obtener dimensiones, color dominante y generar thumbnail.
    Devuelve (width, height, thumbnail_width, thumbnail_height,
               thumb_data, thumb_sha1, dominant_color, animated).
    """
    if ext == "svg":
        return None, None, None, None, None, None, None, False

    try:
        from PIL import Image, ImageStat
        img = Image.open(io.BytesIO(data))
        orig_w, orig_h = img.width, img.height
        animated = getattr(img, "is_animated", False)

        # Color dominante (primeros 6 chars hex) igual que Discourse
        try:
            flat = img.convert("RGB").resize((50, 50))
            stat = ImageStat.Stat(flat)
            r, g, b = [int(c) for c in stat.mean[:3]]
            dominant_color = f"{r:02x}{g:02x}{b:02x}"
        except Exception:
            dominant_color = None

        # Thumbnail: solo si la imagen es más ancha que el límite
        thumb_data = None
        thumb_sha1 = None
        thumb_w = thumb_h = None

        if orig_w > THUMBNAIL_MAX_W and ext not in ("gif", "svg"):
            ratio = THUMBNAIL_MAX_W / orig_w
            thumb_w = THUMBNAIL_MAX_W
            thumb_h = int(orig_h * ratio)
            thumb_img = img.convert("RGB").resize(
                (thumb_w, thumb_h), Image.LANCZOS
            )
            buf = io.BytesIO()
            thumb_img.save(buf, format="JPEG", quality=85, optimize=True)
            thumb_data = buf.getvalue()
            thumb_sha1 = hashlib.sha1(thumb_data).hexdigest()

        return orig_w, orig_h, thumb_w, thumb_h, thumb_data, thumb_sha1, dominant_color, animated

    except Exception:
        return None, None, None, None, None, None, None, False


@router.post("/uploads", response_model=UploadOut, status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    # ── 1. Validaciones básicas ──────────────────────────────────────────────
    content_type = file.content_type or ""
    if content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Tipo no permitido: {content_type}. Solo se aceptan imágenes.",
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")
    if len(data) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo supera el límite de {MAX_SIZE_BYTES // 1024 // 1024} MB.",
        )

    # ── 2. SHA1 y deduplicación ──────────────────────────────────────────────
    sha1 = hashlib.sha1(data).hexdigest()
    ext = _ext_from(file.filename or "", content_type)

    existing = await db.execute(
        select(Upload).where(Upload.sha1 == sha1)
    )
    existing_upload = existing.scalar_one_or_none()
    if existing_upload:
        return existing_upload

    # ── 3. Procesar imagen (dimensiones, thumbnail, color dominante) ─────────
    orig_w, orig_h, thumb_w, thumb_h, thumb_data, thumb_sha1, dominant_color, animated = (
        _process_image(data, ext)
    )

    # ── 4. Guardar original en disco ─────────────────────────────────────────
    _, url = _save_to_disk(data, sha1, ext)

    # ── 5. Crear registro en uploads ─────────────────────────────────────────
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    upload = Upload(
        user_id=current_user.id,
        original_filename=file.filename or f"{sha1}.{ext}",
        filesize=len(data),
        width=orig_w,
        height=orig_h,
        url=url,
        created_at=now,
        updated_at=now,
        sha1=sha1,
        extension=ext,
        thumbnail_width=thumb_w,
        thumbnail_height=thumb_h,
        secure=False,
        verification_status=1,
        animated=animated,
        dominant_color=dominant_color,
    )
    db.add(upload)
    await db.flush()   # obtenemos el id sin cerrar la transacción

    # ── 6. Crear optimized_image si hay thumbnail ────────────────────────────
    if thumb_data and thumb_sha1 and thumb_w and thumb_h:
        _, thumb_url = _save_to_disk(thumb_data, thumb_sha1, "jpg")

        optimized = OptimizedImage(
            upload_id=upload.id,
            sha1=thumb_sha1,
            extension="jpg",
            width=thumb_w,
            height=thumb_h,
            url=thumb_url,
            filesize=len(thumb_data),
            version=2,
            created_at=now,
            updated_at=now,
        )
        db.add(optimized)

    return upload


@router.post("/uploads/{upload_id}/reference", status_code=status.HTTP_201_CREATED)
async def create_upload_reference(
    upload_id: int,
    target_type: str,
    target_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    """
    Registra la relación entre un upload y un post o tema.
    Llamado automáticamente por el frontend después de publicar.
    target_type: 'Post' | 'Topic'
    """
    if target_type not in ("Post", "Topic"):
        raise HTTPException(status_code=400, detail="target_type debe ser 'Post' o 'Topic'")

    # Verificar que el upload existe
    result = await db.execute(select(Upload).where(Upload.id == upload_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Upload no encontrado")

    # Evitar duplicados
    existing = await db.execute(
        select(UploadReference).where(
            UploadReference.upload_id == upload_id,
            UploadReference.target_type == target_type,
            UploadReference.target_id == target_id,
        )
    )
    if existing.scalar_one_or_none():
        return {"status": "already_exists"}

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    ref = UploadReference(
        upload_id=upload_id,
        target_type=target_type,
        target_id=target_id,
        created_at=now,
        updated_at=now,
    )
    db.add(ref)
    return {"status": "created"}
