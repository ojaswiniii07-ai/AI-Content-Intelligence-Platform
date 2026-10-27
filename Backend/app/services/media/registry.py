"""
Adapter registry — central lookup for all registered detector adapters.
Routers and workers import from here; never import adapters directly.

To add a new detector: subclass BaseDetectorAdapter and register below.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from app.services.media.base import BaseDetectorAdapter
from app.services.media.image_adapter import ImageSyntheticAdapter
from app.services.media.audio_adapter import AudioSyntheticAdapter
from app.services.media.video_adapter import AVConsistencyAdapter, VideoManipulationAdapter

# All registered adapters
_ADAPTERS: List[BaseDetectorAdapter] = [
    ImageSyntheticAdapter(),
    AudioSyntheticAdapter(),
    VideoManipulationAdapter(),
    AVConsistencyAdapter(),
]

# Quick lookup by key
_ADAPTER_MAP: Dict[str, BaseDetectorAdapter] = {a.ADAPTER_KEY: a for a in _ADAPTERS}


def get_adapters_for_media_type(
    media_type: str,
    requested_keys: Optional[List[str]] = None,
) -> List[BaseDetectorAdapter]:
    """
    Return adapters suitable for `media_type`.
    If `requested_keys` is provided and non-empty, filter to only those keys.
    Always returns a list (may be empty).
    """
    candidates = [a for a in _ADAPTERS if media_type in a.MEDIA_TYPES]
    if requested_keys:
        candidates = [a for a in candidates if a.ADAPTER_KEY in requested_keys]
    return candidates


def get_adapter(key: str) -> Optional[BaseDetectorAdapter]:
    return _ADAPTER_MAP.get(key)


def list_all_adapters() -> List[Dict]:
    """Returns a registry summary useful for /docs and health endpoints."""
    return [
        {
            "key": a.ADAPTER_KEY,
            "media_types": a.MEDIA_TYPES,
            "is_configured": a.is_configured(),
            "status": "ready" if a.is_configured() else "not_configured",
            "supports_regions": getattr(a, "supports_regions", False),
            "supports_frame_refs": getattr(a, "supports_frame_refs", False),
            "supports_time_ranges": getattr(a, "supports_time_ranges", False),
        }
        for a in _ADAPTERS
    ]

