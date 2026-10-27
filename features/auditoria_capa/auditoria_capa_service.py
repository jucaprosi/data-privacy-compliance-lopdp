"""Compuerta pública de la sala ADPA: Auditoría Anual y Planes de Acción (CAPA)."""
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from features.auditoria_capa.domain.models import EstadoCAPA, SeveridadHallazgo, TicketCAPA
from features.auditoria_capa.services.capa_engine import (
    TicketYaCerradoError,
    cerrar_ticket_dominio,
    cerrar_ticket_verificado,
    crear_ticket_capa,
    listar_tickets_tenant,
    preparar_ticket_dominio,
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


def registrar_hallazgo_auditoria(
    ticket_o_session: TicketCAPA | AsyncSession,
    ticket: Optional[TicketCAPA] = None,
):
    """Abre un ticket CAPA (con AsyncSession persiste en PostgreSQL)."""
    if isinstance(ticket_o_session, AsyncSession):
        if ticket is None:
            raise ValueError("Se requiere el ticket CAPA a persistir.")
        return registrar_hallazgo_capa(ticket_o_session, ticket)
    return preparar_ticket_dominio(ticket_o_session)


def obtener_tickets_capa(session: AsyncSession, tenant_id: str):
    """Lista los planes de acción correctiva y preventiva de la organización."""
    return listar_tickets_capa(session, tenant_id)


consultar_hallazgos_tenant = listar_tickets_capa


def cerrar_accion_correctiva_independiente(
    ticket_id: str,
    auditor_id: str = "",
    evidencia_id: str = "",
) -> TicketCAPA:
    """Cierra un ticket CAPA en el dominio validando que el auditor no sea el implementador (SoD)."""
    return cerrar_ticket_dominio(
        ticket_id=ticket_id,
        auditor_id=auditor_id,
        evidencia_id=evidencia_id,
    )


__all__ = [
    "EstadoCAPA",
    "SeveridadHallazgo",
    "TicketCAPA",
    "TicketYaCerradoError",
    "cerrar_accion_correctiva_independiente",
    "cerrar_ticket_capa",
    "consultar_hallazgos_tenant",
    "listar_tickets_capa",
    "obtener_tickets_capa",
    "registrar_hallazgo_auditoria",
    "registrar_hallazgo_capa",
]
