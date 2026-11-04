# ¤adpa ¤rbac-tenant
"""API BIB-302: enlaces de revisiones documentales con acciones canónicas."""
from typing import Annotated
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from api.rbac import get_context, require_role
from app_core.db.session import get_session
from features.biblioteca import biblioteca_service as biblioteca
from features.roadmap import roadmap_service as roadmap

AUTO_REGISTRO = True
router = APIRouter(prefix="/biblioteca/documentos", tags=["Biblioteca enlaces"])
Sesion = Annotated[AsyncSession, Depends(get_session)]
Consulta = Annotated[dict, Depends(get_context)]
Gestion = Annotated[dict, Depends(require_role("admin_organizacion", "implementador", "coordinador"))]


@router.get("/{documento_id}/enlaces", response_model=list[biblioteca.EnlaceDocumento])
async def listar(documento_id: str, session: Sesion, ctx: Consulta):
    return await biblioteca.listar_enlaces(session, ctx["tenant_id"], ctx["user_id"], documento_id)


@router.get("/acciones/{accion_id}/documentos", response_model=list[biblioteca.EnlaceDocumento])
async def listar_por_accion(accion_id: str, session: Sesion, ctx: Consulta):
    return await biblioteca.listar_documentos_de_accion(
        session, ctx["tenant_id"], ctx["user_id"], accion_id, roadmap.obtener_accion_para_enlace)


@router.post("/{documento_id}/enlaces", status_code=status.HTTP_201_CREATED,
             response_model=biblioteca.EnlaceDocumento)
async def crear(documento_id: str, entrada: biblioteca.CrearEnlace, session: Sesion, ctx: Gestion):
    return await biblioteca.crear_enlace(
        session, ctx["tenant_id"], ctx["user_id"], documento_id, entrada, roadmap.obtener_accion_para_enlace)


@router.delete("/{documento_id}/enlaces/{enlace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar(documento_id: str, enlace_id: str, session: Sesion, ctx: Gestion):
    await biblioteca.eliminar_enlace(session, ctx["tenant_id"], ctx["user_id"], documento_id, enlace_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
