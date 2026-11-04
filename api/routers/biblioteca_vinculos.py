# ¤adpa ¤rbac-tenant
"""API BIB-402: vínculos de un documento con tratamientos, controles y tareas."""
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.rbac import get_context, require_role
from app_core.db.session import get_session
from app_core.pasillo.biblioteca import ReferenciasVinculos
from features.biblioteca import biblioteca_service as biblioteca

AUTO_REGISTRO = True
router = APIRouter(prefix="/biblioteca", tags=["Biblioteca vínculos"])
Sesion = Annotated[AsyncSession, Depends(get_session)]
Consulta = Annotated[dict, Depends(get_context)]
Gestion = Annotated[dict, Depends(require_role("implementador", "coordinador"))]


@router.get("/documentos/{documento_id}/vinculos", response_model=biblioteca.VinculosDocumento)
async def listar(documento_id: str, session: Sesion, ctx: Consulta):
    return await biblioteca.listar_vinculos(session, ctx["tenant_id"], ctx["user_id"], documento_id)


@router.put("/documentos/{documento_id}/vinculos", response_model=biblioteca.VinculosDocumento)
async def reemplazar(documento_id: str, entrada: biblioteca.EntradaVinculos, session: Sesion, ctx: Gestion):
    return await biblioteca.reemplazar_vinculos(
        session, ctx["tenant_id"], ctx["user_id"], documento_id, entrada, ReferenciasVinculos())


@router.get("/tratamientos/{tratamiento_id}/documentos", response_model=list[biblioteca.DocumentoVinculado])
async def documentos_de_tratamiento(tratamiento_id: str, session: Sesion, ctx: Consulta):
    return await biblioteca.documentos_de_tratamiento(session, ctx["tenant_id"], ctx["user_id"], tratamiento_id)
