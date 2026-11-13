"""Compuerta pública de la sala ADPA: Transferencias (transferencias internacionales y debida diligencia).
`¤adpa` `¤transferencias`

Única vía por la que otras salas y la API acceden a la sala Transferencias.
"""
from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from features.transferencias.services.encargados_service import (
    NivelProteccion,
    RolTercero,
    TerceroEncargado,
)

__all__ = [
    "NivelProteccion",
    "RolTercero",
    "TerceroEncargado",
    "listar_transferencias",
]


async def listar_transferencias(
    session: AsyncSession,
) -> Sequence[TerceroEncargado]:
    """Lista las transferencias de terceros registradas en el tenant actual."""
    result = await session.execute(select(TerceroEncargado))
    return result.scalars().all()


# === ADPA-05 ===
# ¤adpa Los códigos de error de esta sala viven en features/transferencias/domain/errores.py y se registran al importarlo.
from features.transferencias.domain import errores as _errores_sala  # noqa: E402,F401
# === fin ADPA-05 ===


# === TER-01 ===
# ¤hallazgos ¤transferencias Contrato, garantía y revisión de cada tercero (especificación TER-01 §1).
# SQL explícito: las 7 columnas aún no están en features/transferencias/models.py (decisión del Arquitecto,
# 2026-11-13). Devuelve diccionarios planos; la sala terceros los convierte en su tipo.
from sqlalchemy import text as _text_ter01  # noqa: E402

from app_core.db.session import fijar_contexto_rls as _fijar_contexto_ter01  # noqa: E402

COLUMNAS_GARANTIAS = (
    "pais", "contrato_sha256", "contrato_vigente_hasta", "garantia_tipo",
    "garantia_sha256", "criticidad", "proxima_revision",
)
_SELECT_GARANTIAS = (
    "SELECT id::text AS id, nombre, rol, " + ", ".join(COLUMNAS_GARANTIAS) + " FROM transferencias_terceros"
)


async def listar_garantias_terceros(session: AsyncSession, tenant_id: str, user_id: str) -> list[dict]:
    """Terceros de la organización con sus columnas de contrato y garantía."""
    await _fijar_contexto_ter01(session, tenant_id, user_id)
    filas = await session.execute(
        _text_ter01(_SELECT_GARANTIAS + " WHERE tenant_id = :t ORDER BY nombre, id"), {"t": tenant_id}
    )
    return [dict(f) for f in filas.mappings()]


async def obtener_garantias_tercero(session: AsyncSession, tenant_id: str, user_id: str, tercero_id: str) -> dict | None:
    await _fijar_contexto_ter01(session, tenant_id, user_id)
    fila = (await session.execute(
        _text_ter01(_SELECT_GARANTIAS + " WHERE tenant_id = :t AND id::text = :i"), {"t": tenant_id, "i": tercero_id}
    )).mappings().first()
    return dict(fila) if fila else None


async def actualizar_garantias_tercero(
    session: AsyncSession, tenant_id: str, user_id: str, tercero_id: str, campos: dict
) -> dict | None:
    """Escribe solo las columnas de TER-01; `rol` se acepta con los valores existentes del CHECK."""
    permitidas = set(COLUMNAS_GARANTIAS) | {"rol"}
    sets = [c for c in campos if c in permitidas]
    if not sets:
        return await obtener_garantias_tercero(session, tenant_id, user_id, tercero_id)
    await _fijar_contexto_ter01(session, tenant_id, user_id)
    params = {c: campos[c] for c in sets} | {"t": tenant_id, "i": tercero_id}
    actualizado = (await session.execute(
        _text_ter01(
            "UPDATE transferencias_terceros SET " + ", ".join(f"{c} = :{c}" for c in sets)
            + " WHERE tenant_id = :t AND id::text = :i RETURNING id"
        ),
        params,
    )).scalar()
    if actualizado is None:
        return None
    return await obtener_garantias_tercero(session, tenant_id, user_id, tercero_id)


__all__ += ["COLUMNAS_GARANTIAS", "listar_garantias_terceros", "obtener_garantias_tercero",
            "actualizar_garantias_tercero"]
# === fin TER-01 ===
