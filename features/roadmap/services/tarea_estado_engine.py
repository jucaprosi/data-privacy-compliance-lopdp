# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"""Cambio de estado de tareas con auditoría (sala ADPA: Hoja de Ruta)."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.errors import CodigoErrorNegocio, ErrorNegocio
from features.roadmap.domain.models import TaskStatus
from features.roadmap.services.auditoria_engine import registrar_auditoria
from features.roadmap.services.cierre_verificado_engine import exigir_cierre_conforme
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


RM_CIERRE_SIN_DOBLE_VALIDACION = CodigoErrorNegocio(
    codigo="RM_CIERRE_SIN_DOBLE_VALIDACION",
    status_code=409,
    mensaje_defecto=(
        "La tarea no puede completarse: falta evidencia validada por el coordinador y por el DPO o el auditor, "
        "con nivel E1 o mayor."
    ),
    action_required=None,
)

NIVEL_ACREDITADO_MINIMO_CIERRE = 1  # E1


async def _exigir_doble_validacion(session: AsyncSession, tenant_id: str, task_id: str) -> None:
    """RM-28 R1 (¤roadmap): cuatro ojos antes de completar, con los filtros de RM-25b más el nivel E1.

    Corre en la sesión de la petición, con su contexto RLS ya fijado.
    """
    hay = await session.execute(
        text(
            "SELECT EXISTS (SELECT 1 FROM task_evidence e "
            "WHERE e.task_id = :id AND e.tenant_id = :tid "
            "AND e.validation_status = 'approved' AND e.validated_by IS NOT NULL "
            "AND e.uploaded_by IS NOT NULL AND e.validated_by <> e.uploaded_by "
            "AND e.primera_validacion_rol = 'coordinador' AND e.validado_rol IN ('dpo', 'auditor') "
            "AND NOT e.requiere_revalidacion "
            "AND e.nivel_acreditado >= :nivel)"
        ),
        {"id": task_id, "tid": tenant_id, "nivel": NIVEL_ACREDITADO_MINIMO_CIERRE},
    )
    if not hay.scalar():
        raise ErrorNegocio(RM_CIERRE_SIN_DOBLE_VALIDACION)


async def update_task_status(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    task_id: str,
    new_status: TaskStatus,
) -> Optional[dict]:
    """Cambia estado de una tarea y registra audit log."""
    await set_session_context(session, tenant_id, user_id)

    if new_status == TaskStatus.completada:
        await _exigir_doble_validacion(session, tenant_id, task_id)
        exigir_cierre_conforme(tenant_id, task_id)

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
