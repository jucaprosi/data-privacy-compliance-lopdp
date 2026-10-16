# ¤roadmap ¤seguridad
"""Motor de consulta de auditoría para la Hoja de Ruta (sala ADPA: Hoja de Ruta)."""
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from features.roadmap.services.contexto_tenant import set_session_context


async def get_roadmap_audit_log(
    session: AsyncSession,
    tenant_id: str,
    roadmap_id: str,
    limit: int = 50,
    offset: int = 0,
) -> Optional[Dict[str, Any]]:
    """Consulta paginada del registro de auditoría de una hoja de ruta.

    Alineado con el aislamiento de tenant y la estructura relacional:
    roadmaps -> roadmap_waves -> roadmap_tasks -> task_audit_log.
    Si el roadmap no existe o no pertenece al tenant, devuelve None (404).
    """
    await set_session_context(session, tenant_id)

    # 1. Verificar existencia y pertenencia del roadmap al tenant
    rm = (
        await session.execute(
            text("SELECT id FROM roadmaps WHERE id = :rid AND tenant_id = :tid"),
            {"rid": roadmap_id, "tid": tenant_id},
        )
    ).mappings().first()

    if not rm:
        return None

    # 2. Conteo total de eventos asociados al roadmap
    count_query = text("""
        SELECT COUNT(*) AS total
        FROM task_audit_log tal
        JOIN roadmap_tasks rt ON tal.task_id = rt.id
        JOIN roadmap_waves rw ON rt.wave_id = rw.id
        WHERE rw.roadmap_id = :rid AND tal.tenant_id = :tid
    """)
    total_result = await session.execute(count_query, {"rid": roadmap_id, "tid": tenant_id})
    total = total_result.scalar() or 0

    # 3. Consulta paginada ordenada cronológicamente de forma descendente
    items_query = text("""
        SELECT
            tal.id,
            tal.task_id,
            tal.action,
            tal.user_id,
            tal.timestamp,
            tal.payload
        FROM task_audit_log tal
        JOIN roadmap_tasks rt ON tal.task_id = rt.id
        JOIN roadmap_waves rw ON rt.wave_id = rw.id
        WHERE rw.roadmap_id = :rid AND tal.tenant_id = :tid
        ORDER BY tal.timestamp DESC, tal.id DESC
        LIMIT :limit OFFSET :offset
    """)
    items_result = await session.execute(
        items_query,
        {
            "rid": roadmap_id,
            "tid": tenant_id,
            "limit": limit,
            "offset": offset,
        },
    )
    items: List[Dict[str, Any]] = [dict(row) for row in items_result.mappings().all()]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items,
    }
