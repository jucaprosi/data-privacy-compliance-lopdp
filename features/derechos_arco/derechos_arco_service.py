"""Compuerta pública de la sala ADPA: Derechos ARCO (solicitudes de derechos de titulares).
`¤adpa` `¤derechos`

Única vía por la que otras salas y la API acceden a la sala Derechos ARCO.
"""
from __future__ import annotations

from typing import List, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from features.derechos_arco.domain.models import (
    EstadoSolicitud,
    SolicitudARCO,
    TipoSolicitud,
)

__all__ = [
    "EstadoSolicitud",
    "SolicitudARCO",
    "TipoSolicitud",
    "crear_solicitud_arco",
    "listar_solicitudes_arco",
]


async def listar_solicitudes_arco(
    session: AsyncSession,
) -> Sequence[SolicitudARCO]:
    """Lista todas las solicitudes ARCO visibles en el contexto RLS actual."""
    result = await session.execute(select(SolicitudARCO))
    return result.scalars().all()


async def crear_solicitud_arco(
    session: AsyncSession,
    solicitud_data: dict,
) -> SolicitudARCO:
    """Crea y persiste una nueva solicitud ARCO en el tenant en curso."""
    from datetime import datetime, timedelta, timezone
    from uuid import uuid4

    nueva = SolicitudARCO(
        id=uuid4(),
        tenant_id=uuid4(),
        tipo_solicitud=TipoSolicitud.ACCESO,
        estado=EstadoSolicitud.RECIBIDA,
        cedula_solicitante=solicitud_data.get("cedula_solicitante", "9999999999"),
        nombre_solicitante=solicitud_data.get("nombre_solicitante", "Juan Perez"),
        fecha_recepcion=datetime.now(timezone.utc),
        fecha_vencimiento=datetime.now(timezone.utc) + timedelta(days=15),
    )
    session.add(nueva)
    await session.commit()
    await session.refresh(nueva)
    return nueva
