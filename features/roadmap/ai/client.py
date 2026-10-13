# ¤roadmap ¤copiloto-ia
"""Cliente de generación con IA para la sala Roadmap.

Implementa llamadas fiables al LLM (DeepSeek / OpenAI compatible) con:
- Límite de tiempo explícito (timeout configurable, default 60s).
- Detección de salida truncada (finish_reason == 'length').
- Tope de tokens elevado por defecto (8192) para evitar corte de JSON.
- Soporte para cliente inyectable / modelo simulado en pruebas unitarias.
"""
from __future__ import annotations

import os
from typing import Any, Callable, Optional
from openai import OpenAI

from features.roadmap.ai.roadmap_prompts import SYSTEM_PROMPT

DEFAULT_MAX_TOKENS = 8192
DEFAULT_TIMEOUT_SECONDS = 60.0


class TruncatedOutputError(RuntimeError):
    """Se lanza cuando el modelo agota los tokens de salida (finish_reason == 'length')."""
    pass


class LLMTimeoutError(RuntimeError):
    """Se lanza cuando la llamada al LLM supera el tiempo límite configurado."""
    pass


def get_default_client(timeout: float = DEFAULT_TIMEOUT_SECONDS) -> OpenAI:
    """Instancia cliente OpenAI configurado para DeepSeek con timeout explícito."""
    api_key = os.environ.get("DEEPSEEK_API_KEY", "dummy_key")
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    return OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)


def call_roadmap_llm(
    system_prompt: str,
    user_prompt: str,
    *,
    client: Optional[Any] = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = 0.2,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    model: Optional[str] = None,
) -> str:
    """Ejecuta llamada al LLM en modo JSON con control de truncado y timeout.

    Raises:
        TruncatedOutputError: Si finish_reason == 'length'.
        Exception: Ante fallos de red, timeouts o respuesta no válida.
    """
    if client is None:
        client = get_default_client(timeout=timeout)

    model_name = model or os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    kwargs: dict[str, Any] = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }

    try:
        response = client.chat.completions.create(**kwargs)
    except Exception as exc:
        msg = str(exc).lower()
        if "timed out" in msg or "timeout" in msg:
            raise LLMTimeoutError(f"Tiempo límite agotado en llamada al LLM ({timeout}s): {exc}") from exc
        raise

    choice = response.choices[0]
    finish_reason = getattr(choice, "finish_reason", None)

    if finish_reason == "length":
        raise TruncatedOutputError(
            "La respuesta del modelo fue truncada por límite de tokens (finish_reason = 'length')."
        )

    content = choice.message.content or ""
    return content
