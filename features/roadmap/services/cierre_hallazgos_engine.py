# ¤roadmap ¤hallazgos ¤rbac-tenant
"""Cierre y reapertura de hallazgos por el estado de sus tareas (RM-23, R1).

Contrato: governance/especificaciones/RM-23.md §3. Es el cierre por tareas; el cierre por el origen lo hace
`hallazgo_cierre_engine` y este motor no lo deshace: un hallazgo cerrado porque su causa desapareció sigue
cerrado aunque su tarea quede pendiente. Por eso solo reabre lo que cerró él, y lo sabe por `audit_events`.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from features.roadmap.services.contexto_tenant import set_session_context

MOTIVO_TAREAS = "tareas_completadas"

_TAREA_CUMPLIDA = (
    "t.status = 'completada' AND EXISTS (SELECT 1 FROM task_evidence e WHERE e.task_id = t.id "
    "AND e.tenant_id = t.tenant_id AND e.validation_status = 'approved')"
)


async def cerrar_por_tareas(session: AsyncSession, tenant_id: str, user_id: str) -> int:
    """Cierra los hallazgos `en_tratamiento` con todas sus tareas completadas y con evidencia validada."""
    await set_session_context(session, tenant_id, user_id)
    cerrados = (
        await session.execute(
            text(
                "UPDATE hallazgos h SET estado = 'cerrado', actualizado_en = now() "
                "WHERE h.tenant_id = :t AND h.estado = 'en_tratamiento' "
                "AND EXISTS (SELECT 1 FROM roadmap_tasks t WHERE t.hallazgo_id = h.id AND t.tenant_id = h.tenant_id) "
                "AND NOT EXISTS (SELECT 1 FROM roadmap_tasks t WHERE t.hallazgo_id = h.id "
                f"AND t.tenant_id = h.tenant_id AND NOT ({_TAREA_CUMPLIDA})) "
                "RETURNING h.id"
            ),
            {"t": tenant_id},
        )
    ).scalars().all()
    for hallazgo_id in cerrados:
        await registrar_evento(
            session, tenant_id, "hallazgo", hallazgo_id, "cerrado", user_id, {"motivo": MOTIVO_TAREAS}
        )
    return len(cerrados)


async def reabrir_por_tareas(session: AsyncSession, tenant_id: str, user_id: str) -> int:
    """Devuelve a `en_tratamiento` lo que este motor cerró si alguna de sus tareas ya no está completada."""
    await set_session_context(session, tenant_id, user_id)
    reabiertos = (
        await session.execute(
            text(
                "UPDATE hallazgos h SET estado = 'en_tratamiento', actualizado_en = now() "
                "WHERE h.tenant_id = :t AND h.estado = 'cerrado' "
                "AND EXISTS (SELECT 1 FROM roadmap_tasks t WHERE t.hallazgo_id = h.id "
                "AND t.tenant_id = h.tenant_id AND t.status <> 'completada') "
                "AND (SELECT a.payload ->> 'motivo' FROM audit_events a WHERE a.tenant_id = h.tenant_id "
                "AND a.entity_type = 'hallazgo' AND a.entity_id = h.id AND a.action = 'cerrado' "
                "ORDER BY a.timestamp DESC LIMIT 1) = :motivo "
                "RETURNING h.id"
            ),
            {"t": tenant_id, "motivo": MOTIVO_TAREAS},
        )
    ).scalars().all()
    for hallazgo_id in reabiertos:
        await registrar_evento(
            session, tenant_id, "hallazgo", hallazgo_id, "reabierto", user_id, {"motivo": "tarea_reabierta"}
        )
    return len(reabiertos)
