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
