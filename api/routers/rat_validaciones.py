"""Validaciones y versiones de una ficha del RAT (RAT-05). ¤rat ¤hallazgos ¤rbac-tenant

Contrato: governance/especificaciones/RAT-05.md §2. Solo consulta: reglas, hallazgo y versión se
producen al guardar la ficha. Organización e identidad salen del contexto autenticado.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.rat import _permiso_rat, get_rat_session
from features.rat import rat_service

AUTO_REGISTRO = True
router = APIRouter(prefix="/rat", tags=["Registro de Actividades de Tratamiento (RAT)"])

_consulta = _permiso_rat("implementador", "coordinador", "dpo", "admin_organizacion", "responsable_area")


@router.get("/{rat_id}/validaciones")
async def validaciones(
    rat_id: str, ctx: dict = Depends(_consulta), session: AsyncSession = Depends(get_rat_session),
):
    return await rat_service.validaciones_de_ficha(session, ctx["tenant_id"], rat_id, ctx["user_id"])


@router.get("/{rat_id}/versiones")
async def versiones(
    rat_id: str, ctx: dict = Depends(_consulta), session: AsyncSession = Depends(get_rat_session),
):
    return {"versiones": await rat_service.versiones_de_ficha(session, ctx["tenant_id"], rat_id)}


@router.get("/{rat_id}/versiones/{numero}")
async def version(
    rat_id: str, numero: int, ctx: dict = Depends(_consulta), session: AsyncSession = Depends(get_rat_session),
):
    return await rat_service.version_de_ficha(session, ctx["tenant_id"], rat_id, numero)
