# ¤roadmap ¤hallazgos ¤rbac-tenant
"""Cierre de un hallazgo por la sala que lo produjo (CAPA-02, R1).

Es el cierre por el origen: el hecho que causó el hallazgo dejó de existir (el control vencido se verificó).
El cierre por tareas completadas es de RM-23 y va en su propio motor.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from features.roadmap.services.contexto_tenant import set_session_context


async def cerrar_hallazgo(session: AsyncSession, tenant_id: str, user_id: str, hallazgo_id: str) -> bool:
    """Pasa el hallazgo a `cerrado`; devuelve False si no existe en la organización o ya lo estaba."""
    await set_session_context(session, tenant_id, user_id)
    cerrado = (
        await session.execute(
            text(
                "UPDATE hallazgos SET estado = 'cerrado', actualizado_en = now() "
                "WHERE id = :h AND tenant_id = :t AND estado <> 'cerrado' RETURNING id"
            ),
            {"h": hallazgo_id, "t": tenant_id},
        )
    ).scalar()
    if cerrado is None:
        return False
    await registrar_evento(session, tenant_id, "hallazgo", hallazgo_id, "cerrado", user_id, {"motivo": "origen_resuelto"})
    return True


# === RAT-05 ===
async def reabrir_hallazgo(session: AsyncSession, tenant_id: str, user_id: str, hallazgo_id: str) -> bool:
    """El hecho volvió a ocurrir: un hallazgo cerrado recupera su estado, `en_tratamiento` si ya tiene tarea."""
    await set_session_context(session, tenant_id, user_id)
    reabierto = (
        await session.execute(
            text(
                "UPDATE hallazgos h SET actualizado_en = now(), estado = CASE WHEN EXISTS ("
                "SELECT 1 FROM roadmap_tasks t WHERE t.hallazgo_id = h.id AND t.tenant_id = h.tenant_id"
                ") THEN 'en_tratamiento' ELSE 'abierto' END "
                "WHERE h.id = :h AND h.tenant_id = :t AND h.estado = 'cerrado' RETURNING h.id"
            ),
            {"h": hallazgo_id, "t": tenant_id},
        )
    ).scalar()
    if reabierto is None:
        return False
    await registrar_evento(session, tenant_id, "hallazgo", hallazgo_id, "reabierto", user_id, {"motivo": "origen_reincidente"})
    return True
# === fin RAT-05 ===
