"""Compuerta pública de la sala ADPA: Auditoría Anual y Planes de Acción (CAPA)."""
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from features.auditoria_capa.domain.models import EstadoCAPA, SeveridadHallazgo, TicketCAPA
from features.auditoria_capa.services.capa_engine import (
    TicketYaCerradoError,
    cerrar_ticket_verificado,
    crear_ticket_capa,
    listar_tickets_tenant,
    validar_cierre_sod,
)


async def registrar_hallazgo_capa(
    session: AsyncSession, ticket: TicketCAPA
) -> TicketCAPA:
    """Registra y persiste un hallazgo de auditoría en PostgreSQL."""
    return await crear_ticket_capa(session, ticket)


async def listar_tickets_capa(
    session: AsyncSession, tenant_id: str
) -> List[TicketCAPA]:
    """Lista los tickets CAPA de la organización desde PostgreSQL."""
    return await listar_tickets_tenant(session, tenant_id)


async def cerrar_ticket_capa(
    session: AsyncSession,
    tenant_id: str,
    ticket_id: str,
    auditor_id: str,
    evidencia_id: str,
) -> TicketCAPA:
    """Cierra y verifica un ticket CAPA en PostgreSQL aplicando SoD e inmutabilidad."""
    return await cerrar_ticket_verificado(
        session=session,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        auditor_id=auditor_id,
        evidencia_id=evidencia_id,
    )


__all__ = [
    "EstadoCAPA",
    "SeveridadHallazgo",
    "TicketCAPA",
    "TicketYaCerradoError",
    "cerrar_ticket_capa",
    "listar_tickets_capa",
    "registrar_hallazgo_capa",
    "validar_cierre_sod",
]


# === CAPA-02 ===
from features.auditoria_capa.domain.control_periodico import (  # noqa: E402
    ControlPeriodico,
    CrearControlEntrada,
    EstadoControl,
    FrecuenciaControl,
    ResultadoVencimiento,
    RetirarControlEntrada,
    VerificacionControl,
    VerificarControlEntrada,
)
from features.auditoria_capa.services.controles_engine import (  # noqa: E402
    crear_control,
    listar_controles,
    registrar_verificacion,
    retirar_control,
    vencer_controles,
)

__all__.extend([
    "ControlPeriodico",
    "CrearControlEntrada",
    "EstadoControl",
    "FrecuenciaControl",
    "ResultadoVencimiento",
    "RetirarControlEntrada",
    "VerificacionControl",
    "VerificarControlEntrada",
    "crear_control",
    "listar_controles",
    "registrar_verificacion",
    "retirar_control",
    "vencer_controles",
])
# === fin CAPA-02 ===
