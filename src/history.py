import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import requests
from dotenv import load_dotenv

Collection = Any  # loose typing to avoid optional dependency issues


load_dotenv()


def _slugify(text: str, max_len: int = 60) -> str:
    text = text.strip().lower()
    # Replace non-alphanumeric with hyphens
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:max_len] or "reel"


def get_base_dir() -> Path:
    # Project root is one level above this file (src/)
    return Path(__file__).resolve().parents[1]


def get_reels_dir() -> Path:
    base = get_base_dir()
    reels_dir = base / "reels"
    reels_dir.mkdir(parents=True, exist_ok=True)
    return reels_dir


def get_mongo_collection() -> Optional["Collection"]:
    """Return the MongoDB collection for reels history or None if not configured.

    Env support (first found wins):
      - MONGODB_URI
      - client  (back-compat based on current .env)
    Optional:
      - MONGODB_DB (default: autoreel_ai)
      - MONGODB_COLLECTION (default: reels)
    """
    uri = os.getenv("MONGODB_URI") or os.getenv("client")
    if not uri:
        return None
    # Import at runtime to avoid import errors if not installed during tests
    try:
        from pymongo import MongoClient  # type: ignore
    except Exception:
        return None
    db_name = os.getenv("MONGODB_DB", "autoreel_ai")
    coll_name = os.getenv("MONGODB_COLLECTION", "reels")
    client = MongoClient(uri)
    db = client[db_name]
    return db[coll_name]


def create_versioned_folder_and_download(title: str, video_url: str, filename: str = "video.mp4") -> Optional[str]:
    """Download the video to a versioned folder under project/reels and return relative file path.

    Returns a path relative to the project root (e.g., "reels/20251007-121314-title/video.mp4"), or None on failure.
    """
    try:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        slug = _slugify(title)
        folder = get_reels_dir() / f"{ts}-{slug}"
        folder.mkdir(parents=True, exist_ok=True)
        dest = folder / filename

        # Stream download
        with requests.get(video_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        # Return relative path from project root
        rel_path = dest.relative_to(get_base_dir()).as_posix()
        return rel_path
    except Exception:
        return None


def save_reel_record(title: str, file_value: str, date_iso: Optional[str] = None, id_value: Optional[str] = None) -> bool:
    """Persist a minimal record to MongoDB: { id, title, date, file }.

    - file_value can be a local relative path or a remote URL.
    Returns True on success, False otherwise.
    """
    coll = get_mongo_collection()
    if coll is None:
        return False
    try:
        # Minimal payload only
        record = {
            "id": id_value or datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "title": title,
            "date": date_iso or datetime.now().isoformat(timespec="seconds"),
            "file": file_value,
        }
        coll.insert_one(record)
        return True
    except Exception:
        return False


def list_reels(limit: int = 20) -> List[Dict[str, Any]]:
    """Return a list of recent reels from MongoDB sorted by newest first.

    If Mongo isn't configured, returns an empty list.
    """
    coll = get_mongo_collection()
    if coll is None:
        return []
    try:
        # Sort by natural insertion order descending if date is absent
        docs = coll.find({}, {"_id": 0, "id": 1, "title": 1, "date": 1, "file": 1}).sort("date", -1).limit(limit)
        return list(docs)
    except Exception:
        return []
