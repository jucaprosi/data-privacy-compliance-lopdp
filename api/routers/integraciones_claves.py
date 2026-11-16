# ¤¤backend-developer
# ¤rbac-tenant ¤seguridad ¤api-integraciones
"""Rutas de gestión de claves de integración y techos de paquete (API-02).

Invariante: INV_API_INTEGRATION_SCOPED_KEYS_VERSIONED.
Escriben `admin_organizacion` y `coordinador`. El DPO solo consulta.
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from app_core.integraciones import claves as claves_svc
from app_core.integraciones import techos as techos_svc

AUTO_REGISTRO = True

router = APIRouter(prefix="/integraciones", tags=["Integraciones"])

_ESCRITURA = require_role("admin_organizacion", "coordinador")
_LECTURA = require_role("admin_organizacion", "coordinador", "dpo")


class CrearClaveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: str = Field(..., min_length=1, max_length=120)
    alcances: list[str] = Field(default_factory=list)


@router.post("/claves", status_code=status.HTTP_201_CREATED)
async def crear_clave_integracion(
    payload: CrearClaveRequest,
    ctx: dict = Depends(_ESCRITURA),
    session: AsyncSession = Depends(get_session),
):
    clave, clave_en_claro = await claves_svc.crear_clave(
        session=session,
        tenant_id=ctx["tenant_id"],
        nombre=payload.nombre,
        alcances=payload.alcances,
        usuario_id=ctx["user_id"],
    )
    return {"status": "SUCCESS", "clave": clave, "clave_en_claro": clave_en_claro}


@router.get("/claves")
async def listar_claves_integracion(
    ctx: dict = Depends(_LECTURA),
    session: AsyncSession = Depends(get_session),
):
    claves = await claves_svc.listar_claves(session=session, tenant_id=ctx["tenant_id"])
    return {"claves": claves}


@router.post("/claves/{id}/rotar")
async def rotar_clave_integracion(
    id: str,
    ctx: dict = Depends(_ESCRITURA),
    session: AsyncSession = Depends(get_session),
):
    clave, clave_en_claro = await claves_svc.rotar_clave(
        session=session,
        tenant_id=ctx["tenant_id"],
        clave_id=id,
        usuario_id=ctx["user_id"],
    )
    return {"status": "SUCCESS", "clave": clave, "clave_en_claro": clave_en_claro}


@router.post("/claves/{id}/revocar")
async def revocar_clave_integracion(
    id: str,
    ctx: dict = Depends(_ESCRITURA),
    session: AsyncSession = Depends(get_session),
):
    clave = await claves_svc.revocar_clave(
        session=session,
        tenant_id=ctx["tenant_id"],
        clave_id=id,
        usuario_id=ctx["user_id"],
    )
    return {"status": "SUCCESS", "clave": clave}


@router.get("/techos")
async def consultar_techos_integracion(
    ctx: dict = Depends(_LECTURA),
    session: AsyncSession = Depends(get_session),
):
    techos = await techos_svc.obtener_techos_integracion(
        session=session,
        tenant_id=ctx["tenant_id"],
    )
    return techos
