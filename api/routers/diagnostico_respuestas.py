"""API de respuestas persistidas del diagnóstico."""
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from api.rbac import get_context, require_role
from app_core.db.session import get_session
from features.diagnostico.services.respuestas_engine import guardar_respuestas, listar_respuestas

AUTO_REGISTRO = True
router = APIRouter(prefix="/diagnostico", tags=["Diagnóstico"])

class RespuestaEntrada(BaseModel):
    pregunta_id: int = Field(ge=1)
    control_ref: str
    dimension: str
    estado: Literal["Conforme", "Parcial", "No Conforme", "Pendiente"]
    nivel_evidencia: int = Field(ge=0, le=3)
    criticidad: int = Field(ge=1, le=5)

class RespuestasEntrada(BaseModel):
    respuestas: list[RespuestaEntrada]

@router.get("/respuestas")
async def get_respuestas(ctx: dict = Depends(get_context), session: AsyncSession = Depends(get_session)):
    return {"respuestas": await listar_respuestas(session, ctx["tenant_id"], ctx["user_id"])}

@router.put("/respuestas")
async def put_respuestas(payload: RespuestasEntrada, ctx: dict = Depends(require_role("implementador", "coordinador")), session: AsyncSession = Depends(get_session)):
    try:
        rows = await guardar_respuestas(session, ctx["tenant_id"], ctx["user_id"], [item.model_dump() for item in payload.respuestas])
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"respuestas": rows}
