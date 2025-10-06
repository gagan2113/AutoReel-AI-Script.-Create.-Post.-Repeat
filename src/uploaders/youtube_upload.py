from __future__ import annotations

from .utils import UploadResult, require_env


def upload(video_path_or_url: str, caption: str, hashtags: list[str]) -> UploadResult:
    platform = "YouTube"
    api_key = require_env("YOUTUBE_API_KEY")
    oauth_token = require_env("YOUTUBE_OAUTH_TOKEN")
    if not (api_key or oauth_token):
        return UploadResult(platform, "error", message="Missing YOUTUBE_API_KEY or YOUTUBE_OAUTH_TOKEN")

    # TODO: Implement YouTube Data API v3 upload.
    mock_url = "https://youtu.be/abcdef12345"
    return UploadResult(platform, "success", url=mock_url, message="Uploaded (simulated)")
