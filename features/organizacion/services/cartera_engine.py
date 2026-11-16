# ¤adpa
# ¤cartera ¤rbac-tenant
"""Cartera de organizaciones por pertenencia (ORG-15, `INV_LOPDP_PORTFOLIO_BY_MEMBERSHIP`).

El origen único de la lista es `mis_organizaciones` (ORG-13): solo organizaciones con rol vigente de
la persona. Por cada una se consultan sus indicadores en su propia transacción, con el contexto RLS de
esa organización y nunca con una consulta que cruce organizaciones. Cada fila lleva las dimensiones por
separado y contadores: ni promedio, ni puntaje, ni datos personales (D-1, `INV_LOPDP_MULTIDIMENSIONAL_METRICS`).
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import fijar_contexto_rls
from app_core.pasillo import diagnostico as pasillo_diagnostico
from app_core.pasillo import roadmap as pasillo_roadmap
from features.organizacion.services.roles_engine import listar_mis_organizaciones

logger = logging.getLogger(__name__)

SIN_DATOS = "SIN_DATOS"


async def _indicadores(session: AsyncSession, tenant_id: str, user_id: str) -> dict[str, Any]:
    await fijar_contexto_rls(session, tenant_id, user_id)
    resumen = await pasillo_diagnostico.resumen_para_cartera(session, tenant_id, user_id)
    return {
        "diagnostico": resumen["diagnostico"],
        "hallazgos_abiertos": await pasillo_roadmap.contar_hallazgos_abiertos(session, tenant_id, user_id),
        "tareas_vencidas": await pasillo_roadmap.contar_tareas_vencidas(session, tenant_id, user_id),
        "cadena_integra": resumen["cadena_integra"],
    }


async def armar_cartera(session: AsyncSession, user_id: str) -> list[dict[str, Any]]:
    """Filas de la cartera de `user_id`, ordenadas por nombre. Una organización que falla no tumba las demás."""
    organizaciones = await listar_mis_organizaciones(session, user_id)
    # Termina la transacción de la lectura de pertenencia: cada organización abre la suya.
    await session.commit()
    filas: list[dict[str, Any]] = []
    for org in organizaciones:
        fila: dict[str, Any] = {"tenant_id": org["tenant_id"], "nombre": org["nombre_comercial"], "roles": org["roles"]}
        try:
            fila.update(await _indicadores(session, org["tenant_id"], user_id))
            await session.commit()
        except Exception:  # una organización sin datos legibles no debe ocultar las otras
            await session.rollback()
            logger.warning("cartera: indicadores no disponibles", extra={"tenant_id": org["tenant_id"]})
            fila.update(
                diagnostico=None, hallazgos_abiertos=None, tareas_vencidas=None, cadena_integra=None, error=SIN_DATOS
            )
        filas.append(fila)
    return sorted(filas, key=lambda f: (f["nombre"], f["tenant_id"]))
