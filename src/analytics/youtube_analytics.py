from __future__ import annotations

import os
from typing import Any, Dict, List

import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API = "https://www.googleapis.com/youtube/v3"


def _get_env(name: str) -> str:
    return os.getenv(name, "").strip()


def _safe_get(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}


def fetch_youtube_metrics(limit: int = 20) -> pd.DataFrame:
    """Fetch recent YouTube videos and statistics for a channel.

    Env required:
      - YOUTUBE_API_KEY
      - YOUTUBE_CHANNEL_ID

    Returns DataFrame with [platform, post_id, permalink, likes, comments, views, shares, created_time].
    Note: shares are not provided by YouTube Data API; set to None.
    """
    api_key = _get_env("YOUTUBE_API_KEY")
    channel_id = _get_env("YOUTUBE_CHANNEL_ID")
    if not (api_key and channel_id):
        return pd.DataFrame(columns=[
            "platform", "post_id", "permalink", "likes", "comments", "views", "shares", "created_time"
        ])

    # Get latest uploads via search
    search = _safe_get(f"{YOUTUBE_API}/search", {
        "key": api_key,
        "channelId": channel_id,
        "part": "id,snippet",
        "order": "date",
        "maxResults": min(limit, 50),
        "type": "video",
    })

    video_ids: List[str] = [item["id"]["videoId"] for item in search.get("items", []) if item.get("id", {}).get("videoId")]
    if not video_ids:
        return pd.DataFrame(columns=[
            "platform", "post_id", "permalink", "likes", "comments", "views", "shares", "created_time"
        ])

    # Fetch statistics in bulk
    stats = _safe_get(f"{YOUTUBE_API}/videos", {
        "key": api_key,
        "id": ",".join(video_ids),
        "part": "statistics,snippet",
    })

    rows: List[Dict[str, Any]] = []
    for item in stats.get("items", []):
        vid = item.get("id")
        snippet = item.get("snippet", {})
        st = item.get("statistics", {})
        rows.append({
            "platform": "YouTube",
            "post_id": vid,
            "permalink": f"https://youtu.be/{vid}",
            "likes": int(st.get("likeCount", 0)) if st.get("likeCount") is not None else None,
            "comments": int(st.get("commentCount", 0)) if st.get("commentCount") is not None else None,
            "views": int(st.get("viewCount", 0)) if st.get("viewCount") is not None else None,
            "shares": None,
            "created_time": snippet.get("publishedAt"),
        })

    return pd.DataFrame(rows)
