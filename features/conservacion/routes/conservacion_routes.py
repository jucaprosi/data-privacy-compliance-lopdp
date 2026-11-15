# ¤conservacion ¤seguridad-tenant
"""Rutas /conservacion/politicas. Matriz propia: consulta y alta para ROLES_CONSULTA; ejecutar, para ROLES_EJECUCION.

La identidad y los roles salen de app_core.security (ADPA §7.1 R3: la sala no importa la capa api ni otras salas).
"""
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import get_session
from app_core.security import MODO_HEADERS, modo_autenticacion, roles_activos, usuario_verificado
from features.conservacion import conservacion_service as svc

router = APIRouter(prefix="/conservacion", tags=["Conservación y Bloqueo"])


async def _contexto(
    roles_permitidos: tuple[str, ...],
    authorization: Optional[str],
    x_user_id: str,
    x_tenant_id: str,
    x_role: str,
    session: AsyncSession,
) -> dict:
    """Mismo criterio que api.rbac.require_role: identidad verificada, rol permitido y membresía activa."""
    if modo_autenticacion() == MODO_HEADERS:
        if not x_user_id:
            raise HTTPException(422, "Falta la cabecera X-User-ID")
        usuario = x_user_id
    else:
        usuario = (await usuario_verificado(session, authorization)).usuario_id
    if x_role not in roles_permitidos:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Rol no autorizado para esta operación")
    if x_role not in await roles_activos(session, x_tenant_id, usuario):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sin membresía activa")
    return {"tenant_id": x_tenant_id, "user_id": usuario, "role": x_role}


async def contexto_consulta(
    authorization: Optional[str] = Header(None),
    x_user_id: str = Header("", alias="X-User-ID"),
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_role: str = Header(..., alias="X-Role"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await _contexto(svc.ROLES_CONSULTA, authorization, x_user_id, x_tenant_id, x_role, session)


async def contexto_ejecucion(
    authorization: Optional[str] = Header(None),
    x_user_id: str = Header("", alias="X-User-ID"),
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_role: str = Header(..., alias="X-Role"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await _contexto(svc.ROLES_EJECUCION, authorization, x_user_id, x_tenant_id, x_role, session)


@router.get("/politicas", response_model=list[svc.PoliticaSalida], status_code=status.HTTP_200_OK)
async def listar(ctx: dict = Depends(contexto_consulta), session: AsyncSession = Depends(get_session)):
    return await svc.listar_politicas(session, ctx["tenant_id"])


@router.post("/politicas", response_model=svc.PoliticaSalida, status_code=status.HTTP_201_CREATED)
async def crear(
    cuerpo: svc.PoliticaEntrada,
    ctx: dict = Depends(contexto_consulta),
    session: AsyncSession = Depends(get_session),
):
    return await svc.crear_politica(session, ctx["tenant_id"], cuerpo, ctx["user_id"])


@router.post("/politicas/{politica_id}/ejecutar", response_model=svc.PoliticaSalida, status_code=status.HTTP_200_OK)
async def ejecutar(
    politica_id: str,
    ctx: dict = Depends(contexto_ejecucion),
    session: AsyncSession = Depends(get_session),
):
    return await svc.ejecutar_politica(session, ctx["tenant_id"], politica_id, ctx["user_id"])
