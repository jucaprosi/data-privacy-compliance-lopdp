# ¤adpa
# ¤¤developer-architect
"""Capacidades editoriales propias (BIB-118). Solo lectura: la identidad sale de la sesión verificada y la
respuesta nunca es 403 por no tener capacidades; el menú «Administración editorial» se pinta con esto."""
from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from api.rbac import get_usuario_autenticado
from app_core.db.session import get_session
from features.biblioteca import biblioteca_service as biblioteca

AUTO_REGISTRO = True
router = APIRouter(prefix="/biblioteca/capacidades", tags=["Biblioteca capacidades"])
Sesion = Annotated[AsyncSession, Depends(get_session)]
Actor = Annotated[str, Depends(get_usuario_autenticado)]


# ¤adpa
class MisCapacidades(BaseModel):
    capacidades: list[str]


# ¤adpa
@router.get("/mias", response_model=MisCapacidades)
async def mias(session: Sesion, actor: Actor):
    return MisCapacidades(capacidades=sorted(await biblioteca.capacidades_propias(session, actor)))
