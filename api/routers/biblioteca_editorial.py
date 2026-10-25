# ¤adpa
# ¤¤developer-architect
"""API editorial global, sin tenant ficticio ni permisos derivados de X-Role."""
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.rbac import get_usuario_autenticado
from app_core.db.session import get_session
from features.biblioteca import biblioteca_service as biblioteca

AUTO_REGISTRO = True
router = APIRouter(prefix="/biblioteca/editorial", tags=["Biblioteca editorial"])
Sesion = Annotated[AsyncSession, Depends(get_session)]
Actor = Annotated[str, Depends(get_usuario_autenticado)]


# ¤adpa
@router.get("", response_model=biblioteca.VistaEditorial)
async def listar(session: Sesion, actor: Actor):
    return await biblioteca.listar(session, actor)


# ¤adpa
@router.post("/versiones", status_code=201, response_model=biblioteca.VersionMaestra)
async def crear(entrada: biblioteca.CrearVersion, session: Sesion, actor: Actor):
    return await biblioteca.crear(session, actor, entrada)


# ¤adpa
@router.put("/versiones/{identificador}/ficha", response_model=biblioteca.VersionMaestra)
async def editar(identificador: str, entrada: biblioteca.EditarFicha, session: Sesion, actor: Actor):
    return await biblioteca.editar(session, actor, identificador, entrada)


# ¤adpa
@router.put("/versiones/{identificador}/archivo", response_model=biblioteca.VersionMaestra)
async def cargar(identificador: str, entrada: biblioteca.ArchivoMaestro, session: Sesion, actor: Actor):
    return await biblioteca.cargar(session, actor, identificador, entrada)


# ¤adpa
@router.post("/versiones/{identificador}/revisiones", response_model=biblioteca.VersionMaestra, status_code=201)
async def revisar(identificador: str, entrada: biblioteca.Dictamen, session: Sesion, actor: Actor):
    return await biblioteca.revisar(session, actor, identificador, entrada)


# ¤adpa
@router.post("/versiones/{identificador}/publicar", response_model=biblioteca.VersionMaestra)
async def publicar(identificador: str, entrada: biblioteca.Transicion, session: Sesion, actor: Actor):
    return await biblioteca.publicar(session, actor, identificador, entrada)


# ¤adpa
@router.post("/versiones/{identificador}/retirar", response_model=biblioteca.VersionMaestra)
async def retirar(identificador: str, entrada: biblioteca.Transicion, session: Sesion, actor: Actor):
    return await biblioteca.retirar(session, actor, identificador, entrada)


# ¤adpa
@router.get("/versiones/{identificador}/historial", response_model=list[biblioteca.EventoEditorial])
async def historial(identificador: str, session: Sesion, actor: Actor):
    return await biblioteca.historial(session, actor, identificador)
