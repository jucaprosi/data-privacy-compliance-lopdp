# ¤seguridad
# ¤rbac-tenant
"""Compuerta pública de la sala ADPA: Plataforma (Operador e Invitaciones).

Única interfaz pública por la que otras salas, la API y los árbitros acceden
a las operaciones de administración global de la plataforma (ORG-09).
"""
from __future__ import annotations

from features.plataforma.domain.models import (
    AceptarInvitacionRequest,
    AceptarInvitacionResponse,
    AltaOrganizacionResponse,
    OrganizacionCrearRequest,
    OrganizacionResumen,
)
from features.plataforma.services.operador_engine import (
    aceptar_invitacion,
    crear_organizacion_e_invitacion,
    listar_organizaciones,
    registrar_auditoria_plataforma,
    revocar_invitacion,
    verificar_operador,
)

__all__ = [
    "AceptarInvitacionRequest",
    "AceptarInvitacionResponse",
    "AltaOrganizacionResponse",
    "OrganizacionCrearRequest",
    "OrganizacionResumen",
    "aceptar_invitacion",
    "crear_organizacion_e_invitacion",
    "listar_organizaciones",
    "registrar_auditoria_plataforma",
    "revocar_invitacion",
    "verificar_operador",
]
