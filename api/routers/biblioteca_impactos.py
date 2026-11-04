# ¤adpa ¤rbac-tenant
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from api.rbac import get_context, get_usuario_autenticado, require_role
from app_core.avisos_impacto import construir_aviso_impacto
from app_core.db.session import get_session
from features.biblioteca import biblioteca_service as biblioteca

AUTO_REGISTRO = True
router = APIRouter(prefix="/biblioteca/impactos", tags=["Biblioteca impactos"])
Sesion = Annotated[AsyncSession, Depends(get_session)]
Actor = Annotated[str, Depends(get_usuario_autenticado)]
Miembro = Annotated[dict, Depends(get_context)]
Decisor = Annotated[dict, Depends(require_role("admin_organizacion", "coordinador", "dpo"))]


class Decision(BaseModel):
    decision: Literal["actualizar", "no_aplica", "pendiente"]
    motivo: str = Field(min_length=1, max_length=2000)


class Recepcion(BaseModel):
    recibido: bool
    error: str | None = Field(default=None, max_length=500)


@router.post("/versiones/{version_id}", status_code=201)
async def analizar(version_id: str, session: Sesion, actor: Actor):
    return await biblioteca.crear_analisis(session, actor, version_id)


@router.post("/{analisis_id}/avisos", status_code=202)
async def avisar(analisis_id: str, session: Sesion, actor: Actor,
                 app_base_url: str = Query(pattern=r"^https?://[^/]+")):
    return await biblioteca.preparar_avisos(session, actor, analisis_id, app_base_url, construir_aviso_impacto)


@router.get("")
async def listar(session: Sesion, ctx: Miembro):
    return await biblioteca.listar_organizacion(session, ctx["tenant_id"])


@router.put("/{expediente_id}/decision")
async def decidir(expediente_id: str, entrada: Decision, session: Sesion, ctx: Decisor):
    return await biblioteca.decidir(session, ctx["tenant_id"], ctx["user_id"], expediente_id,
                                    entrada.decision, entrada.motivo)


@router.post("/avisos/{aviso_id}/recepcion")
async def recepcion(aviso_id: str, entrada: Recepcion, session: Sesion, ctx: Miembro):
    return await biblioteca.registrar_intento(session, ctx["tenant_id"], aviso_id,
                                              entrada.recibido, entrada.error)
