import streamlit as st
from src.history import list_reels, save_reel_record, create_versioned_folder_and_download


st.set_page_config(page_title="Reel History — AutoReel AI", page_icon="📜")
st.title("📜 Reel History")
st.caption("Browse, preview, and save your generated reels. You can also add a record manually.")


# --- Add new entry manually ---
with st.expander("Add a reel to history", expanded=False):
    with st.form("add_reel_form"):
        title = st.text_input("Title", placeholder="e.g., iPhone Case Launch Reel")
        video_url = st.text_input("Video URL", placeholder="https://...")
        save_local = st.checkbox("Also download and keep a local copy (reels/…)", value=True)
        submitted = st.form_submit_button("Save")
    if submitted:
        if not title.strip():
            st.error("Please provide a title.")
        elif not video_url.strip():
            st.error("Please provide a video URL.")
        else:
            file_value = video_url.strip()
            if save_local:
                with st.spinner("Downloading video to versioned folder…"):
                    rel = create_versioned_folder_and_download(title.strip(), video_url.strip())
                if rel:
                    file_value = rel
                    st.success(f"Saved local copy to {rel}")
                else:
                    st.warning("Couldn't save locally; keeping remote link.")
            ok = save_reel_record(title=title.strip(), file_value=file_value)
            if ok:
                st.success("Saved to history.")
                st.rerun()
            else:
                st.warning("Could not save to database. Configure MongoDB to enable history.")


st.markdown("---")
st.subheader("Recent reels")
refresh = st.button("Refresh", use_container_width=False)
if refresh:
    st.rerun()

reels = list_reels(limit=100)
if not reels:
    st.info("No history found. Ensure MongoDB is configured via environment variables.")
else:
    for r in reels:
        title = r.get("title", "Untitled")
        date = r.get("date", "")
        file_val = r.get("file")
        with st.container(border=True):
            st.markdown(f"**{title}**  ")
            if date:
                st.caption(date)
            if file_val:
                # Try to preview as video
                try:
                    st.video(file_val)
                except Exception:
                    st.write(file_val)
                # Provide a download button if local file exists
                if not str(file_val).startswith("http"):
                    try:
                        with open(file_val, "rb") as fh:
                            fname = str(file_val).split("/")[-1]
                            st.download_button("Download", data=fh, file_name=fname, use_container_width=False)
                    except Exception:
                        st.caption("Local file not available.")
                else:
                    st.markdown(f"[Open link]({file_val})")
