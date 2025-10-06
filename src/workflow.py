from typing import TypedDict, List, Any
from langgraph.graph import StateGraph, END

from .groq_client import call_groq_api
from .prompts import (
    outline_prompt,
    script_prompt,
    hashtags_prompt,
    caption_options_prompt,
    hashtags_from_caption_prompt,
)


class ScriptState(TypedDict):
    # Product-centric inputs
    product_name: str
    product_description: str
    product_benefits: List[str]
    product_image_analysis: str  # optional
    tone: str
    primary_language: str
    duration_seconds: int
    platforms: List[str]
    aspect_ratios_alts: List[str]

    # Outputs
    script_outline: str
    final_script: str
    hashtags_and_captions: str
    error: str


def _create_outline_node(state: ScriptState) -> ScriptState:
    try:
        state["script_outline"] = call_groq_api(outline_prompt(state))
    except Exception as e:
        state["error"] = f"Error creating outline: {e}"
    return state


def _generate_script_node(state: ScriptState) -> ScriptState:
    if state.get("error"):
        return state
    try:
        state["final_script"] = call_groq_api(script_prompt(state))
    except Exception as e:
        state["error"] = f"Error generating script: {e}"
    return state


def _generate_hashtags_node(state: ScriptState) -> ScriptState:
    if state.get("error"):
        return state
    try:
        state["hashtags_and_captions"] = call_groq_api(hashtags_prompt(state))
    except Exception as e:
        state["error"] = f"Error generating hashtags: {e}"
    return state


def _compile_workflow():
    g = StateGraph(ScriptState)
    g.add_node("create_outline", _create_outline_node)
    g.add_node("generate_script", _generate_script_node)
    g.add_node("generate_hashtags", _generate_hashtags_node)
    g.set_entry_point("create_outline")
    g.add_edge("create_outline", "generate_script")
    g.add_edge("generate_script", "generate_hashtags")
    g.add_edge("generate_hashtags", END)
    return g.compile()


def generate_script(
    *,
    product_name: str,
    product_description: str,
    product_benefits: List[str],
    product_image_analysis: str,
    tone: str,
    primary_language: str,
    duration_seconds: int,
    platforms: List[str],
    aspect_ratios_alts: List[str],
) -> str:
    app = _compile_workflow()
    initial_state: ScriptState = {
        "product_name": product_name,
        "product_description": product_description,
        "product_benefits": product_benefits,
        "product_image_analysis": product_image_analysis,
    "tone": tone,
        "primary_language": primary_language,
        "duration_seconds": duration_seconds,
        "platforms": platforms,
        "aspect_ratios_alts": aspect_ratios_alts,
        # Outputs
        "script_outline": "",
        "final_script": "",
        "hashtags_and_captions": "",
        "error": "",
    }
    try:
        result = app.invoke(initial_state)
        if result.get("error"):
            return f"❌ {result['error']}"
        response = f"""
## 📝 Script Outline
{result.get('script_outline', 'No outline generated')}

## 🎬 Final Script
{result.get('final_script', 'No script generated')}

## 🏷️ Captions & Hashtags by Platform
{result.get('hashtags_and_captions', 'No captions generated')}
"""
        return response.strip()
    except Exception as e:
        return f"❌ Workflow error: {e}"


# -------- New helper and generators for captions/hashtags (human-in-the-loop) -------- #

def _parse_json_list(text: str) -> List[str]:
    """Attempt to parse a compact JSON array of strings. Fallback: split non-empty lines.

    This makes model outputs resilient: if the LLM returns bullet points or lines,
    we still extract a usable list.
    """
    import json

    if not text:
        return []
    text_stripped = text.strip()
    # Try to find the first '[' and last ']' to extract valid JSON array region
    if "[" in text_stripped and "]" in text_stripped:
        start = text_stripped.find("[")
        end = text_stripped.rfind("]") + 1
        candidate = text_stripped[start:end]
        try:
            arr = json.loads(candidate)
            if isinstance(arr, list):
                return [str(x).strip() for x in arr if str(x).strip()]
        except Exception:
            pass
    # Fallback: split by lines and remove any leading symbols like -, *, #
    lines = [l.strip().lstrip("-*#• ") for l in text_stripped.splitlines()]
    return [l for l in lines if l]


def generate_caption_options(
    *,
    product_name: str,
    product_benefits: List[str],
    tone: str,
    primary_language: str,
    final_script: str,
    num_caption_options: int = 3,
) -> List[str]:
    """Produce multiple caption options tailored to the final script.

    Returns a list of strings (2–6 items typically).
    """
    state: dict[str, Any] = {
        "product_name": product_name,
        "product_benefits": product_benefits,
        "tone": tone,
        "primary_language": primary_language,
        "final_script": final_script,
        "num_caption_options": num_caption_options,
    }
    try:
        raw = call_groq_api(caption_options_prompt(state))
    except Exception as e:
        return [f"Error generating caption options: {e}"]
    options = _parse_json_list(raw)
    # Clamp to 2-6
    if len(options) < 2:
        options = options + [f"{product_name} — learn more."]
    return options[:6]


def generate_hashtags_for_caption(
    *,
    selected_caption: str,
    product_name: str,
    platforms: List[str],
    tone: str,
    primary_language: str,
    final_script: str,
    max_hashtags: int = 10,
) -> List[str]:
    """Generate hashtags from a chosen caption and script context.

    Returns tags WITHOUT leading # suitable for UI; callers can add # if needed.
    """
    state: dict[str, Any] = {
        "selected_caption": selected_caption,
        "product_name": product_name,
        "platforms": platforms,
        "tone": tone,
        "primary_language": primary_language,
        "final_script": final_script,
        "max_hashtags": max_hashtags,
    }
    try:
        raw = call_groq_api(hashtags_from_caption_prompt(state))
    except Exception as e:
        return [f"error_{str(e).replace(' ', '_')[:32].lower()}"]
    tags = _parse_json_list(raw)
    # Clean up: remove leading '#', lower simple duplicates, keep order
    seen = set()
    cleaned: List[str] = []
    for t in tags:
        t2 = t.strip().lstrip('#').replace(' ', '')
        key = t2.lower()
        if t2 and key not in seen:
            seen.add(key)
            cleaned.append(t2)
    if not cleaned:
        return []
    # Limit length
    return cleaned[:max_hashtags]
