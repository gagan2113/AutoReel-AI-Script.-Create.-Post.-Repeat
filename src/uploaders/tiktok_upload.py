from __future__ import annotations

from .utils import UploadResult, require_env


def upload(video_path_or_url: str, caption: str, hashtags: list[str]) -> UploadResult:
    platform = "TikTok"
    access_token = require_env("TIKTOK_ACCESS_TOKEN")
    if not access_token:
        return UploadResult(platform, "error", message="Missing TIKTOK_ACCESS_TOKEN in environment")

    # TODO: Replace with real TikTok API integration.
    # For now, simulate success and echo back a mock post URL.
    mock_url = "https://www.tiktok.com/@youraccount/video/1234567890"
    return UploadResult(platform, "success", url=mock_url, message="Uploaded (simulated)")
