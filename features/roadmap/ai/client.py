# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤roadmap ¤copiloto-ia
"""Cliente de generación con IA para la sala Roadmap.

Enruta las llamadas de generación hacia Vertex AI mediante la compuerta única
`app_core.pasillo.inferencia`, con control de tiempo límite y esquema estricto.
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import logging
from typing import Any, Optional

from app_core.pasillo import inferencia as pasillo_inferencia
from features.roadmap.domain.models import RoadmapDocument

logger = logging.getLogger(__name__)

DEFAULT_MAX_TOKENS = 8192
DEFAULT_TIMEOUT_SECONDS = 60.0
MODELO_POR_DEFECTO = pasillo_inferencia.MODELO_GENERACION


class TruncatedOutputError(RuntimeError):
    """Se lanza cuando el modelo agota los tokens de salida (finish_reason == 'length')."""
    pass


class LLMTimeoutError(RuntimeError):
    """Se lanza cuando la llamada al LLM supera el tiempo límite configurado."""
    pass


def _ejecutar_corutina(corutina: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(corutina)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, corutina).result()


def _llamar_cliente_inyectado(
    client: Any,
    system_prompt: str,
    user_prompt: str,
    *,
    model_name: str,
    max_tokens: int,
    temperature: float,
    timeout: float,
) -> str:
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

    return choice.message.content or ""


async def _generar_con_timeout(
    system_prompt: str,
    user_prompt: str,
    *,
    model_name: str,
    org_id: str,
    timeout: float,
) -> RoadmapDocument:
    resultado = await asyncio.wait_for(
        pasillo_inferencia.generar_estructurado(
            system_prompt,
            user_prompt,
            RoadmapDocument,
            modelo=model_name,
            org_id=org_id,
        ),
        timeout=timeout,
    )
    if isinstance(resultado, RoadmapDocument):
        return resultado
    return RoadmapDocument.model_validate(resultado)


def call_roadmap_llm(
    system_prompt: str,
    user_prompt: str,
    *,
    client: Optional[Any] = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = 0.2,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    model: Optional[str] = None,
    org_id: str = "roadmap",
) -> str:
    """Ejecuta llamada estructurada a Vertex AI vía la compuerta de inferencia con timeout explícito."""
    model_name = model or MODELO_POR_DEFECTO
    if client is not None:
        return _llamar_cliente_inyectado(
            client,
            system_prompt,
            user_prompt,
            model_name=model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
        )

    InferenciaNoDisponible, motivo_neutro = pasillo_inferencia.errores()
    if not isinstance(org_id, str) or not org_id.strip():
        raise InferenciaNoDisponible(motivo_neutro)
    if not pasillo_inferencia.estado().disponible:
        raise InferenciaNoDisponible(motivo_neutro)

    try:
        documento = _ejecutar_corutina(
            _generar_con_timeout(
                system_prompt,
                user_prompt,
                model_name=model_name,
                org_id=org_id,
                timeout=timeout,
            )
        )
    except TimeoutError as exc:
        raise LLMTimeoutError(f"Tiempo límite agotado en llamada al LLM ({timeout}s): {exc}") from exc

    return documento.model_dump_json()


async def generar_roadmap_con_traza(
    prompt: Any,
    valores: dict,
    *,
    org_id: str,
    modelo: str = MODELO_POR_DEFECTO,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    esquema: type[Any] = RoadmapDocument,
) -> tuple[Any, Any]:
    """Genera la hoja de ruta con traza auditable (IA-10) usando la compuerta de inferencia."""
    InferenciaNoDisponible, motivo_neutro = pasillo_inferencia.errores()
    if not isinstance(org_id, str) or not org_id.strip():
        raise InferenciaNoDisponible(motivo_neutro)
    if not pasillo_inferencia.estado().disponible:
        raise InferenciaNoDisponible(motivo_neutro)

    try:
        resultado, traza = await asyncio.wait_for(
            pasillo_inferencia.generar_trazado(
                prompt,
                valores,
                esquema,
                modelo=modelo,
                org_id=org_id,
            ),
            timeout=timeout,
        )
        return resultado, traza
    except TimeoutError as exc:
        raise LLMTimeoutError(f"Tiempo límite agotado en llamada al LLM ({timeout}s): {exc}") from exc
