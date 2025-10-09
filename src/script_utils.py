from __future__ import annotations

import json


def extract_final_script(text: str) -> str:
    """
    Extract a usable narration script from the app output.

    - If the input is a JSON array of scene objects with "narration_text",
      join those lines into a single script (one per scene).
    - Otherwise, fall back to extracting the content under the legacy
      "## Final Script" markdown header.
    - If neither format matches, return the raw input.
    """
    if not text:
        return ""

    s = text.strip()
    # Try JSON scenes first
    if s.startswith("["):
        try:
            data = json.loads(s)
            if isinstance(data, list) and all(isinstance(x, dict) for x in data):
                narr_lines: list[str] = []
                for scene in data:
                    nt = scene.get("narration_text") if isinstance(scene, dict) else None  # type: ignore[attr-defined]
                    if isinstance(nt, str) and nt.strip():
                        narr_lines.append(nt.strip())
                if narr_lines:
                    return "\n".join(narr_lines)
        except Exception:
            pass

    # Legacy markdown fallback
    lines = s.splitlines()
    collecting = False
    buf: list[str] = []
    for line in lines:
        if line.strip().lower().startswith("##") and "final script" in line.strip().lower():
            collecting = True
            continue
        if collecting and line.strip().startswith("## "):
            break
        if collecting:
            buf.append(line)
    text2 = "\n".join(buf).strip()
    return text2 if text2 else s


__all__ = ["extract_final_script"]
