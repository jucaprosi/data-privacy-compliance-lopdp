# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤boveda-cloud ¤seguridad-tenant ¤conservacion
"""Rutas /boveda-cloud/objetos: URLs firmadas V4 directas a Cloud Storage (BOV-02).

La API solo devuelve la URL firmada; los bytes del archivo no pasan por ella.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import get_session
from app_core.security import MODO_HEADERS, modo_autenticacion, roles_activos, usuario_verificado
from features.boveda_cloud import boveda_cloud_service as svc

router = APIRouter(prefix="/boveda-cloud/objetos", tags=["Bóveda Cloud"])


async def contexto_objetos(
    authorization: Optional[str] = Header(None),
    x_user_id: str = Header("", alias="X-User-ID"),
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_role: str = Header(..., alias="X-Role"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Identidad verificada, rol permitido y membresía activa (mismo criterio que la consulta de suscripción)."""
    if modo_autenticacion() == MODO_HEADERS:
        if not x_user_id:
            raise HTTPException(422, "Falta la cabecera X-User-ID")
        usuario = x_user_id
    else:
        usuario = (await usuario_verificado(session, authorization)).usuario_id
    if x_role not in svc.ROLES_OBJETOS:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Rol no autorizado para esta operación")
    if x_role not in await roles_activos(session, x_tenant_id, usuario):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sin membresía activa")
    return {"tenant_id": x_tenant_id, "user_id": usuario, "role": x_role}


@router.post("/url-subida-firmada", response_model=svc.UrlFirmadaSalida, status_code=status.HTTP_201_CREATED)
async def url_subida_firmada(
    solicitud: svc.SolicitudUrlSubida,
    ctx: dict = Depends(contexto_objetos),
    session: AsyncSession = Depends(get_session),
):
    return await svc.solicitar_url_subida(session, ctx["tenant_id"], solicitud, ctx["user_id"])


@router.post("/{objeto_id}/url-descarga-firmada", response_model=svc.UrlFirmadaSalida)
async def url_descarga_firmada(
    objeto_id: str,
    ctx: dict = Depends(contexto_objetos),
    session: AsyncSession = Depends(get_session),
):
    return await svc.solicitar_url_descarga(session, ctx["tenant_id"], objeto_id, ctx["user_id"])
