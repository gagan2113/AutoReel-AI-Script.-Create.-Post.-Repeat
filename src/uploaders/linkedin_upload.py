from __future__ import annotations

from .utils import UploadResult, require_env


def upload(video_path_or_url: str, caption: str, hashtags: list[str]) -> UploadResult:
    platform = "LinkedIn"
    access_token = require_env("LINKEDIN_ACCESS_TOKEN")
    if not access_token:
        return UploadResult(platform, "error", message="Missing LINKEDIN_ACCESS_TOKEN")

    # TODO: Implement LinkedIn UGC Posts API upload.
    mock_url = "https://www.linkedin.com/feed/update/urn:li:activity:1234567890"
    return UploadResult(platform, "success", url=mock_url, message="Uploaded (simulated)")
