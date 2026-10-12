"""Cambio de estado de tareas con auditoría (sala ADPA: Hoja de Ruta)."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from features.roadmap.domain.models import TaskStatus
from features.roadmap.services.auditoria_engine import registrar_auditoria
from features.roadmap.services.contexto_tenant import set_session_context


def resolve_completed_at(new_status: TaskStatus) -> datetime | None:
    """Regla de negocio: una tarea completada registra su timestamp; otro estado lo limpia.

    Vive en Python (no en SQL) para:
    - Evitar ambigüedad de tipos en la sentencia.
    - Centralizar la regla de negocio fuera de la capa de datos.
    """
    if new_status == TaskStatus.completada:
        return datetime.now(timezone.utc)
    return None


async def update_task_status(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    task_id: str,
    new_status: TaskStatus,
) -> Optional[dict]:
    """Cambia estado de una tarea y registra audit log."""
    await set_session_context(session, tenant_id, user_id)

    completed_at = resolve_completed_at(new_status)

    result = await session.execute(
        text("""
            UPDATE roadmap_tasks
            SET status = :status,
                completed_at = :completed_at
            WHERE id = :id AND tenant_id = :tid
            RETURNING *
        """),
        {
            "status": new_status.value,
            "completed_at": completed_at,
            "id": task_id,
            "tid": tenant_id,
        },
    )
    row = result.mappings().first()
    if not row:
        return None

    await registrar_auditoria(session, tenant_id, user_id, task_id, "status_changed", {"new_status": new_status.value})
    return dict(row)
