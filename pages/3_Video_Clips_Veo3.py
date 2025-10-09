from __future__ import annotations

import json
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.veo_api import generate_veo_clip
from src.history import get_reels_dir


st.set_page_config(page_title="Veo 3 Scene Clips", page_icon="🎞️")
st.title("🎞️ Generate Scene Clips with Google Veo 3")
st.caption("Generates per-scene MP4 clips from visual prompts. No audio merge yet.")

load_dotenv()


col_a, col_b = st.columns([2, 1])
with col_a:
    scenes_file = st.text_input("Path to scenes.json", value="scenes.json")
with col_b:
    default_out = (get_reels_dir() / "scene_clips").as_posix()
    out_dir = st.text_input("Output folder", value=default_out)

go = st.button("Generate Clips", type="primary")

if go:
    try:
        scenes_path = Path(scenes_file)
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        if not scenes_path.exists():
            st.error(f"Scenes file not found: {scenes_path}")
        else:
            data = json.loads(scenes_path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                st.error("scenes.json must be a JSON array of objects")
            else:
                created = 0
                for scene in data:
                    if not isinstance(scene, dict):
                        continue
                    sid = scene.get("id")
                    prompt = scene.get("visual_prompt")
                    dur = scene.get("duration")
                    if not isinstance(sid, int) or not isinstance(prompt, str) or not isinstance(dur, int):
                        continue
                    st.write(f"Generating video for scene {sid}...")
                    dest = out_path / f"scene_{sid}.mp4"
                    res = generate_veo_clip(visual_prompt=prompt, duration_seconds=dur, out_path=dest)
                    if res.get("status") == "success":
                        created += 1
                        st.success(f"Scene {sid} saved to {dest.as_posix()}")
                        st.video(str(dest))
                    else:
                        st.error(f"Scene {sid} failed: {res.get('message')}")
                if created:
                    st.balloons()
    except Exception as e:
        st.error(f"Failed to generate clips: {e}")
