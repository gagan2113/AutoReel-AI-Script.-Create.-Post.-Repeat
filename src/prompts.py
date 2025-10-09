from typing import Mapping, Sequence

ALLOWED_TONES: Sequence[str] = (
    "Friendly",
    "Professional",
    "Inspirational",
    "Humorous",
    "Serious",
    "Casual",
)


def outline_prompt(state: Mapping[str, object]) -> str:
    product_name = state.get("product_name", "")
    product_description = state.get("product_description", "")
    product_benefits: Sequence[str] = state.get("product_benefits", []) or []
    # Prefer new `tone`; fall back to legacy `brand_voice` if present
    raw_tone = (state.get("tone") or state.get("brand_voice") or "").strip()  # type: ignore[arg-type]
    tone = raw_tone.title() if isinstance(raw_tone, str) else ""
    if tone not in ALLOWED_TONES:
        tone = "Friendly"
    primary_language = state.get("primary_language", "English")
    duration_seconds = state.get("duration_seconds", 60)
    platforms: Sequence[str] = state.get("platforms", []) or []
    aspect_ratios: Sequence[str] = state.get("aspect_ratios_alts", []) or []
    image_analysis = state.get("product_image_analysis", "")

    benefits_str = "\n- ".join([b for b in product_benefits if b])
    platforms_str = ", ".join(platforms) if platforms else "Generic Social"
    ratios_str = ", ".join(aspect_ratios) if aspect_ratios else "Any"

    return f"""
You are a senior social media creative director.
Create a detailed outline for a {duration_seconds}-second product video script in {primary_language}.

Product: {product_name}
Description: {product_description}
Benefits:
- {benefits_str if benefits_str else 'N/A'}
Tone: {tone}
Target platforms: {platforms_str}
Preferred aspect ratios: {ratios_str}
Optional image analysis (if provided): {image_analysis if image_analysis else 'N/A'}

Provide a structured outline with:
1) Scroll-stopping hook (first 3-5 seconds)
2) Demonstration or value points mapping to the benefits
3) Social proof or objection handling
4) Clear CTA adapted to the platforms

Notes:
- Tailor the pacing to {duration_seconds}s.
- If image analysis is present, weave visual references into the hook.
- Tone: {tone} (Allowed: {", ".join(ALLOWED_TONES)})
- Keep language aligned with the selected tone throughout.
"""


def script_prompt(state: Mapping[str, object]) -> str:
    product_name = state.get("product_name", "")
    # Prefer new `tone`; fall back to legacy `brand_voice` if present
    raw_tone = (state.get("tone") or state.get("brand_voice") or "").strip()  # type: ignore[arg-type]
    tone = raw_tone.title() if isinstance(raw_tone, str) else ""
    if tone not in ALLOWED_TONES:
        tone = "Friendly"
    primary_language = state.get("primary_language", "English")
    duration_seconds = state.get("duration_seconds", 60)
    platforms: Sequence[str] = state.get("platforms", []) or []
    platforms_str = ", ".join(platforms) if platforms else "Generic Social"
    outline = state.get("script_outline", "")

    return f"""
You are a senior short-form video scriptwriter.
Convert the following outline into a scene-by-scene script in {primary_language}.

Outline:
{outline}

Output format: STRICT JSON array (no backticks, no prose), where each scene is an object with exactly these fields:
- "id": scene number starting at 1
- "duration": integer duration in seconds
- "visual_prompt": short description of visuals for the scene (concise; 8–14 words)
- "narration_text": text for the voiceover

Constraints:
- Total speaking duration should be close to {duration_seconds} seconds.
- Tone: {tone} (Allowed: {", ".join(ALLOWED_TONES)})
- Target platforms: {platforms_str}
- Keep narration tight and natural; avoid filler and long asides.
- visual_prompt must not include camera jargon; describe what the viewer sees.
- Do NOT include any keys beyond the four specified; do NOT include comments.

Example of the required shape (values are illustrative only):
[
    {{"id": 1, "duration": 4, "visual_prompt": "Close-up of product on clean desk", "narration_text": "Meet ProductName—your daily boost."}},
    {{"id": 2, "duration": 7, "visual_prompt": "Hand uses product; overlay highlights key benefit", "narration_text": "It saves you time with one tap."}}
]
"""


def hashtags_prompt(state: Mapping[str, object]) -> str:
    # Prefer new `tone`; fall back to legacy `brand_voice` if present
    raw_tone = (state.get("tone") or state.get("brand_voice") or "").strip()  # type: ignore[arg-type]
    tone = raw_tone.title() if isinstance(raw_tone, str) else ""
    if tone not in ALLOWED_TONES:
        tone = "Friendly"
    primary_language = state.get("primary_language", "English")
    platforms: Sequence[str] = state.get("platforms", []) or []
    platforms_str = ", ".join(platforms) if platforms else "Generic Social"
    product_name = state.get("product_name", "")
    benefits: Sequence[str] = state.get("product_benefits", []) or []
    script = state.get("final_script", "")

    benefits_inline = ", ".join([b for b in benefits if b])

    return f"""
You are a social media strategist. Create platform-ready captions and hashtags in {primary_language}.

Target platforms: {platforms_str}
Product: {product_name}
Key benefits: {benefits_inline}

Script context:
{script}

Output format:
For each platform, provide:
- Caption (1–2 lines, with a strong CTA)
- 8–10 relevant, high-intent hashtags (avoid banned terms, mix broad + niche)

Keep captions succinct, benefit-driven, and aligned with the platform culture.
Maintain an overall tone of "{tone}" consistently.
"""


def caption_options_prompt(state: Mapping[str, object]) -> str:
    # Prefer new `tone`; fall back to legacy `brand_voice` if present
    raw_tone = (state.get("tone") or state.get("brand_voice") or "").strip()  # type: ignore[arg-type]
    tone = raw_tone.title() if isinstance(raw_tone, str) else ""
    if tone not in ALLOWED_TONES:
        tone = "Friendly"
    primary_language = state.get("primary_language", "English")
    product_name = state.get("product_name", "")
    benefits: Sequence[str] = state.get("product_benefits", []) or []
    script = state.get("final_script", "")
    num_options = int(state.get("num_caption_options", 3) or 3)
    if num_options < 2:
        num_options = 2
    if num_options > 6:
        num_options = 6

    benefits_inline = ", ".join([b for b in benefits if b])

    return f"""
You are an expert social copywriter.
Propose {num_options} distinct caption options in {primary_language} for the content below.

Product: {product_name}
Key benefits: {benefits_inline}

Script context:
{script}

Constraints:
- 1–2 lines each, strong hook and clear CTA.
- Vary style within the same overall tone "{tone}".
- Avoid emojis unless they truly add clarity.

Output STRICTLY as compact JSON array of strings. Example:
["Option 1", "Option 2", "Option 3"]
"""


def hashtags_from_caption_prompt(state: Mapping[str, object]) -> str:
    # Prefer new `tone`; fall back to legacy `brand_voice` if present
    raw_tone = (state.get("tone") or state.get("brand_voice") or "").strip()  # type: ignore[arg-type]
    tone = raw_tone.title() if isinstance(raw_tone, str) else ""
    if tone not in ALLOWED_TONES:
        tone = "Friendly"
    primary_language = state.get("primary_language", "English")
    platforms: Sequence[str] = state.get("platforms", []) or []
    platforms_str = ", ".join(platforms) if platforms else "Generic Social"
    product_name = state.get("product_name", "")
    selected_caption = state.get("selected_caption", "")
    script = state.get("final_script", "")
    max_tags = int(state.get("max_hashtags", 10) or 10)
    if max_tags < 3:
        max_tags = 3
    if max_tags > 15:
        max_tags = 15

    return f"""
You are a social media strategist. Generate a concise set of hashtags in {primary_language}.

Platforms: {platforms_str}
Product: {product_name}
Tone: {tone}

Chosen Caption:
{selected_caption}

Script context:
{script}

Instructions:
- Return between {max_tags-2} and {max_tags} hashtags.
- High-intent, relevant; avoid banned terms.
- Mix broad + niche; prefer camelCase where helpful.
- Exclude the leading # symbols in output.

Output STRICTLY as a compact JSON array of strings, e.g. ["tagOne", "tagTwo", "tagThree"].
"""
