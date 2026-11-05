# ¤adpa ¤rbac-tenant
"""API BIB-208: mapas de captura/salida de las ocho fichas iniciales, evaluación e instantánea PLA-01.

Evaluar no guarda nada. RAT-01 se ancla en el RAT por su compuerta y PLA-01 se lee del plan canónico por
la suya; ninguna de las dos se escribe desde aquí.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from api.rbac import get_context, require_role
from app_core.db.session import get_session
from features.biblioteca import biblioteca_service as biblioteca
from features.rat import rat_service as rat
from features.roadmap import roadmap_service as roadmap

AUTO_REGISTRO = True
router = APIRouter(prefix="/biblioteca/fichas-iniciales", tags=["Biblioteca fichas iniciales"])
Sesion = Annotated[AsyncSession, Depends(get_session)]
Consulta = Annotated[dict, Depends(get_context)]
Gestion = Annotated[dict, Depends(require_role("admin_organizacion", "implementador", "coordinador"))]


@router.get("", response_model=list[biblioteca.MapaPublico])
async def listar(ctx: Consulta):
    return biblioteca.listar_fichas_iniciales()


@router.get("/{codigo}", response_model=biblioteca.MapaPublico)
async def obtener(codigo: str, ctx: Consulta):
    return biblioteca.obtener_ficha_inicial(codigo)


@router.post("/{codigo}/evaluar", response_model=biblioteca.ResultadoFicha | biblioteca.ResultadoRAT)
async def evaluar(codigo: str, entrada: biblioteca.EntradaFicha, session: Sesion, ctx: Gestion):
    return await biblioteca.evaluar_ficha_inicial(
        session, ctx["tenant_id"], ctx["user_id"], codigo, entrada, rat.actividades_para_biblioteca)


@router.get("/PLA-01/instantanea/{roadmap_id}", response_model=biblioteca.InstantaneaPlan)
async def instantanea(roadmap_id: str, session: Sesion, ctx: Gestion,
                      fecha_corte: Annotated[str | None, Query(max_length=10)] = None):
    return await biblioteca.instantanea_plan(
        session, ctx["tenant_id"], roadmap_id, fecha_corte, roadmap.acciones_para_instantanea)
