"""Compuerta pública de la sala ADPA: Derechos ARCO (solicitudes de derechos de titulares).
`¤adpa` `¤derechos`

Única vía por la que otras salas y la API acceden a la sala Derechos ARCO.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Sequence

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from features.derechos_arco.domain.plazos import ESTIMADO as PLAZO_ESTIMADO
from features.derechos_arco.domain.plazos import UNIDAD as PLAZO_UNIDAD
from features.derechos_arco.domain.plazos import TIPOS_ACTIVOS, plazo_dias
from features.derechos_arco.domain.models import (
    EstadoSolicitud,
    SolicitudARCO,
    TipoSolicitud,
)

__all__ = [
    "PLAZO_ESTIMADO",
    "PLAZO_UNIDAD",
    "EstadoSolicitud",
    "SolicitudARCO",
    "TenantNoDisponible",
    "TipoNoDisponible",
    "TipoSolicitud",
    "crear_solicitud_arco",
    "listar_solicitudes_arco",
    "plazo_dias",
]


async def listar_solicitudes_arco(
    session: AsyncSession,
) -> Sequence[SolicitudARCO]:
    """Lista todas las solicitudes ARCO visibles en el contexto RLS actual."""
    result = await session.execute(select(SolicitudARCO))
    return result.scalars().all()


class TenantNoDisponible(ValueError):
    """No hay tenant: ni se recibió ni la sesión lo tiene fijado (RLS)."""


class TipoNoDisponible(ValueError):
    """El tipo de solicitud existe pero todavía no está activo para crear (DER-06a)."""


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
    tipo = TipoSolicitud(solicitud_data.get("tipo_solicitud", TipoSolicitud.ACCESO))
    if tipo not in TIPOS_ACTIVOS:
        raise TipoNoDisponible("tipo no disponible")
    tenant = tenant_id or await _tenant_de_la_sesion(session)
    if not tenant:
        raise TenantNoDisponible("crear_solicitud_arco necesita el tenant de la organización")
    ahora = datetime.now(timezone.utc)
    nueva = SolicitudARCO(
        tenant_id=str(tenant),
        tipo_solicitud=tipo,
        estado=EstadoSolicitud.RECIBIDA,
        cedula_solicitante=solicitud_data["cedula_solicitante"],
        nombre_solicitante=solicitud_data["nombre_solicitante"],
        fecha_recepcion=ahora,
        fecha_vencimiento=ahora + timedelta(days=plazo_dias(tipo)),
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

# === ORG-24 ===


async def contar_solicitudes_para_ficha(session: AsyncSession, tenant_id: str) -> dict:
    """Solicitudes sin contestar y las vencidas entre ellas (ficha de la organización, ORG-24).

    El tenant ya está fijado en la sesión (RLS); el filtro explícito es defensa en profundidad.
    """
    fila = (await session.execute(
        text(
            "SELECT count(*) AS abiertas, count(*) FILTER (WHERE fecha_vencimiento < now()) AS vencidas "
            "FROM derechos_arco_solicitudes WHERE tenant_id_texto = :t AND estado::text <> 'CONTESTADA'"
        ),
        {"t": tenant_id},
    )).mappings().one()
    return {
        "solicitudes_abiertas": int(fila["abiertas"]),
        "solicitudes_vencidas": int(fila["vencidas"]),
        "plazo_estimado": "ESTIMADO" if PLAZO_ESTIMADO else "VINCULANTE",
    }
# === fin ORG-24 ===
