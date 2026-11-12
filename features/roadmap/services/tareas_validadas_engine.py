# ¤roadmap ¤diagnostico-estados
"""Lectura de las tareas cerradas con evidencia validada (DIAG-12), para los estados del diagnóstico.

La Hoja de Ruta es la dueña de `roadmap_tasks` y `task_evidence`: otras salas la leen por su compuerta y su
pasillo, nunca de sus tablas.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import fijar_contexto_rls


async def tareas_cerradas_con_evidencia_validada(session: AsyncSession, tenant_id: str, user_id: str) -> list[dict]:
    """Tareas `completada` con al menos una evidencia aprobada por el DPO, distinto de quien la subió.

    El rol es el vigente en la organización, no el que tenía al validar. `task_evidence` no guarda la primera
    validación del coordinador, así que hoy no se comprueba (queda como ficha aparte de roadmap).

    Cuatro ojos (INV_LOPDP_FOUR_EYES_CLOSURE): una tarea sin evidencia aprobada, o cuya evidencia aprobó
    quien la subió, no cuenta. Devuelve `tarea_id`, `control_ref` ("P12") y `cerrada_en`, por tarea.
    """
    await fijar_contexto_rls(session, tenant_id, user_id)
    filas = await session.execute(
        text(
            "SELECT t.id AS tarea_id, t.control_ref AS control_ref, t.completed_at AS cerrada_en "
            "FROM roadmap_tasks t "
            "WHERE t.tenant_id = :t AND t.status = 'completada' AND EXISTS ("
            "  SELECT 1 FROM task_evidence e WHERE e.task_id = t.id AND e.tenant_id = :t "
            "  AND e.validation_status = 'approved' AND e.validated_by IS NOT NULL "
            "  AND e.uploaded_by IS NOT NULL AND e.validated_by <> e.uploaded_by "
            "  AND EXISTS (SELECT 1 FROM user_tenant_roles r WHERE r.user_id = e.validated_by "
            "  AND r.tenant_id = :t AND r.role = 'dpo')) "
            "ORDER BY t.control_ref, t.id"
        ),
        {"t": tenant_id},
    )
    return [dict(f) for f in filas.mappings().all()]
