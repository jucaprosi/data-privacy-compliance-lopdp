"""Colectivos de titulares y registro agregado de consentimientos (RAT-07). ¤rat ¤evidencias ¤rbac-tenant

Contrato: governance/especificaciones/RAT-07.md §2. Nunca datos de un titular individual. Organización e
identidad salen del contexto autenticado. Escriben implementador, coordinador y admin_organizacion; el DPO lee.
"""
from datetime import date

from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.rat import _permiso_rat, get_rat_session
from features.rat import rat_service

AUTO_REGISTRO = True
router = APIRouter(prefix="/rat", tags=["Registro de Actividades de Tratamiento (RAT)"])

_escritura = _permiso_rat("implementador", "coordinador", "admin_organizacion")
_consulta = _permiso_rat("implementador", "coordinador", "dpo", "admin_organizacion", "responsable_area")


@router.get("/{rat_id}/colectivos")
async def listar_colectivos(
    rat_id: str, ctx: dict = Depends(_consulta), session: AsyncSession = Depends(get_rat_session),
):
    return {"colectivos": await rat_service.listar_colectivos_rat(session, ctx["tenant_id"], rat_id)}


@router.post("/{rat_id}/colectivos", status_code=201)
async def crear_colectivo(
    rat_id: str, cuerpo: dict = Body(...), ctx: dict = Depends(_escritura),
    session: AsyncSession = Depends(get_rat_session),
):
    return await rat_service.crear_colectivo_rat(session, ctx["tenant_id"], rat_id, cuerpo, ctx["user_id"])


@router.put("/colectivos/{colectivo_id}")
async def editar_colectivo(
    colectivo_id: str, cuerpo: dict = Body(...), ctx: dict = Depends(_escritura),
    session: AsyncSession = Depends(get_rat_session),
):
    return await rat_service.editar_colectivo_rat(session, ctx["tenant_id"], colectivo_id, cuerpo)


@router.post("/colectivos/{colectivo_id}/consentimientos", status_code=201)
async def registrar_consentimiento(
    colectivo_id: str, cuerpo: dict = Body(...), ctx: dict = Depends(_escritura),
    session: AsyncSession = Depends(get_rat_session),
):
    return await rat_service.registrar_consentimiento_rat(
        session, ctx["tenant_id"], colectivo_id, cuerpo, ctx["user_id"])


@router.get("/colectivos/{colectivo_id}/consentimientos")
async def consultar_consentimientos(
    colectivo_id: str, desde: date | None = None, hasta: date | None = None,
    ctx: dict = Depends(_consulta), session: AsyncSession = Depends(get_rat_session),
):
    return await rat_service.consentimientos_de_colectivo(session, ctx["tenant_id"], colectivo_id, desde, hasta)
