"""Uploaders package

Contains per-platform upload modules and a router to dispatch uploads.
All modules read credentials from environment variables loaded via .env.
"""

from .router import upload_to_platforms, SUPPORTED_PLATFORMS

__all__ = [
    "upload_to_platforms",
    "SUPPORTED_PLATFORMS",
]
