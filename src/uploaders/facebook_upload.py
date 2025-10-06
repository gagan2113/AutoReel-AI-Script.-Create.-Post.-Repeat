from __future__ import annotations

from .utils import UploadResult, require_env


def upload(video_path_or_url: str, caption: str, hashtags: list[str]) -> UploadResult:
    platform = "Facebook"
    page_access_token = require_env("FACEBOOK_PAGE_ACCESS_TOKEN")
    page_id = require_env("FACEBOOK_PAGE_ID")
    if not (page_access_token and page_id):
        return UploadResult(platform, "error", message="Missing FACEBOOK_PAGE_ACCESS_TOKEN or FACEBOOK_PAGE_ID")

    # TODO: Implement Facebook Graph API video upload to page.
    mock_url = f"https://www.facebook.com/{page_id}/videos/9876543210"
    return UploadResult(platform, "success", url=mock_url, message="Uploaded (simulated)")
