# ¤boveda-cloud ¤videovigilancia-cctv ¤dpo-cockpit ¤conservacion
"""Rutas `/boveda-cloud/orquestador-10d`: centro de mando multidimensional (BOV-04).

Protegido por autenticación y membresía de sala (`ROLES_CONSULTA` / `X-Tenant-ID`) mediante
`app_core.security`, sin importar la capa `api`.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import get_session
from app_core.security import MODO_HEADERS, modo_autenticacion, roles_activos, usuario_verificado
from features.boveda_cloud import boveda_cloud_service as svc

router = APIRouter(prefix="/boveda-cloud", tags=["Bóveda Cloud"])


async def contexto_consulta_orquestador(
    authorization: Optional[str] = Header(None),
    x_user_id: str = Header("", alias="X-User-ID"),
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_role: str = Header(..., alias="X-Role"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Identidad verificada, rol permitido (`ROLES_CONSULTA`) y membresía activa en el tenant."""
    tenant_id = x_tenant_id.strip()
    if not tenant_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Encabezado X-Tenant-ID obligatorio para resolver contexto de aislamiento.",
        )
    if modo_autenticacion() == MODO_HEADERS:
        if not x_user_id:
            raise HTTPException(422, "Falta la cabecera X-User-ID")
        usuario = x_user_id
    else:
        usuario = (await usuario_verificado(session, authorization)).usuario_id
    if x_role not in svc.ROLES_CONSULTA:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Rol no autorizado para esta operación")
    if x_role not in await roles_activos(session, tenant_id, usuario):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sin membresía activa")
    return {"tenant_id": tenant_id, "user_id": usuario, "role": x_role}


@router.get("/orquestador-10d", response_model=svc.ResumenOrquestadorDiezDimensiones)
async def obtener_orquestador_10d(
    incluir_metrica_global: bool = Query(default=False),
    ctx: dict = Depends(contexto_consulta_orquestador),
    session: AsyncSession = Depends(get_session),
):
    """Expone el resumen multidimensional de las 10 dimensiones LOPDP y Bóveda Cloud."""
    modo_lectura = ctx["role"] == "dpo"
    return await svc.obtener_resumen_orquestador_10d(
        session,
        ctx["tenant_id"],
        modo_lectura=modo_lectura,
        incluir_metrica_global=incluir_metrica_global,
    )
