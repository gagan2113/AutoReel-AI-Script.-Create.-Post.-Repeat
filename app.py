import streamlit as st
from src.workflow import generate_script

# --- Streamlit UI ---
st.set_page_config(page_title="AI Product Script Generator", page_icon="📝")
st.title("AI Product Script Generator")
st.write("Produce platform-ready scripts and captions tailored to your product, tone, and target formats.")


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

        st.subheader("📋 Generated Content")
        st.markdown(script)
        st.success("✅ Script generated! Copy and use it across your channels.")

st.markdown("---")
st.caption("Made by Gagan Verma")