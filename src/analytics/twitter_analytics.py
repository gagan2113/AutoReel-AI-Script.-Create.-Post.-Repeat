from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

TWITTER_API = "https://api.twitter.com/2"


def _get_env(name: str) -> str:
    return os.getenv(name, "").strip()


def _auth_headers() -> Dict[str, str]:
    bearer = _get_env("TWITTER_BEARER_TOKEN") or _get_env("TWITTER_V2_BEARER_TOKEN")
    return {"Authorization": f"Bearer {bearer}"} if bearer else {}


def _safe_get(url: str, params: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    try:
        r = requests.get(url, params=params, headers=headers, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}


def _get_user_id(username: str) -> Optional[str]:
    headers = _auth_headers()
    if not headers:
        return None
    data = _safe_get(f"{TWITTER_API}/users/by/username/{username}", {}, headers)
    return data.get("data", {}).get("id")


def fetch_twitter_metrics(limit: int = 20) -> pd.DataFrame:
    """Fetch recent tweets with public metrics. Requires Bearer token (App-only).

    Env required:
      - TWITTER_BEARER_TOKEN (or TWITTER_V2_BEARER_TOKEN)
      - Either TWITTER_USERNAME or TWITTER_USER_ID

    Returns DataFrame with [platform, post_id, permalink, likes, comments, views, shares, created_time].
    Notes: comments approximated by reply_count; shares approximated by retweet_count; views use view_count if available.
    """
    headers = _auth_headers()
    if not headers:
        return pd.DataFrame(columns=[
            "platform", "post_id", "permalink", "likes", "comments", "views", "shares", "created_time"
        ])

    user_id = _get_env("TWITTER_USER_ID")
    username = _get_env("TWITTER_USERNAME")
    if not user_id and username:
        user_id = _get_user_id(username)

    if not user_id:
        return pd.DataFrame(columns=[
            "platform", "post_id", "permalink", "likes", "comments", "views", "shares", "created_time"
        ])

    tweets = _safe_get(f"{TWITTER_API}/users/{user_id}/tweets", {
        "max_results": min(limit, 100),
        "tweet.fields": "created_at,public_metrics,possibly_sensitive,conversation_id,referenced_tweets,organic_metrics,non_public_metrics",
        "expansions": "attachments.media_keys",
        "media.fields": "type,public_metrics,non_public_metrics,organic_metrics,preview_image_url",
    }, headers)

    rows: List[Dict[str, Any]] = []
    for t in tweets.get("data", []):
        tid = t.get("id")
        metrics = t.get("public_metrics", {})
        like_count = metrics.get("like_count")
        reply_count = metrics.get("reply_count")
        retweet_count = metrics.get("retweet_count")
        quote_count = metrics.get("quote_count")
        view_count = metrics.get("view_count")  # Only present for some tiers

        rows.append({
            "platform": "Twitter/X",
            "post_id": tid,
            "permalink": f"https://x.com/{username}/status/{tid}" if username else None,
            "likes": like_count,
            "comments": reply_count,
            "views": view_count,
            "shares": retweet_count,
            "created_time": t.get("created_at"),
        })

    return pd.DataFrame(rows)
