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
    """Tareas `completada` con al menos una evidencia con doble validación (RM-25b).

    Cuenta la evidencia aprobada cuya primera validación hizo un `coordinador` y cuya validación final hizo un
    `dpo` o un `auditor`, sin la marca `requiere_revalidacion`. Los roles son los guardados en la fila al
    validar, no los que la persona tenga hoy. Una evidencia con una sola validación no cuenta.

    Devuelve `tarea_id`, `control_ref` ("P12"), `cerrada_en` y `nivel_acreditado` (el mayor de sus evidencias
    con doble validación, o None si ninguna lo trae), por tarea.
    """
    await fijar_contexto_rls(session, tenant_id, user_id)
    filas = await session.execute(
        text(
            "SELECT t.id AS tarea_id, t.control_ref AS control_ref, t.completed_at AS cerrada_en, "
            "MAX(e.nivel_acreditado) AS nivel_acreditado "
            "FROM roadmap_tasks t JOIN task_evidence e ON e.task_id = t.id AND e.tenant_id = t.tenant_id "
            "WHERE t.tenant_id = :t AND t.status = 'completada' "
            "AND e.validation_status = 'approved' AND e.validated_by IS NOT NULL "
            "AND e.uploaded_by IS NOT NULL AND e.validated_by <> e.uploaded_by "
            "AND e.primera_validacion_rol = 'coordinador' AND e.validado_rol IN ('dpo', 'auditor') "
            "AND NOT e.requiere_revalidacion "
            "GROUP BY t.id, t.control_ref, t.completed_at "
            "ORDER BY t.control_ref, t.id"
        ),
        {"t": tenant_id},
    )
    return [dict(f) for f in filas.mappings().all()]
