from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

GRAPH_BASE = "https://graph.facebook.com/v18.0"


def _get_env(name: str) -> str:
    return os.getenv(name, "").strip()


def _safe_get(url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def fetch_instagram_metrics(limit: int = 20) -> pd.DataFrame:
    """Fetch recent Instagram media metrics.

    Env required:
      - INSTAGRAM_BUSINESS_ACCOUNT_ID
      - INSTAGRAM_ACCESS_TOKEN (page access token with instagram_basic, instagram_manage_insights)

    Returns a DataFrame with columns: [platform, post_id, permalink, likes, comments, views, shares, created_time]
    Note: IG doesn't expose shares directly; shares will be None.
    """
    ig_id = _get_env("INSTAGRAM_BUSINESS_ACCOUNT_ID")
    token = _get_env("INSTAGRAM_ACCESS_TOKEN") or _get_env("FACEBOOK_PAGE_ACCESS_TOKEN")
    if not (ig_id and token):
        return pd.DataFrame(columns=[
            "platform", "post_id", "permalink", "likes", "comments", "views", "shares", "created_time"
        ])

    media_url = f"{GRAPH_BASE}/{ig_id}/media"
    media_params = {
        "access_token": token,
        "fields": "id,media_type,caption,permalink,timestamp",
        "limit": limit,
    }
    media_data = _safe_get(media_url, media_params)
    items: List[Dict[str, Any]] = []
    for m in (media_data.get("data", []) if media_data else []):
        media_id = m.get("id")
        permalink = m.get("permalink")
        created_time = m.get("timestamp")

        # insights: likes (from /{id}?fields=like_count for IG Graph), comments_count, video_views for video
        like_count = None
        comments_count = None
        video_views = None

        # Basic fields
        details = _safe_get(f"{GRAPH_BASE}/{media_id}", {
            "access_token": token,
            "fields": "like_count,comments_count,media_type"
        }) or {}
        like_count = details.get("like_count")
        comments_count = details.get("comments_count")

        if details.get("media_type") in ("VIDEO", "REELS", "IGTV"):
            insights = _safe_get(f"{GRAPH_BASE}/{media_id}/insights", {
                "metric": "video_views",
                "access_token": token,
            }) or {}
            try:
                data = insights.get("data", [])
                if data and data[0].get("values"):
                    video_views = data[0]["values"][0].get("value")
            except Exception:
                pass

        items.append({
            "platform": "Instagram",
            "post_id": media_id,
            "permalink": permalink,
            "likes": like_count,
            "comments": comments_count,
            "views": video_views,
            "shares": None,
            "created_time": created_time,
        })

    return pd.DataFrame(items)
