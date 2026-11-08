# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Documentos externos del cliente (BIB-106). La organización sale de la sesión verificada; la reserva es
de quien la pidió. El archivo se envía como cuerpo binario y el servidor corta la lectura al superar el tope."""
from typing import Annotated
from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from api.rbac import get_context, require_role
from app_core.db.session import get_session
from app_core.errors import ErrorNegocio
from features.biblioteca import biblioteca_service as biblioteca

AUTO_REGISTRO = True
TOPE = 10 * 1024 * 1024
router = APIRouter(prefix="/biblioteca/cargas", tags=["Biblioteca cargas externas"])
Sesion = Annotated[AsyncSession, Depends(get_session)]
Miembro = Annotated[dict, Depends(get_context)]
Redactor = Annotated[dict, Depends(require_role("admin_organizacion", "implementador", "coordinador"))]


# ¤adpa
async def _cuerpo(request: Request) -> bytes:
    partes, total = [], 0
    async for trozo in request.stream():
        total += len(trozo)
        if total > TOPE:
            raise ErrorNegocio("BIB_CARGA_TAMANO_INVALIDO")
        partes.append(trozo)
    return b"".join(partes)


# ¤adpa
@router.post("", status_code=201, response_model=biblioteca.Carga)
async def reservar(entrada: biblioteca.ReservarCarga, session: Sesion, ctx: Redactor):
    return await biblioteca.reservar_carga(session, ctx["tenant_id"], ctx["user_id"], entrada)


# ¤adpa
@router.get("", response_model=list[biblioteca.Carga])
async def listar(documento_id: str, session: Sesion, ctx: Miembro):
    return await biblioteca.listar_cargas(session, ctx["tenant_id"], ctx["user_id"], documento_id)


# ¤adpa
@router.get("/{carga_id}", response_model=biblioteca.Carga)
async def obtener(carga_id: str, session: Sesion, ctx: Miembro):
    return await biblioteca.obtener_carga(session, ctx["tenant_id"], ctx["user_id"], carga_id)


# ¤adpa
@router.put("/{carga_id}/archivo", response_model=biblioteca.Carga)
async def subir(carga_id: str, request: Request, session: Sesion, ctx: Redactor):
    contenido = await _cuerpo(request)
    return await biblioteca.subir_archivo(session, ctx["tenant_id"], ctx["user_id"], carga_id, contenido)


# ¤adpa
@router.post("/{carga_id}/finalizar", response_model=biblioteca.Documento)
async def finalizar(carga_id: str, session: Sesion, ctx: Redactor):
    return await biblioteca.finalizar_carga(session, ctx["tenant_id"], ctx["user_id"], carga_id)


# ¤adpa
@router.get("/{carga_id}/archivo")
async def descargar(carga_id: str, session: Sesion, ctx: Miembro):
    contenido, nombre, mime = await biblioteca.descargar_carga(session, ctx["tenant_id"], ctx["user_id"], carga_id)
    return Response(content=contenido, media_type=mime, headers=biblioteca.cabeceras_descarga(nombre, len(contenido), mime))
