# ¤adpa ¤rbac-tenant
"""API de revisión documental; una autoridad explícita manda sobre el nombre del rol."""
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.rbac import get_context, require_role
from app_core.db.session import get_session
from features.biblioteca import biblioteca_service as bib

AUTO_REGISTRO = True
router = APIRouter(prefix="/biblioteca/revisiones", tags=["Biblioteca revisiones"])
Sesion = Annotated[AsyncSession, Depends(get_session)]
Miembro = Annotated[dict, Depends(get_context)]
Gestor = Annotated[dict, Depends(require_role("admin_organizacion", "coordinador"))]
Editor = Annotated[dict, Depends(require_role("admin_organizacion", "coordinador", "implementador"))]


@router.post("/autoridades", status_code=201)
async def delegar(entrada: bib.DelegarAutoridad, session: Sesion, ctx: Gestor):
    return {"id": await bib.delegar_autoridad(session, ctx["tenant_id"], ctx["user_id"], entrada)}


@router.post("/documentos/{documento_id}", response_model=bib.RevisionDocumental, status_code=201)
async def enviar(documento_id: str, entrada: bib.EnviarRevision, session: Sesion, ctx: Editor):
    return await bib.enviar_a_revision(session, ctx["tenant_id"], ctx["user_id"], documento_id, entrada)


@router.post("/documentos/{documento_id}/nueva", status_code=201)
async def nueva(documento_id: str, session: Sesion, ctx: Editor):
    return {"revision": await bib.abrir_nueva_revision(session, ctx["tenant_id"], ctx["user_id"], documento_id)}


@router.get("/{revision_id}", response_model=bib.RevisionDocumental)
async def obtener(revision_id: str, session: Sesion, ctx: Miembro):
    await bib.fijar_contexto_revision(session, ctx["tenant_id"], ctx["user_id"])
    return await bib.obtener_revision(session, ctx["tenant_id"], revision_id)


@router.post("/{revision_id}/devolver", response_model=bib.RevisionDocumental)
async def devolver(revision_id: str, entrada: bib.DictamenRevision, session: Sesion, ctx: Miembro):
    return await bib.devolver_revision(session, ctx["tenant_id"], ctx["user_id"], revision_id, entrada)


@router.post("/{revision_id}/aprobar", response_model=bib.RevisionDocumental)
async def aprobar(revision_id: str, entrada: bib.AprobarRevision, session: Sesion, ctx: Miembro):
    return await bib.aprobar_revision(session, ctx["tenant_id"], ctx["user_id"], revision_id, entrada)

