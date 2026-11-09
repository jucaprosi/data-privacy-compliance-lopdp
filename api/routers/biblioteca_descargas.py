# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Descarga controlada de plantillas Word/Excel (BIB-104).

El servidor verifica actor, tenant, rol y estado publicado antes de emitir enlaces
temporales firmados o emitir el streaming del archivo maestro editable.
"""
import io
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from api.rbac import get_context
from app_core.db.session import get_session
from features.biblioteca import biblioteca_service as biblioteca

AUTO_REGISTRO = True
router = APIRouter(prefix="/biblioteca", tags=["Biblioteca descargas"])
Sesion = Annotated[AsyncSession, Depends(get_session)]
Contexto = Annotated[dict, Depends(get_context)]


# ¤adpa ¤rbac-tenant
@router.post("/plantillas/{plantilla_id}/descargar", response_model=biblioteca.EnlaceDescarga)
async def solicitar_descarga(plantilla_id: str, session: Sesion, ctx: Contexto):
    """Genera un enlace temporal firmado para la descarga segura de la plantilla."""
    return await biblioteca.generar_enlace_descarga(
        session=session,
        tenant_id=ctx["tenant_id"],
        usuario_id=ctx["user_id"],
        plantilla_id=plantilla_id,
    )


# ¤adpa ¤rbac-tenant ¤seguridad
@router.get("/descargas/{plantilla_id}/archivo")
async def descargar_con_token(
    plantilla_id: str,
    session: Sesion,
    ctx: Contexto,
    token: Annotated[str | None, Query()] = None,
):
    """Descarga el archivo maestro. SEC-19: primero la sesión; el token solo confirma que es de quien lo usa.

    El tenant, el usuario y la RLS salen siempre de la sesión, nunca del token.
    """
    archivo_bytes, _, mime, cabeceras = await biblioteca.ejecutar_descarga(
        session=session,
        tenant_id=ctx["tenant_id"],
        usuario_id=ctx["user_id"],
        plantilla_id=plantilla_id,
        token=token,
    )

    return StreamingResponse(
        io.BytesIO(archivo_bytes),
        media_type=mime,
        headers=cabeceras,
    )


# ¤adpa ¤rbac-tenant
@router.get("/plantillas/{plantilla_id}/descargar")
async def descargar_directo(plantilla_id: str, session: Sesion, ctx: Contexto):
    """Descarga directa del archivo maestro mediante cabeceras de sesión."""
    archivo_bytes, _, mime, cabeceras = await biblioteca.ejecutar_descarga(
        session=session,
        tenant_id=ctx["tenant_id"],
        usuario_id=ctx["user_id"],
        plantilla_id=plantilla_id,
    )

    return StreamingResponse(
        io.BytesIO(archivo_bytes),
        media_type=mime,
        headers=cabeceras,
    )
