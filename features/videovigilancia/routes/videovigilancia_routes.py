# ¤videovigilancia-cctv ¤seguridad-tenant ¤rbac-tenant
"""Rutas /videovigilancia/camaras. La identidad y los roles salen de app_core.security (ADPA: la sala no importa api)."""
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import get_session
from app_core.security import MODO_HEADERS, modo_autenticacion, roles_activos, usuario_verificado
from features.videovigilancia import videovigilancia_service as svc

router = APIRouter(prefix="/videovigilancia", tags=["Videovigilancia"])


def _contexto(roles_permitidos: tuple[str, ...]):
    async def dependencia(
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
        if x_role not in roles_permitidos:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Rol no autorizado para esta operación")
        if x_role not in await roles_activos(session, x_tenant_id, usuario):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Sin membresía activa")
        return {"tenant_id": x_tenant_id, "user_id": usuario, "role": x_role}

    return dependencia


_alta = _contexto(svc.ROLES_ALTA)
_consulta = _contexto(svc.ROLES_CONSULTA)


@router.get("/camaras", response_model=list[svc.CamaraSalida])
async def listar_camaras(ctx: dict = Depends(_consulta), session: AsyncSession = Depends(get_session)):
    return await svc.listar_camaras(session, ctx["tenant_id"])


@router.post("/camaras", response_model=svc.CamaraSalida, status_code=status.HTTP_201_CREATED)
async def registrar_camara(
    solicitud: svc.SolicitudCamara, ctx: dict = Depends(_alta), session: AsyncSession = Depends(get_session)
):
    return await svc.registrar_camara(session, ctx["tenant_id"], ctx["user_id"], solicitud)
