# ¤adpa ¤rbac-tenant
"""API BIB-305: indicadores verificables de Biblioteca y acceso a sus registros de origen.

La organización y el usuario salen de la sesión autenticada (get_context); la RLS filtra las filas.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from api.rbac import get_context
from app_core.db.session import get_session
from features.biblioteca import biblioteca_service as biblioteca

AUTO_REGISTRO = True
router = APIRouter(prefix="/biblioteca/indicadores", tags=["Biblioteca indicadores"])
Sesion = Annotated[AsyncSession, Depends(get_session)]
Miembro = Annotated[dict, Depends(get_context)]


@router.get("", response_model=biblioteca.Indicadores)
async def indicadores(session: Sesion, ctx: Miembro):
    return await biblioteca.calcular_indicadores(session, ctx["tenant_id"], ctx["user_id"])


@router.get("/{clave}/registros", response_model=biblioteca.RegistrosIndicador)
async def registros(clave: str, session: Sesion, ctx: Miembro,
                    categoria: str | None = Query(default=None, max_length=40)):
    return await biblioteca.registros_de_indicador(session, ctx["tenant_id"], ctx["user_id"], clave, categoria)
