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


def fetch_facebook_metrics(limit: int = 20) -> pd.DataFrame:
    """Fetch recent Facebook Page video metrics.

    Env required:
      - FACEBOOK_PAGE_ID
      - FACEBOOK_PAGE_ACCESS_TOKEN

    Returns DataFrame with columns [platform, post_id, permalink, likes, comments, views, shares, created_time].
    """
    page_id = _get_env("FACEBOOK_PAGE_ID")
    token = _get_env("FACEBOOK_PAGE_ACCESS_TOKEN")
    if not (page_id and token):
        return pd.DataFrame(columns=[
            "platform", "post_id", "permalink", "likes", "comments", "views", "shares", "created_time"
        ])

    # Get recent videos posted by the page
    videos_url = f"{GRAPH_BASE}/{page_id}/videos"
    videos_params = {
        "access_token": token,
        "fields": "id,permalink_url,created_time,content_category",
        "limit": limit,
    }
    videos_data = _safe_get(videos_url, videos_params)

    rows: List[Dict[str, Any]] = []
    for v in (videos_data.get("data", []) if videos_data else []):
        vid = v.get("id")
        permalink = v.get("permalink_url")
        created_time = v.get("created_time")

        # Reactions summary (as likes proxy)
        reactions = _safe_get(f"{GRAPH_BASE}/{vid}/reactions", {
            "access_token": token,
            "summary": "total_count",
            "limit": 0,
        }) or {}
        likes = reactions.get("summary", {}).get("total_count")

        # Comments count
        comments = _safe_get(f"{GRAPH_BASE}/{vid}/comments", {
            "access_token": token,
            "summary": "total_count",
            "filter": "toplevel",
            "limit": 0,
        }) or {}
        comments_count = comments.get("summary", {}).get("total_count")

        # Shares count (for posts; for videos, sometimes via /sharedposts)
        shared = _safe_get(f"{GRAPH_BASE}/{vid}", {
            "access_token": token,
            "fields": "shares",
        }) or {}
        shares = (shared.get("shares") or {}).get("count")

        # Views via video_insights metric: total_video_impressions or total_video_views
        insights = _safe_get(f"{GRAPH_BASE}/{vid}/video_insights", {
            "access_token": token,
            "metric": "total_video_views",
        }) or {}
        views = None
        try:
            data = insights.get("data", [])
            if data and data[0].get("values"):
                views = data[0]["values"][0].get("value")
        except Exception:
            pass

        rows.append({
            "platform": "Facebook",
            "post_id": vid,
            "permalink": permalink,
            "likes": likes,
            "comments": comments_count,
            "views": views,
            "shares": shares,
            "created_time": created_time,
        })

    return pd.DataFrame(rows)
