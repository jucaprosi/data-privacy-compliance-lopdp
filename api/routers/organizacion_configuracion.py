# ¤rbac-tenant
"""Router de configuración de la organización (tamaño y sector).

Endpoints:
- GET /api/v1/organizacion/configuracion
  Requiere membresía activa de cualquier rol en el tenant.
- PATCH /api/v1/organizacion/configuracion
  Requiere rol 'admin_organizacion'. Deja registro en audit_events.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import get_context, require_role
from app_core.db.session import get_session
from features.organizacion import organizacion_service
from features.organizacion.organizacion_service import TamanoOrganizacion

AUTO_REGISTRO = True

router = APIRouter(prefix="/organizacion", tags=["Organización - Configuración"])


class OrganizacionConfiguracionPatch(BaseModel):
    tamano: Optional[TamanoOrganizacion] = Field(
        default=None,
        description="Tamaño de la organización según vocabulario cerrado",
    )
    sector: Optional[str] = Field(
        default=None,
        description="Sector productivo o actividad de la organización",
    )


@router.get("/configuracion")
async def get_configuracion(
    ctx: dict = Depends(get_context),
    session: AsyncSession = Depends(get_session),
):
    """Consulta la configuración de la organización para el tenant en curso.
    
    Accesible por cualquier rol activo del tenant.
    """
    return await organizacion_service.get_tenant_config(
        session=session,
        tenant_id=ctx["tenant_id"],
    )


@router.patch("/configuracion")
async def patch_configuracion(
    payload: OrganizacionConfiguracionPatch,
    ctx: dict = Depends(require_role("admin_organizacion")),
    session: AsyncSession = Depends(get_session),
):
    """Actualiza tamaño y/o sector de la organización.
    
    Exclusivo para el rol 'admin_organizacion'.
    Registra el cambio inmutablemente en audit_events.
    """
    return await organizacion_service.update_tenant_config(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        tamano=payload.tamano.value if payload.tamano is not None else None,
        sector=payload.sector,
    )
