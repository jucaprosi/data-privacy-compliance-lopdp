# ¤adpa
# ¤rbac-tenant
"""Ficha de la organización activa (ORG-24, para FE-25).

Es del tenant del contexto, nunca de varias organizaciones: lleva RUC, naturaleza, los nombres del DPO y del
implementador (datos personales: solo los ven `ROLES_VEN_NOMBRES`) y contadores de las salas de derechos e
incidentes. Cada contador se consulta aparte: si una compuerta falla, solo ese campo queda en `null` con su
error y la ficha responde igual (mismo criterio que la cartera, ORG-15).

Visibilidad de los nombres: ESTIMADA por decisión del CTO (2026-11-12), pendiente de respuesta del abogado.
Lista cerrada de roles que ven; cualquier otro rol, incluido uno nuevo, recibe `nombres_visibles=false`, `null` y `[]`
(el texto «No disponible» es de presentación y lo pone el frontend).
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import fijar_contexto_rls
from app_core.pasillo import derechos_arco as pasillo_derechos
from app_core.pasillo import incidentes as pasillo_incidentes

logger = logging.getLogger(__name__)

SIN_DATOS = "SIN_DATOS"
PLAZO_NO_DEFINIDO = "plazo_no_definido"
ROLES_VEN_NOMBRES: frozenset[str] = frozenset({"admin_organizacion", "implementador", "dpo"})

_SQL_TENANT = "SELECT nombre_comercial, ruc_identificacion, naturaleza FROM tenants WHERE id = :t"
_SQL_NOMBRES = (
    "SELECT u.nombre AS nombre, r.role AS rol FROM user_tenant_roles r JOIN users u ON u.id = r.user_id "
    "WHERE r.tenant_id = :t AND r.role IN ('dpo', 'implementador') AND u.deleted_at IS NULL "
    "AND (r.valid_from IS NULL OR r.valid_from <= now()) AND (r.valid_to IS NULL OR r.valid_to > now()) ORDER BY u.nombre, r.id"
)


def nombres_visibles(rol: str) -> bool:
    """Única función de la regla: ven los nombres solo los roles de la lista cerrada."""
    return rol in ROLES_VEN_NOMBRES


async def _nombres(session: AsyncSession, tenant_id: str) -> tuple[str | None, list[str]]:
    filas = (await session.execute(text(_SQL_NOMBRES), {"t": tenant_id})).mappings().all()
    dpo = next((f["nombre"] for f in filas if f["rol"] == "dpo"), None)
    return dpo, [f["nombre"] for f in filas if f["rol"] == "implementador"]


async def _aislado(session: AsyncSession, errores: dict[str, str], campos: tuple[str, ...], consulta) -> dict[str, Any]:
    """Ejecuta una compuerta en un savepoint: si falla, devuelve sus campos en None y anota el error."""
    try:
        async with session.begin_nested():
            return await consulta()
    except Exception:
        logger.warning("ficha: compuerta no disponible", extra={"campos": campos})
        for campo in campos:
            errores[campo] = SIN_DATOS
        return {campo: None for campo in campos}


async def armar_ficha(session: AsyncSession, tenant_id: str, user_id: str, rol: str) -> dict[str, Any]:
    """Ficha del tenant `tenant_id` para `user_id` con el rol `rol` (el del contexto verificado)."""
    await fijar_contexto_rls(session, tenant_id, user_id)
    fila = (await session.execute(text(_SQL_TENANT), {"t": tenant_id})).mappings().first()
    errores: dict[str, str] = {}
    visibles = nombres_visibles(rol)
    # Minimización: sin permiso, ni siquiera se consultan los nombres.
    dpo, implementadores = await _nombres(session, tenant_id) if visibles else (None, [])
    solicitudes = await _aislado(
        session, errores, ("solicitudes_abiertas", "solicitudes_vencidas", "plazo_estimado"),
        lambda: pasillo_derechos.contar_solicitudes_para_ficha(session, tenant_id, user_id),
    )
    incidentes = await _aislado(
        session, errores, ("vulneraciones_abiertas",),
        lambda: pasillo_incidentes.contar_vulneraciones_para_ficha(session, tenant_id, user_id),
    )
    return {
        "tenant_id": tenant_id,
        "nombre": fila["nombre_comercial"] if fila else None,
        "ruc": fila["ruc_identificacion"] if fila else None,
        "naturaleza": fila["naturaleza"] if fila else None,
        "nombres_visibles": visibles,
        "dpo_nombre": dpo,
        "implementadores": implementadores,
        **solicitudes,
        **incidentes,
        "vulneraciones_con_plazo": None,
        "vulneraciones_con_plazo_motivo": PLAZO_NO_DEFINIDO,
        "errores": errores,
    }
