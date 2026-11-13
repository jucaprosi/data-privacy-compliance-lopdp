# ¤rbac-tenant
"""Ficha de la organización activa (ORG-24, governance/tareas/ORG-24.md): `GET /organizacion/ficha`.

El tenant sale del contexto verificado (token y `X-Tenant-ID` con membresía vigente), nunca del cuerpo. Cualquier
rol vigente la lee; los nombres del DPO y del implementador solo los ve la lista cerrada de `nombres_visibles`.
El contrato de la respuesta es `FichaOrganizacion`.
"""
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import get_context
from app_core.db.session import get_session
from features.organizacion import organizacion_service

AUTO_REGISTRO = True

router = APIRouter(prefix="/organizacion", tags=["Organización - Ficha"])


class FichaOrganizacion(BaseModel):
    tenant_id: str
    nombre: Optional[str] = None
    ruc: Optional[str] = None
    naturaleza: Optional[str] = None
    nombres_visibles: bool
    dpo_nombre: Optional[str] = None
    implementadores: list[str]
    solicitudes_abiertas: Optional[int] = None
    solicitudes_vencidas: Optional[int] = None
    plazo_estimado: Optional[str] = None
    vulneraciones_abiertas: Optional[int] = None
    vulneraciones_con_plazo: Optional[int] = None
    vulneraciones_con_plazo_motivo: str
    errores: dict[str, str]


@router.get("/ficha", response_model=FichaOrganizacion)
async def ficha(ctx: dict = Depends(get_context), session: AsyncSession = Depends(get_session)):
    """RUC, naturaleza, nombres (según rol) y contadores de la organización activa."""
    return await organizacion_service.armar_ficha(session, ctx["tenant_id"], ctx["user_id"], ctx["role"])
