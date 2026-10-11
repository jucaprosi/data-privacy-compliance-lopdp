"""Encolado de la generación de hojas de ruta y estado del job (sala ADPA: Hoja de Ruta)."""
from typing import Optional
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from features.roadmap.domain.models import GenerateRoadmapRequest
from features.roadmap.services.contexto_tenant import set_session_context


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
