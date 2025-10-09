from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Dict, Any, Tuple

from dotenv import load_dotenv


load_dotenv()


DEFAULT_TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts").strip() or "gpt-4o-mini-tts"

# Conservatively provide a small curated list of OpenAI voices.
# This can be expanded as OpenAI adds more voices.
OPENAI_VOICES: List[str] = [
    "alloy",
    "verse",
]


def _slugify(text: str, max_len: int = 60) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:max_len] or "voiceover"


def ensure_output_dir(base_reels_dir: Path, title: str | None = None) -> Path:
    """Create and return a fresh timestamped folder to hold voice files.

    Example: reels/20251009-101112-product-name/
    """
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = _slugify(title or "voiceover")
    folder = base_reels_dir / f"{ts}-{slug}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def normalize_for_speech(text: str) -> str:
    """Lightly normalize narration text to encourage natural pauses.

    - Ensure sentences end with punctuation.
    - Collapse excessive whitespace.
    - Preserve commas/periods to let the TTS engine pause naturally.
    """
    if not text:
        return ""
    s = re.sub(r"\s+", " ", text).strip()
    if s and s[-1] not in ".!?":
        s += "."
    return s


def _get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not found in environment (.env)")
    try:
        from openai import OpenAI  # type: ignore
    except Exception as e:
        raise RuntimeError("The 'openai' package is required. Add it to requirements and install.") from e
    return OpenAI(api_key=api_key)


def synthesize_mp3(text: str, voice: str, dest_path: Path, model: str = DEFAULT_TTS_MODEL) -> None:
    """Synthesize speech using OpenAI TTS and save as MP3 to dest_path."""
    client = _get_openai_client()
    # Prefer streaming response for memory efficiency
    try:
        with client.audio.speech.with_streaming_response.create(  # type: ignore[attr-defined]
            model=model,
            voice=voice,
            input=text,
            format="mp3",
        ) as response:
            response.stream_to_file(str(dest_path))
            return
    except Exception:
        # Fallback to non-streaming if available
        audio = client.audio.speech.create(model=model, voice=voice, input=text, format="mp3")
        # Some client versions return a bytes-like object at .content or .read()
        data = getattr(audio, "content", None)
        if data is None and hasattr(audio, "read"):
            data = audio.read()
        if not data:
            raise RuntimeError("OpenAI TTS returned empty audio data")
        dest_path.write_bytes(data)


def generate_scene_voiceovers(
    scenes: Iterable[Dict[str, Any]],
    *,
    out_dir: Path,
    voice: str,
    model: str = DEFAULT_TTS_MODEL,
) -> List[Path]:
    """Generate one MP3 per scene. Returns list of created file paths.

    Each file is named voice_scene_<id>.mp3 in the provided out_dir.
    """
    generated: List[Path] = []
    for scene in scenes:
        try:
            sid = int(scene.get("id"))  # type: ignore[arg-type]
        except Exception:
            # If no numeric id, skip
            continue
        narr = scene.get("narration_text")
        if not isinstance(narr, str) or not narr.strip():
            continue
        text = normalize_for_speech(narr)
        dest = out_dir / f"voice_scene_{sid}.mp3"
        synthesize_mp3(text, voice=voice, dest_path=dest, model=model)
        generated.append(dest)
    return generated


__all__ = [
    "OPENAI_VOICES",
    "DEFAULT_TTS_MODEL",
    "ensure_output_dir",
    "normalize_for_speech",
    "generate_scene_voiceovers",
]
