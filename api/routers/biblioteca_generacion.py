# ¤adpa
# ¤¤developer-architect
# ¤rbac-tenant
"""Generación de Word y Excel desde un borrador (BIB-205). Tenant e identidad salen de la sesión.

Reutiliza las fuentes de solo lectura de BIB-201 (ORG-14, designaciones y RAT), así que el archivo usa los
mismos valores que muestra el editor. Generar no aprueba el documento ni cierra acciones.
"""
from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from api.rbac import require_role
from api.routers.biblioteca_borradores import EDITORES, FUENTES
from app_core.db.session import get_session
from features.biblioteca import biblioteca_service as biblioteca

AUTO_REGISTRO = True
router = APIRouter(prefix="/biblioteca/generaciones", tags=["Biblioteca generación"])
Sesion = Annotated[AsyncSession, Depends(get_session)]


# ¤adpa
@router.post("/borradores/{borrador_id}", status_code=201, response_model=biblioteca.Generacion)
async def generar(borrador_id: str, pedido: biblioteca.PedirGeneracion, session: Sesion,
                  ctx: dict = Depends(require_role(*EDITORES))):
    return await biblioteca.generar_documento(session, FUENTES, ctx["tenant_id"], ctx["user_id"], borrador_id, pedido)


# ¤adpa
@router.get("/borradores/{borrador_id}", response_model=list[biblioteca.Generacion])
async def listar(borrador_id: str, session: Sesion, ctx: dict = Depends(require_role(*EDITORES))):
    return await biblioteca.listar_generaciones(session, ctx["tenant_id"], ctx["user_id"], borrador_id)


# ¤adpa
@router.get("/borradores/{borrador_id}/guia", response_model=biblioteca.Guia)
async def guia(borrador_id: str, session: Sesion, ctx: dict = Depends(require_role(*EDITORES))):
    return await biblioteca.guia_de_borrador(session, ctx["tenant_id"], ctx["user_id"], borrador_id)


# ¤adpa
@router.get("/{generacion_id}/archivo")
async def archivo(generacion_id: str, session: Sesion, ctx: dict = Depends(require_role(*EDITORES))):
    datos, mime, nombre, sha = await biblioteca.archivo_generado(session, ctx["tenant_id"], ctx["user_id"], generacion_id)
    return Response(content=datos, media_type=mime, headers={
        "Content-Disposition": f'attachment; filename="{nombre}"', "X-Content-SHA256": sha,
        "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})
