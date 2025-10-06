from typing import TypedDict, List
from langgraph.graph import StateGraph, END

from .groq_client import call_groq_api
from .prompts import outline_prompt, script_prompt, hashtags_prompt


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
