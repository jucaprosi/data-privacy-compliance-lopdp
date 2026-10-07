"""Cliente DeepSeek. Compatible con SDK openai.

- Modelo por defecto: deepseek-chat.
- JSON mode forzado cuando se solicita.
"""
import os
from typing import Any

from openai import OpenAI

_client = None


def get_client() -> OpenAI:
    """Devuelve un cliente OpenAI apuntando a DeepSeek (singleton)."""
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.environ["DEEPSEEK_API_KEY"],
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        )
    return _client


def call_llm(
    system: str,
    user: str,
    json_mode: bool = True,
    max_tokens: int = 4096,
    temperature: float = 0.2,
) -> str:
    """Llama al LLM y devuelve el contenido string.

    Si json_mode=True, fuerza response_format=json_object.
    """
    client = get_client()
    kwargs: dict[str, Any] = {
        "model": os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content or ""
