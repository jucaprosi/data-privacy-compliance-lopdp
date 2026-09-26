"""Lógica de negocio para tickets de No Conformidad y CAPA con verificación independiente."""
from typing import Dict, List, Optional
from datetime import datetime, timezone
from features.auditoria_capa.domain.models import TicketCAPA, EstadoCAPA

class InMemoryCAPARepository:
    def __init__(self):
        self._store: Dict[str, TicketCAPA] = {}

    def guardar(self, ticket: TicketCAPA) -> TicketCAPA:
        self._store[ticket.id] = ticket
        return ticket

    def obtener_por_id(self, ticket_id: str) -> Optional[TicketCAPA]:
        return self._store.get(ticket_id)

    def listar_por_tenant(self, tenant_id: str) -> List[TicketCAPA]:
        return [t for t in self._store.values() if t.tenant_id == tenant_id]

repo_capa = InMemoryCAPARepository()

def crear_ticket_capa(ticket: TicketCAPA, version_normativa: str = "LOPDP-Ecuador-2021") -> TicketCAPA:
    ticket.estado = EstadoCAPA.ABIERTO
    # Inyección de Snapshot Normativo para inmutabilidad histórica
    # En un entorno real se extraería de la configuración global del sistema
    ticket.snapshot_normativo = version_normativa
    return repo_capa.guardar(ticket)

def cerrar_ticket_verificado(ticket_id: str, auditor_id: str, evidencia_id: str) -> TicketCAPA:
    """Cierra un hallazgo solo si quien verifica es un rol independiente del implementador."""
    ticket = repo_capa.obtener_por_id(ticket_id)
    if not ticket:
        raise KeyError(f"Ticket CAPA {ticket_id} no encontrado")

    # Invariante SoD: El implementador no puede verificar su propio cierre
    if ticket.responsable_implementacion_id == auditor_id:
        raise PermissionError("Violación SoD: El implementador de la acción correctiva no puede ser el auditor que verifica y cierra el hallazgo.")

    if not evidencia_id:
        raise ValueError("No se puede cerrar un ticket CAPA sin vincular la evidencia de cierre.")

    ticket.auditor_verificador_id = auditor_id
    ticket.evidencia_cierre_id = evidencia_id
    ticket.estado = EstadoCAPA.CERRADO_VERIFICADO
    ticket.fecha_cierre = datetime.now(timezone.utc)
    return repo_capa.guardar(ticket)

def listar_tickets_tenant(tenant_id: str) -> List[TicketCAPA]:
    return repo_capa.listar_por_tenant(tenant_id)
