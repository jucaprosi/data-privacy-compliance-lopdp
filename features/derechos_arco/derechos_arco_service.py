"""Compuerta pública de la sala ADPA: Derechos ARCO (solicitudes de derechos de titulares).
`¤adpa` `¤derechos`

Única vía por la que otras salas y la API acceden a la sala Derechos ARCO.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Sequence

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from features.derechos_arco.domain.models import (
    EstadoSolicitud,
    SolicitudARCO,
    TipoSolicitud,
)

PLAZO_DIAS = 15  # LOPDP: plazo de respuesta de una solicitud de derechos

__all__ = [
    "EstadoSolicitud",
    "SolicitudARCO",
    "TenantNoDisponible",
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


class TenantNoDisponible(ValueError):
    """No hay tenant: ni se recibió ni la sesión lo tiene fijado (RLS)."""


# ¤seguridad-tenant
async def _tenant_de_la_sesion(session: AsyncSession) -> str | None:
    valor = (await session.execute(text("SELECT current_setting('app.current_tenant_id', true)"))).scalar()
    return valor or None


# ¤seguridad-tenant
async def crear_solicitud_arco(
    session: AsyncSession,
    solicitud_data: dict,
    tenant_id: str | None = None,
) -> SolicitudARCO:
    """Crea la solicitud en el tenant recibido o, si no llega, en el de la sesión; nunca en uno generado.

    No hace commit: la transacción es de quien llama (DER-03). Hace flush para que la base asigne el id.
    """
    tenant = tenant_id or await _tenant_de_la_sesion(session)
    if not tenant:
        raise TenantNoDisponible("crear_solicitud_arco necesita el tenant de la organización")
    ahora = datetime.now(timezone.utc)
    nueva = SolicitudARCO(
        tenant_id=str(tenant),
        tipo_solicitud=TipoSolicitud(solicitud_data.get("tipo_solicitud", TipoSolicitud.ACCESO)),
        estado=EstadoSolicitud.RECIBIDA,
        cedula_solicitante=solicitud_data["cedula_solicitante"],
        nombre_solicitante=solicitud_data["nombre_solicitante"],
        fecha_recepcion=ahora,
        fecha_vencimiento=ahora + timedelta(days=PLAZO_DIAS),
    )
    session.add(nueva)
    await session.flush()
    await session.refresh(nueva)
    return nueva


# === DER-01 ===
# === fin DER-01 ===

# === DER-02 ===
# === fin DER-02 ===


# === ADPA-05 ===
# ¤adpa Los códigos de error de esta sala viven en features/derechos_arco/domain/errores.py y se registran al importarlo.
from features.derechos_arco.domain import errores as _errores_sala  # noqa: E402,F401
# === fin ADPA-05 ===
