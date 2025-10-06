from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Ensure environment variables from .env are loaded once.
load_dotenv()


@dataclass
class UploadResult:
    platform: str
    status: str  # "success" | "error"
    url: Optional[str] = None
    message: str = ""


def require_env(name: str) -> str:
    """Return env var value or empty string if missing."""
    return os.getenv(name, "").strip()
