# ¤boveda-cloud ¤seguridad-tenant
"""Rutas /boveda-cloud/suscripcion. La consulta es del tenant del contexto; el alta, del operador de plataforma.

La identidad y los roles salen de app_core.security (ADPA §7.1 R3: la sala no importa la capa api ni otras salas).
"""
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import get_session
from app_core.security import (
    MODO_HEADERS,
    extraer_bearer,
    modo_autenticacion,
    roles_activos,
    usuario_verificado,
    verificar_token_google,
)
from features.boveda_cloud import boveda_cloud_service as svc

router = APIRouter(prefix="/boveda-cloud", tags=["Bóveda Cloud"])


async def contexto_consulta(
    authorization: Optional[str] = Header(None),
    x_user_id: str = Header("", alias="X-User-ID"),
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_role: str = Header(..., alias="X-Role"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Mismo criterio que api.rbac.require_role: identidad verificada, rol permitido y membresía activa."""
    if modo_autenticacion() == MODO_HEADERS:
        if not x_user_id:
            raise HTTPException(422, "Falta la cabecera X-User-ID")
        usuario = x_user_id
    else:
        usuario = (await usuario_verificado(session, authorization)).usuario_id
    if x_role not in svc.ROLES_CONSULTA:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Rol no autorizado para esta operación")
    if x_role not in await roles_activos(session, x_tenant_id, usuario):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sin membresía activa")
    return {"tenant_id": x_tenant_id, "user_id": usuario, "role": x_role}


async def requiere_operador(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_user_email: Optional[str] = Header(None, alias="X-User-Email"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Mismo criterio que el router de plataforma (ORG-09): operador activo verificado."""
    if modo_autenticacion() == MODO_HEADERS:
        email, sub = (x_user_email or "").strip().lower(), (x_user_id or "").strip()
        if not email and not sub:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Falta cabecera de identidad.")
    else:
        identidad = await verificar_token_google(extraer_bearer(authorization))
        email, sub = identidad.email, identidad.sub
    operador = await svc.operador_activo(session, email, sub)
    if operador is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Acceso restringido al operador de la plataforma.")
    return operador


@router.get("/suscripcion", response_model=svc.SuscripcionSalida)
async def obtener_suscripcion(ctx: dict = Depends(contexto_consulta), session: AsyncSession = Depends(get_session)):
    return await svc.obtener_suscripcion(session, ctx["tenant_id"])


@router.post("/suscripcion", response_model=svc.SuscripcionSalida, status_code=status.HTTP_201_CREATED)
async def crear_suscripcion(
    alta: svc.SolicitudAlta,
    operador: dict = Depends(requiere_operador),
    session: AsyncSession = Depends(get_session),
):
    return await svc.crear_suscripcion(session, alta, operador["id"])
