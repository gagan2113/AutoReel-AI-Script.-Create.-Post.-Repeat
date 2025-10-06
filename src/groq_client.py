import os
from typing import List, Dict, Any
import json
import logging
import requests
from requests.exceptions import RequestException
from dotenv import load_dotenv

load_dotenv()

GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_DEBUG = os.getenv("GROQ_DEBUG", "0") in {"1", "true", "True", "YES", "yes"}
GROQ_TIMEOUT = float(os.getenv("GROQ_TIMEOUT", "60"))


class GroqClient:
    """Minimal Groq Chat Completions client with clear diagnostics on failure."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None):
        self.api_key = api_key or GROQ_API_KEY
        self.base_url = base_url or GROQ_API_URL
        self.model = model or GROQ_MODEL
        self.timeout = GROQ_TIMEOUT
        self.debug = GROQ_DEBUG
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set. Add it to your .env file or env vars.")

    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 1024, temperature: float = 0.8) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if self.debug:
            logging.warning(
                "[GROQ DEBUG] POST %s model=%s, messages=%d, max_tokens=%d, temperature=%s",
                self.base_url,
                self.model,
                len(messages),
                max_tokens,
                temperature,
            )
        try:
            resp = requests.post(self.base_url, headers=headers, json=data, timeout=self.timeout)
        except RequestException as e:
            raise RuntimeError(f"Groq API request failed to send: {e}") from e

        if self.debug:
            logging.warning("[GROQ DEBUG] HTTP %s", resp.status_code)

        # Handle non-2xx with as much detail as possible
        if not resp.ok:
            content_type = resp.headers.get("content-type", "")
            body_text = resp.text
            err_detail = body_text
            if "application/json" in content_type:
                try:
                    err_json = resp.json()
                    err_detail = json.dumps(err_json, ensure_ascii=False)
                except Exception:
                    pass
            raise RuntimeError(
                "Groq API error: "
                f"status={resp.status_code}, url={self.base_url}, model={self.model}, "
                f"detail={err_detail[:2000]}"
            )

        try:
            j = resp.json()
        except ValueError as e:
            raise RuntimeError(f"Groq API returned non-JSON response: status={resp.status_code}, body={resp.text[:2000]}") from e

        try:
            content = j["choices"][0]["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"Unexpected Groq response schema: {json.dumps(j)[:2000]}") from e
        return (content or "").strip()


def call_groq_api(prompt: str, system: str = "You are a helpful assistant.") -> str:
    client = GroqClient()
    return client.chat([
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ])
