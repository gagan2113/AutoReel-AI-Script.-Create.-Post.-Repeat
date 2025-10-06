from __future__ import annotations

from typing import List, Dict

from .utils import UploadResult
from . import tiktok_upload, youtube_upload, linkedin_upload, facebook_upload, twitter_upload


SUPPORTED_PLATFORMS = [
    "TikTok",
    "YouTube",
    "LinkedIn",
    "Facebook",
    "Twitter/X",
]


def upload_to_platforms(video_path_or_url: str, caption: str, hashtags: List[str], platforms: List[str]) -> Dict[str, UploadResult]:
    """Dispatch uploads to the selected platforms and return per-platform results."""
    results: Dict[str, UploadResult] = {}
    for p in platforms:
        p_norm = p.strip()
        try:
            if p_norm == "TikTok":
                results[p_norm] = tiktok_upload.upload(video_path_or_url, caption, hashtags)
            elif p_norm == "YouTube":
                results[p_norm] = youtube_upload.upload(video_path_or_url, caption, hashtags)
            elif p_norm == "LinkedIn":
                results[p_norm] = linkedin_upload.upload(video_path_or_url, caption, hashtags)
            elif p_norm == "Facebook":
                results[p_norm] = facebook_upload.upload(video_path_or_url, caption, hashtags)
            elif p_norm == "Twitter/X":
                results[p_norm] = twitter_upload.upload(video_path_or_url, caption, hashtags)
            else:
                results[p_norm] = UploadResult(p_norm, "error", message="Platform not supported")
        except Exception as e:
            results[p_norm] = UploadResult(p_norm, "error", message=str(e))
    return results
