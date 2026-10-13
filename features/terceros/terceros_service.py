"""Compuerta pública de la sala ADPA: Terceros (gestión de terceros y encargados de tratamiento).
`¤adpa`

Única vía por la que otras salas y la API acceden a la sala Terceros.
"""
from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from features.terceros.domain.models import Tercero

__all__ = [
    "Tercero",
    "listar_terceros_encargados",
]


async def listar_terceros_encargados(
    session: AsyncSession,
) -> Sequence[Tercero]:
    """Lista todos los terceros encargados visibles en el contexto RLS actual."""
    result = await session.execute(select(Tercero))
    return result.scalars().all()
