from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List

import pandas as pd
from dotenv import load_dotenv

from src.analytics import (
    fetch_instagram_metrics,
    fetch_facebook_metrics,
    fetch_youtube_metrics,
    fetch_twitter_metrics,
)

load_dotenv()


def merge_frames(frames: List[pd.DataFrame]) -> pd.DataFrame:
    cols = ["platform", "post_id", "permalink", "likes", "comments", "views", "shares", "created_time"]
    norm = []
    for df in frames:
        if df is None or df.empty:
            continue
        # Ensure all expected columns exist
        for c in cols:
            if c not in df.columns:
                df[c] = None
        norm.append(df[cols])
    if not norm:
        return pd.DataFrame(columns=cols)
    return pd.concat(norm, ignore_index=True)


def store_sqlite(df: pd.DataFrame, db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path.as_posix()) as conn:
        # Create or replace table
        df.to_sql("analytics", conn, if_exists="append", index=False)


if __name__ == "__main__":
    # Fetch from all platforms
    ig = fetch_instagram_metrics(limit=20)
    fb = fetch_facebook_metrics(limit=20)
    yt = fetch_youtube_metrics(limit=20)
    tw = fetch_twitter_metrics(limit=20)

    merged = merge_frames([ig, fb, yt, tw])

    # Drop duplicate rows by (platform, post_id)
    if not merged.empty:
        merged = merged.drop_duplicates(subset=["platform", "post_id"], keep="last")

    db = Path("analytics.db")
    if not merged.empty:
        store_sqlite(merged, db)
        print(f"Stored {len(merged)} rows into {db}")
    else:
        print("No analytics data fetched.")
