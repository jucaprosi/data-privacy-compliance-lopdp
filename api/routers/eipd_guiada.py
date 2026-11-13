# ¤riesgos-eipd ¤rbac-tenant
"""MTGE-03: API de la EIPD guiada de ocho pasos.

Organización y usuario salen del contexto autenticado (`get_context`), nunca del cuerpo.
Escriben `implementador` y `coordinador`; cierra `implementador`; leen además `dpo`, `admin_organizacion` y `auditor` (ORG-22: lee, no ejecuta).
"""
from typing import Optional

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from features.riesgos_mtge import riesgos_mtge_service as sala
from features.riesgos_mtge.riesgos_mtge_service import CierreEipd, CrearEipd, Eipd, InformeEipd

router = APIRouter(prefix="/eipd", tags=["Evaluación de impacto guiada (MTGE-03)"])
AUTO_REGISTRO = True

_escritura = require_role("implementador", "coordinador")
_cierre = require_role("implementador")
_lectura = require_role("implementador", "coordinador", "dpo", "admin_organizacion", "auditor")


@router.get("/catalogos")
async def catalogos(ctx: dict = Depends(_lectura)):
    return {"fases": sala.FASES_CICLO_VIDA, "amenazas": sala.AMENAZAS}


@router.post("", response_model=Eipd, status_code=status.HTTP_201_CREATED)
async def crear(payload: CrearEipd, ctx: dict = Depends(_escritura), session: AsyncSession = Depends(get_session)):
    eipd = await sala.crear_eipd(session, ctx["tenant_id"], ctx["user_id"], payload.tratamiento_id)
    await session.commit()
    return eipd


@router.get("", response_model=list[Eipd])
async def listar(tratamiento_id: Optional[str] = None, ctx: dict = Depends(_lectura),
                 session: AsyncSession = Depends(get_session)):
    return await sala.listar_eipd(session, ctx["tenant_id"], ctx["user_id"], tratamiento_id)


@router.get("/{eipd_id}", response_model=Eipd)
async def obtener(eipd_id: str, ctx: dict = Depends(_lectura), session: AsyncSession = Depends(get_session)):
    return await sala.obtener_eipd(session, ctx["tenant_id"], ctx["user_id"], eipd_id)


@router.put("/{eipd_id}/paso/{n}", response_model=Eipd)
async def guardar_paso(eipd_id: str, n: int, cuerpo: dict = Body(...), ctx: dict = Depends(_escritura),
                       session: AsyncSession = Depends(get_session)):
    eipd = await sala.guardar_paso(session, ctx["tenant_id"], ctx["user_id"], eipd_id, n, cuerpo)
    await session.commit()
    return eipd


@router.post("/{eipd_id}/cerrar", response_model=CierreEipd)
async def cerrar(eipd_id: str, ctx: dict = Depends(_cierre), session: AsyncSession = Depends(get_session)):
    cierre = await sala.cerrar_eipd(session, ctx["tenant_id"], ctx["user_id"], eipd_id)
    await session.commit()
    return cierre


@router.get("/{eipd_id}/informe", response_model=InformeEipd)
async def informe(eipd_id: str, ctx: dict = Depends(_lectura), session: AsyncSession = Depends(get_session)):
    return await sala.informe_eipd(session, ctx["tenant_id"], ctx["user_id"], eipd_id)
