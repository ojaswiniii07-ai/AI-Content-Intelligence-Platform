"""
Media metadata extractor.
Extracts file-level metadata using python-magic (MIME) and optionally
ffprobe (for audio/video) and Pillow (for images).

Metadata is supporting context for human reviewers — NOT proof of manipulation.
"""
from __future__ import annotations

import os
import subprocess
import json
from typing import Any, Dict, Optional

from app.schemas.media import MediaMetadata, MediaType


# ── MIME type → MediaType mapping ────────────────────────────
MIME_TO_MEDIA_TYPE: Dict[str, str] = {
    "image/jpeg": "image", "image/png": "image", "image/gif": "image",
    "image/webp": "image", "image/bmp": "image", "image/tiff": "image",
    "audio/mpeg": "audio", "audio/mp4": "audio", "audio/wav": "audio",
    "audio/ogg": "audio", "audio/flac": "audio", "audio/aac": "audio",
    "video/mp4": "video", "video/mpeg": "video", "video/webm": "video",
    "video/quicktime": "video", "video/x-msvideo": "video", "video/ogg": "video",
}

ALLOWED_MIME_TYPES = set(MIME_TO_MEDIA_TYPE.keys())


def detect_media_type(content_type: str) -> Optional[MediaType]:
    mt = MIME_TO_MEDIA_TYPE.get(content_type.split(";")[0].strip().lower())
    if mt:
        return MediaType(mt)
    return None


def extract_metadata(
    file_path: str,
    file_name: str,
    content_type: str,
    file_size_bytes: int,
    media_type: MediaType,
    ffprobe_path: str = "ffprobe",
) -> MediaMetadata:
    """
    Extract technical metadata from the file.
    All fields are Optional — never fabricated if extraction fails.
    """
    base = MediaMetadata(
        file_name=file_name,
        file_size_bytes=file_size_bytes,
        content_type=content_type,
        media_type=media_type,
    )

    if media_type == MediaType.IMAGE:
        _extract_image_metadata(file_path, base)
    elif media_type in (MediaType.AUDIO, MediaType.VIDEO):
        _extract_av_metadata(file_path, base, ffprobe_path)

    return base


def _extract_image_metadata(file_path: str, meta: MediaMetadata) -> None:
    try:
        from PIL import Image  # type: ignore
        with Image.open(file_path) as img:
            meta.width_px, meta.height_px = img.size
            meta.color_mode = img.mode
            # EXIF extraction
            try:
                exif_raw = img._getexif()
                if exif_raw:
                    from PIL.ExifTags import TAGS
                    meta.exif = {TAGS.get(k, str(k)): str(v) for k, v in exif_raw.items()}
            except Exception:
                pass
    except ImportError:
        pass  # Pillow not installed — fields remain None
    except Exception:
        pass  # Corrupt file — fields remain None


def _extract_av_metadata(file_path: str, meta: MediaMetadata, ffprobe_path: str) -> None:
    import shutil
    if not shutil.which(ffprobe_path):
        return  # ffprobe not available — skip, leave fields None

    try:
        cmd = [
            ffprobe_path, "-v", "quiet", "-print_format", "json",
            "-show_streams", "-show_format", file_path,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if proc.returncode != 0:
            return

        probe: Dict[str, Any] = json.loads(proc.stdout)
        fmt = probe.get("format", {})
        streams = probe.get("streams", [])

        # Duration from format
        if "duration" in fmt:
            meta.duration_sec = round(float(fmt["duration"]), 3)

        for stream in streams:
            codec_type = stream.get("codec_type")
            if codec_type == "video":
                meta.has_video_track = True
                meta.codec = stream.get("codec_name")
                meta.width_px = stream.get("width")
                meta.height_px = stream.get("height")
                fps_str = stream.get("r_frame_rate", "")
                if "/" in fps_str:
                    num, den = fps_str.split("/")
                    if int(den) > 0:
                        meta.fps = round(int(num) / int(den), 3)
                if meta.duration_sec and meta.fps:
                    meta.frame_count = int(meta.duration_sec * meta.fps)
            elif codec_type == "audio":
                meta.has_audio_track = True
                meta.sample_rate_hz = int(stream.get("sample_rate", 0) or 0) or None
                meta.channels = stream.get("channels")
                meta.bit_depth = stream.get("bits_per_sample") or None

    except Exception:
        pass  # Extraction failures leave fields None — never fabricated
