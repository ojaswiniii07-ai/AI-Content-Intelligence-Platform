"""
Private file storage for uploaded media.

Files are written to MEDIA_UPLOAD_DIR (default: ./uploads/media/).
The storage path is opaque and never served as a public URL.
Files are deleted by the worker after analysis completes.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path


def get_upload_dir() -> Path:
    base = Path(os.getenv("MEDIA_UPLOAD_DIR", "./uploads/media")).resolve()
    base.mkdir(parents=True, exist_ok=True)
    return base


def write_temp_file(
    data: bytes,
    original_name: str,
    content_type: str,
) -> tuple[str, str, datetime]:
    """
    Write uploaded bytes to private storage.

    Returns:
        (upload_id, absolute_storage_path, expires_at)

    The storage_path is an absolute internal path — never exposed as a URL.
    expires_at is set to 24h from now; workers clean files after completion.
    """
    ext = Path(original_name).suffix or _ext_from_mime(content_type)
    upload_id = f"upl_{uuid.uuid4().hex}"
    file_path = get_upload_dir() / f"{upload_id}{ext}"

    file_path.write_bytes(data)

    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    return upload_id, str(file_path), expires_at


def delete_file(storage_path: str) -> None:
    try:
        p = Path(storage_path)
        if p.exists():
            p.unlink()
    except Exception:
        pass


def _ext_from_mime(content_type: str) -> str:
    mapping = {
        "image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif",
        "image/webp": ".webp", "image/tiff": ".tiff", "image/bmp": ".bmp",
        "audio/mpeg": ".mp3", "audio/wav": ".wav", "audio/ogg": ".ogg",
        "audio/flac": ".flac", "audio/aac": ".aac", "audio/mp4": ".m4a",
        "video/mp4": ".mp4", "video/webm": ".webm", "video/mpeg": ".mpg",
        "video/quicktime": ".mov", "video/x-msvideo": ".avi",
    }
    return mapping.get(content_type.split(";")[0].strip(), "")
