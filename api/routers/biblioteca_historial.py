# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Cronología y conservación de documentos; identidad y tenant salen de la sesión verificada."""
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import get_context, require_role
from app_core.db.session import get_session
from features.biblioteca import biblioteca_service as biblioteca

AUTO_REGISTRO = True
router = APIRouter(prefix="/biblioteca/documentos", tags=["Biblioteca historial"])
Sesion = Annotated[AsyncSession, Depends(get_session)]
Miembro = Annotated[dict, Depends(get_context)]
Gestor = Annotated[dict, Depends(require_role("admin_organizacion", "implementador", "coordinador"))]


@router.get("/{documento_id}/cronologia", response_model=list[biblioteca.EventoCronologia])
async def cronologia(documento_id: str, session: Sesion, ctx: Miembro):
    return await biblioteca.cronologia(session, ctx["tenant_id"], ctx["user_id"], documento_id)


@router.post("/{documento_id}/eventos", response_model=biblioteca.EventoCronologia, status_code=201)
async def evento(documento_id: str, entrada: biblioteca.RegistrarEvento, session: Sesion, ctx: Gestor):
    return await biblioteca.registrar_evento(session, ctx["tenant_id"], ctx["user_id"], documento_id, entrada)


@router.post("/{documento_id}/restauraciones", response_model=biblioteca.Documento)
async def restaurar(documento_id: str, entrada: biblioteca.RestaurarRevision, session: Sesion, ctx: Gestor):
    return await biblioteca.restaurar_revision(session, ctx["tenant_id"], ctx["user_id"], documento_id, entrada)


@router.get("/{documento_id}/conservacion", response_model=biblioteca.ConservacionDocumento)
async def conservacion(documento_id: str, session: Sesion, ctx: Miembro):
    return await biblioteca.obtener_conservacion(session, ctx["tenant_id"], ctx["user_id"], documento_id)


@router.put("/{documento_id}/conservacion", response_model=biblioteca.ConservacionDocumento)
async def cambiar_conservacion(documento_id: str, entrada: biblioteca.CambiarConservacion,
                               session: Sesion, ctx: Gestor):
    return await biblioteca.cambiar_conservacion(session, ctx["tenant_id"], ctx["user_id"], documento_id, entrada)
