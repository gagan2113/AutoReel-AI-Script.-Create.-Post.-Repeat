"""
Google Veo 3 video generation wrapper.

Environment variables:
- GOOGLE_VEO_API_KEY: API key for auth
- GOOGLE_VEO_API_BASE_URL: Base URL for Veo 3 service (e.g., https://veo.googleapis.com)
- GOOGLE_VEO_TIMEOUT: Optional timeout seconds (default: 120)

Contract:
generate_veo_clip(prompt, duration_seconds, out_path) -> dict
  Returns { status: 'success'|'error', message: str, video_url?: str }
  Saves the MP4 to out_path when possible (direct download or returned URL fetch).

Note: This is a generic wrapper; wire it to your actual Veo 3 endpoint shape.
"""
from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

import requests
from requests.exceptions import RequestException
from dotenv import load_dotenv


load_dotenv()


VEO_BASE = (os.getenv("GOOGLE_VEO_API_BASE_URL") or "").strip()
VEO_KEY = (os.getenv("GOOGLE_VEO_API_KEY") or "").strip()
VEO_TIMEOUT = float(os.getenv("GOOGLE_VEO_TIMEOUT", "120"))


def _headers() -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if VEO_KEY:
        h["Authorization"] = f"Bearer {VEO_KEY}"
    return h


def _download_file(url: str, dest: Path) -> None:
    with requests.get(url, stream=True, timeout=VEO_TIMEOUT) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def generate_veo_clip(*, visual_prompt: str, duration_seconds: int, out_path: Path) -> Dict[str, Any]:
    """Generate a video clip using Veo 3 and save to out_path.

    This implementation assumes a generic POST to <BASE_URL>/v1/generate with
    JSON payload and a response containing either a streaming URL or direct URL.
    Adjust the endpoint and response parsing to your actual API.
    """
    if not VEO_BASE:
        return {"status": "error", "message": "GOOGLE_VEO_API_BASE_URL is not set"}
    if not VEO_KEY:
        return {"status": "error", "message": "GOOGLE_VEO_API_KEY is not set"}

    url = VEO_BASE.rstrip("/") + "/v1/generate"
    payload = {
        "model": "veo-3",
        "prompt": visual_prompt,
        "duration_seconds": int(duration_seconds),
        "format": "mp4",
    }
    try:
        resp = requests.post(url, headers=_headers(), data=json.dumps(payload), timeout=VEO_TIMEOUT)
    except RequestException as e:
        return {"status": "error", "message": f"Network error: {e}"}

    if not resp.ok:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        return {"status": "error", "message": f"Veo API error {resp.status_code}: {str(detail)[:800]}"}

    try:
        data = resp.json()
    except ValueError:
        return {"status": "error", "message": "Veo API returned non-JSON response"}

    # Example response handling (adapt this to your API):
    # - Direct URL: data["video_url"]
    # - Or binary content at data["video_base64"] (not implemented)
    video_url: Optional[str] = data.get("video_url")  # type: ignore[assignment]
    if video_url:
        try:
            _download_file(video_url, out_path)
            return {"status": "success", "message": "Downloaded clip", "video_url": video_url}
        except Exception as e:
            return {"status": "error", "message": f"Failed to download video: {e}"}

    # If the API supports direct binary streaming, adjust here accordingly.
    return {"status": "error", "message": "Unsupported Veo response shape; no video_url found"}


__all__ = ["generate_veo_clip"]
