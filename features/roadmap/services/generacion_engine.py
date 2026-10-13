# ¤roadmap ¤copiloto-ia
"""Motor de generación con IA de hojas de ruta (sala ADPA: Hoja de Ruta).

Implementa:
1. Encolado asíncrono en Redis (enqueue_generation).
2. Generación fiable con IA (generate_roadmap_document):
   - Inclusión obligatoria del esquema de RoadmapDocument en el prompt.
   - Detección de salida truncada (finish_reason = 'length').
   - Reintento correctivo enviando el esquema y el error específico de validación de Pydantic.
   - Límite de tiempo explícito en la llamada.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Callable, Optional
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from features.roadmap.ai.client import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_TIMEOUT_SECONDS,
    TruncatedOutputError,
    call_roadmap_llm,
)
from features.roadmap.ai.roadmap_prompts import (
    SYSTEM_PROMPT,
    build_roadmap_prompt,
    get_roadmap_schema_str,
)
from features.roadmap.domain.models import GenerateRoadmapRequest, RoadmapDocument
from features.roadmap.services.contexto_tenant import set_session_context

logger = logging.getLogger(__name__)


class GeneracionRoadmapError(Exception):
    """Fallo en el proceso de generación con IA."""
    pass


def generate_roadmap_document(
    assessment: dict,
    variables: dict,
    roadmap_id: str,
    tenant_id: str,
    *,
    llm_caller: Optional[Callable[[str, str], str]] = None,
    max_retries: int = 2,
) -> RoadmapDocument:
    """Genera y valida un RoadmapDocument utilizando IA y reintentos correctivos.

    Si la respuesta es inválida sintáctica o esquemáticamente, reintenta enviando
    el error exacto y el esquema para que el modelo corrija su salida.
    """
    initial_user_prompt = build_roadmap_prompt(assessment, variables)
    current_user_prompt = initial_user_prompt
    last_error: Optional[Exception] = None

    for intento in range(max_retries):
        try:
            if llm_caller is not None:
                raw_response = llm_caller(SYSTEM_PROMPT, current_user_prompt)
            else:
                raw_response = call_roadmap_llm(
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=current_user_prompt,
                    max_tokens=DEFAULT_MAX_TOKENS,
                    timeout=DEFAULT_TIMEOUT_SECONDS,
                )

            data = json.loads(raw_response)
            data["roadmap_id"] = roadmap_id
            data["tenant_id"] = tenant_id

            doc = RoadmapDocument.model_validate(data)
            return doc

        except TruncatedOutputError as exc:
            logger.warning(
                "Intento %d de generación de roadmap truncado por tokens: %s",
                intento + 1,
                exc,
            )
            last_error = exc
            # Reintento solicitando concisión para evitar corte
            current_user_prompt = (
                initial_user_prompt
                + f"\n\nERROR PREVIO: La respuesta anterior fue truncada por límite de longitud."
                + f"\nPor favor genera un documento conciso manteniendo las olas prioritarias y cumpliendo estrictamente el esquema:\n{get_roadmap_schema_str()}"
            )

        except (json.JSONDecodeError, ValidationError, Exception) as exc:
            logger.warning(
                "Intento %d de generación de roadmap falló con error: %s",
                intento + 1,
                exc,
            )
            last_error = exc
            # Reintento correctivo con esquema y detalle del error
            error_msg = str(exc)
            current_user_prompt = (
                initial_user_prompt
                + f"\n\nCORRECCIÓN REQUERIDA (Intento previo fallido):"
                + f"\nLa salida anterior NO cumplió con las especificaciones y produjo el siguiente error:"
                + f"\n{error_msg}"
                + f"\n\nAsegúrate de devolver ÚNICAMENTE un JSON válido que cumpla estrictamente este esquema:\n{get_roadmap_schema_str()}"
            )

    raise GeneracionRoadmapError(
        f"No se pudo generar un RoadmapDocument válido tras {max_retries} intentos. Último error: {last_error}"
    )


async def enqueue_generation(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    request: GenerateRoadmapRequest,
) -> str:
    """Persiste roadmap draft y encola job en Redis. Devuelve job_id."""
    from app_core.queue.redis_client import enqueue_job

    await set_session_context(session, tenant_id, user_id)

    roadmap_id = str(uuid4())
    job_id = str(uuid4())

    await session.execute(
        text("""
            INSERT INTO roadmaps (id, tenant_id, status, variables_json, summary)
            VALUES (:id, :tenant_id, 'draft', CAST(:vars AS JSON), :summary)
        """),
        {
            "id": roadmap_id,
            "tenant_id": tenant_id,
            "vars": request.variables.model_dump_json(),
            "summary": "Roadmap en generación",
        },
    )

    payload = {
        "job_id": job_id,
        "roadmap_id": roadmap_id,
        "tenant_id": tenant_id,
        "user_id": user_id,
        "variables": request.variables.model_dump(),
        "assessment": request.assessment,
    }
    enqueue_job(payload)
    return job_id


async def get_job(job_id: str) -> Optional[dict]:
    """Estado del job desde Redis."""
    from app_core.queue.redis_client import get_job_status
    return get_job_status(job_id)
