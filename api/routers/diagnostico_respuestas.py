"""API de las respuestas del diagnóstico guardadas por organización (DIAG-01)."""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from features.diagnostico import diagnostico_service

AUTO_REGISTRO = True
router = APIRouter(prefix="/diagnostico", tags=["Diagnóstico"])

# Solo el DPO responde (DIAG-03, decisión del propietario del 2026-10-27); los demás consultan.
_escritura = require_role("dpo")
_lectura = require_role("implementador", "coordinador", "dpo", "admin_organizacion")


class RespuestaEntrada(BaseModel):
    pregunta_id: int = Field(ge=1)
    control: str = Field(min_length=1, max_length=300)
    dimension: str
    estado: Literal["Conforme", "Parcial", "No Conforme", "Pendiente"]
    nivel_evidencia: int = Field(ge=0, le=3)
    criticidad: int = Field(ge=1, le=5)
    es_critica: bool = False
    riesgo_base: int = Field(ge=1, le=10)


class RespuestasEntrada(BaseModel):
    respuestas: list[RespuestaEntrada] = Field(min_length=1)


@router.get("/respuestas")
async def get_respuestas(ctx: dict = Depends(_lectura), session: AsyncSession = Depends(get_session)):
    return {"respuestas": await diagnostico_service.listar_respuestas(session, ctx["tenant_id"], ctx["user_id"])}


@router.put("/respuestas")
async def put_respuestas(
    payload: RespuestasEntrada,
    ctx: dict = Depends(_escritura),
    session: AsyncSession = Depends(get_session),
):
    try:
        filas = await diagnostico_service.guardar_respuestas(
            session, ctx["tenant_id"], ctx["user_id"], [r.model_dump() for r in payload.respuestas]
        )
    except diagnostico_service.RespuestaFueraDeCatalogo as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    return {"respuestas": filas}
