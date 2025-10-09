import streamlit as st
from src.workflow import generate_script, generate_caption_options, generate_hashtags_for_caption
from src.video_api import generate_video, extract_final_script
from src.uploaders import upload_to_platforms, SUPPORTED_PLATFORMS
from src.history import list_reels, save_reel_record, create_versioned_folder_and_download

# --- Streamlit UI ---
st.set_page_config(page_title="Reelora.AI", page_icon="📝")
st.title("Reelora.AI - writes, creates, and posts — on repeat.")
st.write("Automatically writes scripts, generates videos, and posts them on social media — all in a continuous, trend-driven loop.")

# Keep the current script across interactions
# Store the primary script payload (now JSON). Name kept generic for compatibility.
if "script_md" not in st.session_state:
    st.session_state["script_md"] = ""
if "latest_video_url" not in st.session_state:
    st.session_state["latest_video_url"] = None
if "latest_title" not in st.session_state:
    st.session_state["latest_title"] = None

"""
Sidebar navigation is handled automatically by Streamlit multipage apps.
We intentionally avoid adding a duplicate custom link to Reel History here.
"""


with st.form("product_script_form"):
    st.subheader("Product Details")
    product_name = st.text_input("Product name", help="What is the product called?")
    product_description = st.text_area("Product description", height=120, help="Short overview, key features, audience, pricing, etc.")
    benefits_input = st.text_area(
        "Product benefits (one per line)",
        value="",
        height=120,
        help="List the top benefits. One benefit per line.",
    )

    st.subheader("Creative Controls")
    tone = st.selectbox(
        "Tone",
        [
            "Friendly",
            "Professional",
            "Inspirational",
            "Humorous",
            "Serious",
            "Casual",
        ],
        index=0,
        help="Select the tone to shape the writing style.",
    )
    primary_language = st.selectbox("Primary language", ["English", "Hindi"], index=0)
    duration_seconds = st.number_input("Target duration (seconds)", min_value=10, max_value=600, value=60, step=5)

    st.subheader("Channels & Formats")
    platforms = st.multiselect(
        "Platforms",
        ["Instagram", "TikTok", "YouTube", "LinkedIn", "Facebook", "Twitter/X"],
        default=["Instagram", "TikTok"],
    )
    aspect_ratios_alts = st.multiselect(
        "Preferred aspect ratios",
        [
            "9:16 (vertical)",
            "4:5 (portrait)",
            "1:1 (square)",
            "16:9 (wide)",
        ],
        default=["9:16 (vertical)", "1:1 (square)"],
    )

    st.subheader("Optional Media Context")
    st.caption("Optionally describe what's visible in a product image to help craft the hook. Uploading an image is optional; analysis text is sufficient.")
    uploaded_img = st.file_uploader("Upload product image (optional)", type=["png", "jpg", "jpeg"], accept_multiple_files=False)
    if uploaded_img is not None:
        st.image(uploaded_img, caption="Uploaded image preview", use_column_width=True)
    product_image_analysis = st.text_area(
        "Image analysis (optional)",
        placeholder="Describe key visual elements, colors, materials, or the scenario depicted.",
        height=100,
    )

    submitted = st.form_submit_button("Generate Script")

if submitted:
    benefits = [b.strip(" \t\r") for b in benefits_input.split("\n") if b.strip()]
    if not product_name.strip():
        st.error("Please enter a product name.")
    elif not product_description.strip() and not benefits:
        st.error("Please provide a product description or at least one benefit.")
    else:
        with st.spinner("🔄 Generating product script & captions..."):
            script = generate_script(
                product_name=product_name.strip(),
                product_description=product_description.strip(),
                product_benefits=benefits,
                product_image_analysis=product_image_analysis.strip() if product_image_analysis else "",
                tone=tone,
                primary_language=primary_language,
                duration_seconds=int(duration_seconds),
                platforms=platforms,
                aspect_ratios_alts=aspect_ratios_alts,
            )
        st.session_state["script_md"] = script  # now expected to be JSON array string
        # Prepare final script and caption options for human selection
        final_script_only = extract_final_script(script)
        st.session_state["final_script_text"] = final_script_only
        with st.spinner("🔄 Drafting caption options..."):
            options = generate_caption_options(
                product_name=product_name.strip(),
                product_benefits=benefits,
                tone=tone,
                primary_language=primary_language,
                final_script=final_script_only,
                num_caption_options=3,
            )
        st.session_state["caption_options"] = options
        # reset prior selections
        st.session_state.pop("selected_caption", None)
        st.session_state.pop("suggested_hashtags", None)
        st.session_state.pop("hashtags_key", None)

# If a script already exists (e.g., after regeneration), show it and the confirmation UI again
if st.session_state.get("script_md"):
    st.subheader("📋 Generated Content")
    # Try to render JSON nicely; fallback to markdown rendering.
    try:
        import json as _json
        _parsed = _json.loads(st.session_state["script_md"])
        st.json(_parsed)
    except Exception:
        st.markdown(st.session_state["script_md"]) 
    st.markdown("---")
    # Human-in-the-loop caption selection
    st.subheader("Choose a caption")
    cap_options = st.session_state.get("caption_options", [])
    # Regenerate options only
    regen_cap_col1, regen_cap_col2 = st.columns([1, 3])
    with regen_cap_col1:
        regen_caps_btn = st.button("Regenerate caption options 🔁", key="regen_caps_only")
    if regen_caps_btn:
        with st.spinner("🔄 Regenerating caption options..."):
            cap_options = generate_caption_options(
                product_name=product_name.strip(),
                product_benefits=[b.strip(" \t\r") for b in benefits_input.split("\n") if b.strip()],
                tone=tone,
                primary_language=primary_language,
                final_script=st.session_state.get("final_script_text", extract_final_script(st.session_state.get("script_md", ""))),
                num_caption_options=3,
            )
        st.session_state["caption_options"] = cap_options
        # reset choice and hashtags suggestions when options change
        st.session_state.pop("caption_choice_idx", None)
        st.session_state.pop("selected_caption", None)
        st.session_state.pop("suggested_hashtags", None)
        st.session_state.pop("hashtags_key", None)
    if not cap_options and st.session_state.get("final_script_text"):
        with st.spinner("🔄 Drafting caption options..."):
            cap_options = generate_caption_options(
                product_name=product_name.strip(),
                product_benefits=[b.strip(" \t\r") for b in benefits_input.split("\n") if b.strip()],
                tone=tone,
                primary_language=primary_language,
                final_script=st.session_state.get("final_script_text", ""),
                num_caption_options=3,
            )
        st.session_state["caption_options"] = cap_options
    if cap_options:
        chosen_idx = st.radio(
            "Select one caption to use",
            list(range(len(cap_options))),
            format_func=lambda i: cap_options[i],
            horizontal=False,
            key="caption_choice_idx",
        )
        selected_caption = cap_options[chosen_idx]
    else:
        selected_caption = f"{product_name} — watch now!"
        st.info("No caption options available yet; using a simple default.")
    st.session_state["selected_caption"] = selected_caption
    st.markdown("---")
    st.subheader("Confirmation")
    st.info("Can I proceed to create the video?")

    col1b, col2b = st.columns(2)
    with col1b:
        proceed_b = st.button("Yes, create the video 🎥", key="proceed_again", type="primary")
    with col2b:
        regenerate_b = st.button("No, regenerate the script 🔁", key="regenerate_again")

    if proceed_b:
        final_script_only = extract_final_script(st.session_state.get("script_md", ""))
        with st.spinner("🎬 Generating video using the confirmed script..."):
            result = generate_video(
                script_text=final_script_only,
                product_name=product_name.strip(),
                platforms=platforms,
                aspect_ratios=aspect_ratios_alts,
                duration_seconds=int(duration_seconds),
            )
        if result.get("status") == "success":
            video_url = result.get("video_url")
            job_id = result.get("job_id")
            msg = result.get("message", "")
            if video_url:
                st.success(f"✅ Video generated! {msg}")
                st.video(video_url)
                st.write(f"Job ID: {job_id}")
                st.write(f"Direct link: {video_url}")
                st.session_state["latest_video_url"] = video_url
                st.session_state["latest_title"] = product_name.strip() or "Reel"
                # Post-video actions will be rendered below based on session state
            else:
                st.info("✅ Video request accepted. The provider may be processing the render.")
                if job_id:
                    st.write(f"Job ID: {job_id}")
                if msg:
                    st.caption(msg)
                # No direct video URL yet, so we cannot upload at this time.
        else:
            st.error(result.get("message", "Failed to generate video."))

    if regenerate_b:
        with st.spinner("🔄 Regenerating product script & captions..."):
            script2 = generate_script(
                product_name=product_name.strip(),
                product_description=product_description.strip(),
                product_benefits=[b.strip(" \t\r") for b in benefits_input.split("\n") if b.strip()],
                product_image_analysis=product_image_analysis.strip() if product_image_analysis else "",
                tone=tone,
                primary_language=primary_language,
                duration_seconds=int(duration_seconds),
                platforms=platforms,
                aspect_ratios_alts=aspect_ratios_alts,
            )
        st.session_state["script_md"] = script2
        # refresh derived state
        fs = extract_final_script(script2)
        st.session_state["final_script_text"] = fs
        with st.spinner("🔄 Drafting caption options..."):
            st.session_state["caption_options"] = generate_caption_options(
                product_name=product_name.strip(),
                product_benefits=[b.strip(" \t\r") for b in benefits_input.split("\n") if b.strip()],
                tone=tone,
                primary_language=primary_language,
                final_script=fs,
                num_caption_options=3,
            )
        st.session_state.pop("selected_caption", None)
        st.session_state.pop("suggested_hashtags", None)
        st.session_state.pop("hashtags_key", None)
        st.success("✅ Script regenerated!")
        st.rerun()

st.markdown("---")
st.caption("Made by Gagan Verma")

# --- Persistent post-video actions (Upload + Save) using session state ---
if st.session_state.get("latest_video_url"):
    st.markdown("---")
    st.subheader("Upload Confirmation")
    st.info("Do you want to upload this video?")

    video_url = st.session_state.get("latest_video_url")
    latest_title = st.session_state.get("latest_title") or "Reel"

    # Upload inputs
    upload_platforms_default = [p for p in SUPPORTED_PLATFORMS]
    chosen_upload_platforms = st.multiselect(
        "Select platforms to upload",
        SUPPORTED_PLATFORMS,
        default=upload_platforms_default,
        key="upload_platforms_selection",
    )

    # Use selected caption and auto-generate hashtags suggestions
    default_caption = st.session_state.get("selected_caption") or f"{latest_title} — watch now!"
    caption_input = st.text_area(
        "Caption",
        value=default_caption,
        help="Choose from options above or edit manually.",
        height=80,
        key="caption_textarea",
    )

    # Suggest hashtags based on current caption and chosen platforms; cache to avoid extra calls
    suggest_key = f"{caption_input}|{','.join(sorted(chosen_upload_platforms))}"
    final_script_only = st.session_state.get("final_script_text", "")
    tone_for_tags = 'Friendly'
    primary_language_for_tags = 'English'
    try:
        tone_for_tags = tone  # from current UI selection if available
        primary_language_for_tags = primary_language
    except Exception:
        pass
    if st.session_state.get("hashtags_key") != suggest_key:
        with st.spinner("🔄 Generating hashtag suggestions..."):
            suggested = generate_hashtags_for_caption(
                selected_caption=caption_input,
                product_name=latest_title,
                platforms=chosen_upload_platforms,
                tone=tone_for_tags,
                primary_language=primary_language_for_tags,
                final_script=final_script_only,
                max_hashtags=10,
            )
        st.session_state["suggested_hashtags"] = suggested
        st.session_state["hashtags_key"] = suggest_key
    hashtags_default = ", ".join(st.session_state.get("suggested_hashtags", []))
    hashtags_input = st.text_input(
        "Hashtags (comma-separated)",
        value=hashtags_default,
        help="Edit or keep the suggested tags. Example: product, startup, ai",
        key="hashtags_input",
    )
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        confirm_upload = st.button("Yes, upload now ⬆️", key="confirm_upload")
    with col_u2:
        skip_upload = st.button("No, skip for now", key="skip_upload")

    if confirm_upload and video_url:
        hashtags = [h.strip().lstrip("#") for h in hashtags_input.split(",") if h.strip()]
        with st.spinner("⬆️ Uploading to selected platforms..."):
            results = upload_to_platforms(video_url, caption_input, hashtags, chosen_upload_platforms)
        any_success = False
        for plat, res in results.items():
            if res.status == "success":
                any_success = True
                st.success(f"{plat}: Uploaded. {res.message}")
                if res.url:
                    st.write(f"Post URL: {res.url}")
            else:
                st.error(f"{plat}: Failed to upload — {res.message}")
        if any_success:
            st.balloons()
    if skip_upload:
        st.info("Upload skipped. You can download or share the video link above.")

    # Save to history section
    st.markdown("---")
    st.subheader("Save to History")
    default_title = st.session_state.get("latest_title") or "Reel"
    save_title = st.text_input("Title for history", value=default_title, key="save_history_title")
    save_locally = st.checkbox("Save a local copy in versioned folder (reels/…)", value=True, key="save_history_local")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        do_save = st.button("Save to history 💾", type="primary", key="save_history_btn")
    with col_s2:
        clear_latest = st.button("Clear current video", key="clear_latest_btn")

    if do_save and video_url:
        file_value = video_url
        if save_locally:
            rel = create_versioned_folder_and_download(save_title, video_url)
            if rel:
                file_value = rel
                st.success(f"Saved locally to {rel}")
            else:
                st.warning("Couldn't save locally; keeping remote link.")
        ok = save_reel_record(title=save_title, file_value=file_value)
        if ok:
            st.success("Saved to history (MongoDB). Open Reel History page from the sidebar.")
        else:
            st.warning("Could not save to database. Check MongoDB configuration.")
    if clear_latest:
        st.session_state["latest_video_url"] = None
        st.session_state["latest_title"] = None
        st.rerun()