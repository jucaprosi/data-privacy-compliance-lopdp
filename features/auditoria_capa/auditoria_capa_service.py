"""Compuerta pública de la sala ADPA: Auditoría y CAPA."""
from typing import List
from features.auditoria_capa.domain.models import TicketCAPA, SeveridadHallazgo, EstadoCAPA
from features.auditoria_capa.services.capa_engine import (
    crear_ticket_capa,
    cerrar_ticket_verificado,
    listar_tickets_tenant,
)

def registrar_hallazgo_auditoria(ticket: TicketCAPA) -> TicketCAPA:
    """Registra una no conformidad u oportunidad de mejora."""
    return crear_ticket_capa(ticket)

def cerrar_accion_correctiva_independiente(ticket_id: str, auditor_id: str, evidencia_id: str) -> TicketCAPA:
    """Cierra un hallazgo tras verificar la eficacia con un rol independiente."""
    return cerrar_ticket_verificado(ticket_id, auditor_id, evidencia_id)

def consultar_hallazgos_tenant(tenant_id: str) -> List[TicketCAPA]:
    """Lista todos los tickets CAPA de una organización."""
    return listar_tickets_tenant(tenant_id)
