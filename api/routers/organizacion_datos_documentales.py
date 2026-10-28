# ¤rbac-tenant
"""Router de los datos de la organización para documentos (ORG-14).

Endpoints:
- GET /api/v1/organizacion/datos-documentales
  Requiere membresía activa de cualquier rol en el tenant.
- PATCH /api/v1/organizacion/datos-documentales
  Requiere rol 'admin_organizacion'. Deja registro en audit_events.

La organización sale siempre del contexto de la sesión (X-Tenant-ID verificado contra la
membresía); el cuerpo no la admite.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import get_context, require_role
from app_core.db.session import get_session
from features.organizacion import organizacion_service
from features.organizacion.organizacion_service import DatosDocumentalesPatch

AUTO_REGISTRO = True

router = APIRouter(prefix="/organizacion", tags=["Organización - Datos para documentos"])


@router.get("/datos-documentales")
async def get_datos_documentales(
    ctx: dict = Depends(get_context),
    session: AsyncSession = Depends(get_session),
):
    """Domicilio, contactos y representante legal de la organización, con los campos faltantes."""
    return await organizacion_service.obtener_datos_documentales(
        session=session,
        tenant_id=ctx["tenant_id"],
    )


@router.patch("/datos-documentales")
async def patch_datos_documentales(
    payload: DatosDocumentalesPatch,
    ctx: dict = Depends(require_role("admin_organizacion")),
    session: AsyncSession = Depends(get_session),
):
    """Actualiza los campos enviados. Exclusivo para 'admin_organizacion'."""
    return await organizacion_service.actualizar_datos_documentales(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        cambios=payload,
    )
