from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

from src.veo_api import generate_veo_clip


def main():
    load_dotenv()

    # Inputs
    scenes_path = Path(os.getenv("SCENES_JSON", "scenes.json"))
    out_dir = Path(os.getenv("SCENE_CLIPS_DIR", "reels/scene_clips"))
    out_dir.mkdir(parents=True, exist_ok=True)

    if not scenes_path.exists():
        print(f"Scenes file not found: {scenes_path}")
        raise SystemExit(1)

    try:
        data = json.loads(scenes_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Failed to parse {scenes_path}: {e}")
        raise SystemExit(1)

    if not isinstance(data, list):
        print("scenes.json must be a JSON array of scene objects")
        raise SystemExit(1)

    scenes: List[Dict[str, Any]] = [s for s in data if isinstance(s, dict)]
    for scene in scenes:
        try:
            sid = int(scene.get("id"))
        except Exception:
            continue
        prompt = scene.get("visual_prompt")
        dur = scene.get("duration")
        if not isinstance(prompt, str) or not prompt.strip():
            continue
        if not isinstance(dur, int) or dur <= 0:
            continue
        print(f"Generating video for scene {sid}...")
        dest = out_dir / f"scene_{sid}.mp4"
        res = generate_veo_clip(visual_prompt=prompt, duration_seconds=dur, out_path=dest)
        if res.get("status") == "success":
            print(f"✓ Scene {sid} saved to {dest}")
        else:
            print(f"✗ Scene {sid} failed: {res.get('message')}")


if __name__ == "__main__":
    main()
