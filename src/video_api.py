"""
Video generation API wrapper.

This module isolates all video-related logic so it can be swapped out without
touching the main app or workflow code. Implementors can replace the stubbed
HTTP call below with their preferred provider (e.g., OpenAI, Pika, Runway, etc.).

Environment variables:
- VIDEO_API_BASE_URL: Base URL of your video generation service (e.g., https://api.example.com)
- VIDEO_API_KEY:      API key for auth; sent as Bearer token if provided

Contract:
- generate_video(...) returns a dict like:
  {
    "status": "success" | "error",
    "video_url": "https://..."  # optional, when available
    "job_id": "abc123"          # optional, when async
    "message": "human-readable status or error"
  }

If VIDEO_API_BASE_URL is not configured, a local mock response is returned to
allow the rest of the app to function during development.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional
import os
import json
import time
import requests
from requests.exceptions import RequestException
from dotenv import load_dotenv

load_dotenv()


VIDEO_API_BASE_URL = os.getenv("VIDEO_API_BASE_URL", "").strip()
VIDEO_API_KEY = os.getenv("VIDEO_API_KEY", "").strip()
VIDEO_API_TIMEOUT = float(os.getenv("VIDEO_API_TIMEOUT", "60"))


def _headers() -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if VIDEO_API_KEY:
        h["Authorization"] = f"Bearer {VIDEO_API_KEY}"
    return h


def generate_video(
    *,
    script_text: str,
    product_name: str,
    platforms: List[str],
    aspect_ratios: List[str],
    duration_seconds: int,
    voice: Optional[str] = None,
    music_style: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a video from the provided script. If VIDEO_API_BASE_URL is set,
    this will POST to `<BASE_URL>/generate`. Otherwise, returns a mocked
    successful response for development.
    """
    payload: Dict[str, Any] = {
        "script": script_text,
        "meta": {
            "product_name": product_name,
            "platforms": platforms,
            "aspect_ratios": aspect_ratios,
            "duration_seconds": duration_seconds,
            "voice": voice,
            "music_style": music_style,
        },
    }

    # Development fallback: no external service configured
    if not VIDEO_API_BASE_URL:
        # Simulate brief processing time
        time.sleep(0.5)
        return {
            "status": "success",
            "video_url": "https://example.com/placeholder-video.mp4",
            "job_id": "dev-mock-job-0001",
            "message": "VIDEO_API_BASE_URL not set. Returning mock URL.",
        }

    url = VIDEO_API_BASE_URL.rstrip("/") + "/generate"
    try:
        resp = requests.post(url, headers=_headers(), data=json.dumps(payload), timeout=VIDEO_API_TIMEOUT)
    except RequestException as e:
        return {
            "status": "error",
            "message": f"Failed to reach video API: {e}",
        }

    if not resp.ok:
        # Attempt to extract JSON error
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        return {
            "status": "error",
            "message": f"Video API error {resp.status_code}: {str(detail)[:1000]}",
        }

    try:
        data = resp.json()
    except ValueError:
        return {
            "status": "error",
            "message": f"Video API returned non-JSON response: {resp.text[:500]}",
        }

    # Normalize output keys
    return {
        "status": data.get("status", "success"),
        "video_url": data.get("video_url"),
        "job_id": data.get("job_id"),
        "message": data.get("message", ""),
    }


def extract_final_script(text: str) -> str:
    """
    Extract a usable narration script from the app output.

    - If the input is a JSON array of scene objects with "narration_text",
      join those lines into a single script (one per scene).
    - Otherwise, fall back to extracting the content under the legacy
      "## Final Script" markdown header.
    - If neither format matches, return the raw input.
    """
    if not text:
        return ""

    s = text.strip()
    # Try JSON scenes first
    if s.startswith("["):
        try:
            data = json.loads(s)
            if isinstance(data, list) and all(isinstance(x, dict) for x in data):
                narr_lines: list[str] = []
                for scene in data:
                    nt = scene.get("narration_text") if isinstance(scene, dict) else None  # type: ignore[attr-defined]
                    if isinstance(nt, str) and nt.strip():
                        narr_lines.append(nt.strip())
                if narr_lines:
                    return "\n".join(narr_lines)
        except Exception:
            pass

    # Legacy markdown fallback
    lines = s.splitlines()
    collecting = False
    buf: list[str] = []
    for line in lines:
        if line.strip().lower().startswith("##") and "final script" in line.strip().lower():
            collecting = True
            continue
        if collecting and line.strip().startswith("## "):
            break
        if collecting:
            buf.append(line)
    text2 = "\n".join(buf).strip()
    return text2 if text2 else s
