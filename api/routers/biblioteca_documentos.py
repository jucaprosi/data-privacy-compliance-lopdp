# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Documentos de la organización. La organización sale de la sesión verificada (membresía activa en
X-Tenant-ID), nunca del cuerpo ni de la URL; el id de un documento ajeno responde 404."""
from datetime import date
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.rbac import get_context, require_role
from app_core.db.session import get_session
from features.biblioteca import biblioteca_service as biblioteca

AUTO_REGISTRO = True
router = APIRouter(prefix="/biblioteca/documentos", tags=["Biblioteca documentos"])
Sesion = Annotated[AsyncSession, Depends(get_session)]
Miembro = Annotated[dict, Depends(get_context)]
# Quien redacta: roles transversales que ejecutan la implementación. Aprobar es de BIB-301.
Redactor = Annotated[dict, Depends(require_role("admin_organizacion", "implementador", "coordinador"))]


# ¤adpa
@router.post("", status_code=201, response_model=biblioteca.Documento)
async def crear(entrada: biblioteca.CrearDocumento, session: Sesion, ctx: Redactor):
    return await biblioteca.crear_documento(session, ctx["tenant_id"], ctx["user_id"], entrada)


# ¤adpa
@router.get("", response_model=list[biblioteca.DocumentoResumen])
async def listar(
    session: Sesion, ctx: Miembro, estado: str | None = None, origen: str | None = None, codigo: str | None = None,
    autor: str | None = None, desde: date | None = None, hasta: date | None = None,
):
    return await biblioteca.listar_documentos(
        session, ctx["tenant_id"], ctx["user_id"], estado=estado, origen=origen, codigo=codigo, autor=autor,
        desde=desde, hasta=hasta)


# ¤adpa
# Declarada antes de `/{documento_id}` para que "pendientes" no se tome por un id.
@router.get("/pendientes", response_model=biblioteca.Pendientes)
async def pendientes(session: Sesion, ctx: Miembro):
    return await biblioteca.pendientes(session, ctx["tenant_id"], ctx["user_id"])


# ¤adpa
@router.get("/{documento_id}", response_model=biblioteca.Documento)
async def obtener(documento_id: str, session: Sesion, ctx: Miembro):
    return await biblioteca.obtener_documento(session, ctx["tenant_id"], ctx["user_id"], documento_id)


# ¤adpa
@router.get("/{documento_id}/historial", response_model=list[biblioteca.EventoHistorial])
async def historial(documento_id: str, session: Sesion, ctx: Miembro):
    return await biblioteca.historial_documento(session, ctx["tenant_id"], ctx["user_id"], documento_id)


# ¤adpa
@router.patch("/{documento_id}", response_model=biblioteca.Documento)
async def cambiar(documento_id: str, entrada: biblioteca.CambiarDocumento, session: Sesion, ctx: Redactor):
    return await biblioteca.cambiar_documento(session, ctx["tenant_id"], ctx["user_id"], documento_id, entrada)
