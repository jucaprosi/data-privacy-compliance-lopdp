# ¤seguridad
# ¤rbac-tenant
"""Esquemas de datos para la sala Plataforma (ORG-09)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class OrganizacionCrearRequest(BaseModel):
    nombre_comercial: str = Field(..., min_length=2, max_length=255)
    razon_social: str = Field(..., min_length=2, max_length=255)
    ruc_identificacion: str = Field(..., min_length=10, max_length=20)
    tamano: Optional[str] = Field(None, pattern=r"^(micro|pequena|mediana|corporativo)$")
    sector: Optional[str] = Field(None, max_length=100)
    email_admin_inicial: str = Field(..., min_length=5, max_length=255)


class OrganizacionResumen(BaseModel):
    id: str
    nombre_comercial: str
    razon_social: str
    ruc_identificacion: str
    activo: Optional[bool] = True
    created_at: Optional[datetime] = None
    email_admin_inicial: Optional[str] = None
    invitacion_estado: Optional[str] = None


class AltaOrganizacionResponse(BaseModel):
    tenant_id: str
    invitacion_id: str
    codigo_invitacion: str
    expira_en: datetime
    email_invitado: str


class AceptarInvitacionRequest(BaseModel):
    codigo: str = Field(..., min_length=10)
    nombre_usuario: Optional[str] = Field(None, max_length=255)


class AceptarInvitacionResponse(BaseModel):
    tenant_id: str
    user_id: str
    email: str
    rol_asignado: str
    mensaje: str
