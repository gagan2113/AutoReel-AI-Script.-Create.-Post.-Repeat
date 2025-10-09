"""
Merge per-scene voice-over MP3s with their corresponding scene MP4s and concatenate to final_video.mp4.

Inputs/assumptions:
- scenes.json: Array of scene objects in order. Each has at least: { "id": int, "duration": number or time-string }
- Video files named scene_<id>.mp4 (typically under reels/scene_clips)
- Audio files named voice_scene_<id>.mp3 (directory can be specified or auto-detected)

Usage (defaults align with repo conventions):
    python merge_scenes.py \
      --scenes scenes.json \
      --video-dir reels/scene_clips \
      --audio-dir <folder with voice_scene_*.mp3> \
      --out final_video.mp4

Environment variable fallbacks (optional):
    SCENES_JSON, SCENE_CLIPS_DIR, SCENE_AUDIO_DIR

Notes:
- Requires ffmpeg and ffprobe available on PATH.
- Audio is trimmed to scene duration. Video is cut to scene duration if longer;
  if video is shorter, it is not extended (no freeze-frame). Concatenation uses
  the ffmpeg concat demuxer with stream copy to avoid re-encoding at the final step.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def require_ffmpeg() -> None:
    for exe in ("ffmpeg", "ffprobe"):
        if shutil.which(exe) is None:
            raise RuntimeError(
                f"Required tool '{exe}' not found. Please install FFmpeg and ensure '{exe}' is on PATH."
            )


def parse_duration(value: Any) -> float:
    """Parse a duration from scenes.json.

    Accepts:
    - number (int/float) => seconds
    - string forms like "5", "5.0", "5s", "00:00:05.2" (HH:MM:SS[.ms])
    """
    if value is None:
        raise ValueError("Duration missing in scene entry")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip().lower()
        if s.endswith("s"):
            s = s[:-1]
        # HH:MM:SS(.ms) or MM:SS
        if ":" in s:
            parts = s.split(":")
            if len(parts) == 3:
                hh, mm, ss = parts
            elif len(parts) == 2:
                hh, mm, ss = "0", parts[0], parts[1]
            else:
                raise ValueError(f"Unrecognized duration format: {value}")
            try:
                h = float(hh)
                m = float(mm)
                ssec = float(ss)
                return h * 3600 + m * 60 + ssec
            except Exception as e:
                raise ValueError(f"Invalid time components in duration: {value}") from e
        # plain number string
        try:
            return float(s)
        except Exception as e:
            raise ValueError(f"Unrecognized duration value: {value}") from e
    raise TypeError(f"Unsupported duration type: {type(value)}")


def load_scenes(scenes_path: Path) -> List[Dict[str, Any]]:
    if not scenes_path.exists():
        raise FileNotFoundError(f"Scenes file not found: {scenes_path}")
    try:
        data = json.loads(scenes_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(f"Failed to parse {scenes_path}: {e}") from e
    if not isinstance(data, list):
        raise ValueError("scenes.json must be a JSON array of scene objects")
    # Keep order as provided; filter to dicts only
    scenes = [s for s in data if isinstance(s, dict)]
    return scenes


def detect_latest_audio_dir(reels_root: Path) -> Optional[Path]:
    """Try to find the most recent folder under 'reels' that contains voice_scene_*.mp3 files."""
    if not reels_root.exists():
        return None
    candidates: List[Path] = []
    for child in sorted(reels_root.iterdir(), reverse=True):
        if child.is_dir():
            if any(child.glob("voice_scene_*.mp3")):
                candidates.append(child)
    return candidates[0] if candidates else None


def ensure_even_dimensions_args() -> List[str]:
    """Return a scale filter ensuring even dimensions if needed for H.264.

    We keep it minimal and only enforce even dimensions when necessary by using
    a scale filter that rounds to even. Many clips will already have even sizes.
    """
    return [
        "-vf",
        "scale=trunc(iw/2)*2:trunc(ih/2)*2",
    ]


def run_ffmpeg(args: List[str]) -> None:
    # Execute ffmpeg with provided args; raise on failure with readable error
    proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg failed (exit {proc.returncode}) with output:\n{proc.stdout}")


def probe_duration_seconds(path: Path) -> Optional[float]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True).strip()
        return float(out)
    except Exception:
        return None


def merge_scene(
    scene_id: int,
    video_path: Path,
    audio_path: Path,
    duration_s: float,
    out_path: Path,
) -> None:
    """Mux video with trimmed audio. Video re-encoded to H.264 for later concat.

    - Audio is trimmed to duration with atrim; video is limited with -t <duration>.
    - We do NOT use -shortest, to avoid cutting off video if audio is shorter.
    - Video is re-encoded uniformly to enable concat with -c copy later.
    """
    # Build filter for audio trim
    a_filter = f"atrim=0:{duration_s},asetpts=N/SR/TB"
    args: List[str] = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-i",
        str(audio_path),
        "-filter_complex",
        f"[1:a]{a_filter}[aout]",
        "-map",
        "0:v:0",
        "-map",
        "[aout]",
        # Re-encode video uniformly
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        # Ensure even dimensions for H.264
        *ensure_even_dimensions_args(),
        # Encode audio
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        # Limit total output duration to scene duration
        "-t",
        str(duration_s),
        str(out_path),
    ]
    print(f"Merging scene {scene_id} → {out_path.name} ...")
    run_ffmpeg(args)


def concat_segments(files: List[Path], out_path: Path) -> None:
    # Use concat demuxer with stream copy to avoid re-encoding the final output.
    with tempfile.TemporaryDirectory() as td:
        list_file = Path(td) / "concat_list.txt"
        list_file.write_text("\n".join([f"file '{f.as_posix()}'" for f in files]) + "\n", encoding="utf-8")
        args = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c",
            "copy",
            str(out_path),
        ]
        print(f"Concatenating {len(files)} scene(s) → {out_path} ...")
        run_ffmpeg(args)


def find_audio_dir(audio_dir_arg: Optional[Path], video_dir: Path) -> Path:
    if audio_dir_arg is not None:
        return audio_dir_arg
    # 1) Try video_dir (common case if mp3s placed next to mp4s)
    if any(video_dir.glob("voice_scene_*.mp3")):
        return video_dir
    # 2) Try to auto-detect under reels/<timestamp-*> directories
    reels_root = Path("reels")
    detected = detect_latest_audio_dir(reels_root)
    if detected is not None:
        return detected
    # 3) Fallback to CWD
    return Path.cwd()


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Merge per-scene audio with video and concatenate to a final video.")
    parser.add_argument("--scenes", default=os.getenv("SCENES_JSON", "scenes.json"), help="Path to scenes.json")
    parser.add_argument(
        "--video-dir",
        default=os.getenv("SCENE_CLIPS_DIR", "reels/scene_clips"),
        help="Directory containing scene_<id>.mp4 files",
    )
    parser.add_argument(
        "--audio-dir",
        default=os.getenv("SCENE_AUDIO_DIR", None),
        help="Directory containing voice_scene_<id>.mp3 files (auto-detected if omitted)",
    )
    parser.add_argument("--out", default="final_video.mp4", help="Output final video path")
    args = parser.parse_args(list(argv) if argv is not None else None)

    scenes_path = Path(args.scenes)
    video_dir = Path(args.video_dir)
    audio_dir = Path(args.audio_dir) if args.audio_dir else None
    out_path = Path(args.out)

    require_ffmpeg()
    scenes = load_scenes(scenes_path)

    if not video_dir.exists():
        raise FileNotFoundError(f"Video directory not found: {video_dir}")
    audio_dir = find_audio_dir(audio_dir, video_dir)
    if not audio_dir.exists():
        raise FileNotFoundError(f"Audio directory not found: {audio_dir}")

    # Prepare temp outputs per scene
    tmp_dir = Path(tempfile.mkdtemp(prefix="merged_scenes_"))
    print(f"Using temporary directory: {tmp_dir}")
    merged_files: List[Path] = []

    try:
        for idx, scene in enumerate(scenes, start=1):
            # Read ID & duration
            sid_raw = scene.get("id")
            try:
                sid = int(sid_raw)
            except Exception:
                raise ValueError(f"Scene at position {idx} has non-integer id: {sid_raw}")

            try:
                dur = parse_duration(scene.get("duration"))
            except Exception:
                # Optional fallback: if duration missing, try probing video duration
                candidate_video = video_dir / f"scene_{sid}.mp4"
                vdur = probe_duration_seconds(candidate_video)
                if vdur is None:
                    raise
                dur = vdur

            video_path = video_dir / f"scene_{sid}.mp4"
            audio_path = audio_dir / f"voice_scene_{sid}.mp3"

            if not video_path.exists():
                raise FileNotFoundError(f"Missing video for scene {sid}: {video_path}")
            if not audio_path.exists():
                raise FileNotFoundError(f"Missing audio for scene {sid}: {audio_path}")

            out_seg = tmp_dir / f"merged_scene_{sid}.mp4"
            merge_scene(sid, video_path, audio_path, dur, out_seg)
            merged_files.append(out_seg)

        # Concatenate
        concat_segments(merged_files, out_path)
        print(f"\n✓ Final video written to: {out_path}\n")
        return 0
    finally:
        # Cleanup temp files
        try:
            for f in merged_files:
                if f.exists():
                    f.unlink(missing_ok=True)  # type: ignore[arg-type]
            if tmp_dir.exists():
                tmp_dir.rmdir()
        except Exception:
            # Non-fatal cleanup errors
            pass


if __name__ == "__main__":
    sys.exit(main())
