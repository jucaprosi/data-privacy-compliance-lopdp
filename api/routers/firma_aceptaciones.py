# ¤firma-electronica ¤rbac-tenant
"""API autenticada de aceptaciones (FIRMA-02).

Endpoints:
- POST /firma/aceptaciones  — crea enlaces de aceptación (implementador, coordinador, admin_organizacion)
- GET  /firma/aceptaciones  — lista aceptaciones del tenant (cualquier rol activo)
- POST /firma/verificar     — verifica si un archivo coincide con documentos o acuses (cualquier rol)
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

import features.biblioteca.biblioteca_service as _bib

from api.errores import ErrorNegocio
from api.rbac import get_context, require_role
from app_core.db.session import get_tenant_session
from features.firma_electronica import firma_electronica_service as firma

AUTO_REGISTRO = True
router = APIRouter(prefix="/firma", tags=["firma-aceptaciones"])

MAX_VERIFICAR_BYTES = 10 * 1024 * 1024  # 10 MB

_escritura = require_role("implementador", "coordinador", "admin_organizacion")


class SolicitudAceptacion(BaseModel):
    documento_id: UUID
    persona_ids: list[str] = Field(min_length=1, max_length=50)
    dias_vigencia: int = Field(ge=1, le=30)


@router.post("/aceptaciones", status_code=status.HTTP_201_CREATED)
async def crear_aceptaciones(
    solicitud: SolicitudAceptacion,
    ctx: dict = Depends(_escritura),
    session: AsyncSession = Depends(get_tenant_session),
):
    """Envía un documento aprobado a una o varias personas como enlace con caducidad."""
    try:
        enlaces = await firma.crear_enlaces(
            session,
            tenant_id=ctx["tenant_id"],
            user_id=ctx["user_id"],
            documento_id=str(solicitud.documento_id),
            persona_ids=solicitud.persona_ids,
            dias_vigencia=solicitud.dias_vigencia,
            obtener_doc=getattr(_bib, "obtener_documento_para_firma", None),
        )
    except ErrorNegocio:
        raise
    except NotImplementedError as exc:
        raise ErrorNegocio("SERVICIO_NO_DISPONIBLE", detail=str(exc), status_code=503) from exc
    return {"enlaces": [{"persona_id": e.persona_id, "url": e.url} for e in enlaces]}


@router.get("/aceptaciones")
async def listar_aceptaciones(
    documento_id: Optional[UUID] = Query(None),
    ctx: dict = Depends(get_context),
    session: AsyncSession = Depends(get_tenant_session),
):
    """Lista las aceptaciones del tenant, sin exponer el token."""
    aceptaciones = await firma.listar_aceptaciones(
        session,
        tenant_id=ctx["tenant_id"],
        documento_id=str(documento_id) if documento_id else None,
    )
    return {"aceptaciones": aceptaciones}


@router.post("/verificar")
async def verificar_documento(
    archivo: UploadFile = File(...),
    ctx: dict = Depends(get_context),
    session: AsyncSession = Depends(get_tenant_session),
):
    """Verifica si el hash del archivo coincide con un documento aprobado o un acuse del tenant."""
    contenido = await archivo.read(MAX_VERIFICAR_BYTES + 1)
    if len(contenido) > MAX_VERIFICAR_BYTES:
        raise ErrorNegocio("ARCHIVO_DEMASIADO_GRANDE", detail="El archivo supera 10 MB.", status_code=413)
    coincide, tipo = await firma.verificar_hash(session, ctx["tenant_id"], contenido)
    return {"coincide": coincide, "tipo": tipo}
