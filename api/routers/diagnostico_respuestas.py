"""API de las respuestas del diagnóstico guardadas por organización (DIAG-01)."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import get_context, require_role
from app_core.db.session import get_session
from features.diagnostico import diagnostico_service

AUTO_REGISTRO = True
router = APIRouter(prefix="/diagnostico", tags=["Diagnóstico"])



async def _escritura(ctx: dict = Depends(get_context)) -> dict:
    """DIAG-07 (R1 y R4): guarda cualquier rol vigente salvo el `dpo`, que revisa y sella pero no responde.

    La decisión por dimensión (administrador en todas, encargado solo en las suyas) la toma el motor.
    """
    if ctx["role"] == "dpo":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "El DPO revisa y sella el diagnóstico; no responde.")
    return ctx


_lectura = require_role("implementador", "coordinador", "dpo", "admin_organizacion")


class RespuestaEntrada(BaseModel):
    """Un `estado` en el cuerpo se rechaza: lo deriva el servidor del nivel asignado (DIAG-08)."""

    model_config = ConfigDict(extra="forbid")

    pregunta_id: int = Field(ge=1)
    control: str = Field(min_length=1, max_length=300)
    dimension: str
    nivel_asignado: int = Field(ge=1, le=5)
    nivel_evidencia: int = Field(ge=0, le=4)
    criticidad: int = Field(ge=1, le=5)
    es_critica: bool = False
    riesgo_base: int = Field(ge=1, le=10)
    # === DIAG-05 ===
    # ¤diagnostico-no-aplica La justificación la valida el servidor (422); el autor sale del token.
    no_aplica: bool = False
    justificacion_no_aplica: str | None = Field(default=None, max_length=2000)
    # === fin DIAG-05 ===


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
    respuestas = [r.model_dump() for r in payload.respuestas]
    await diagnostico_service.exigir_puede_escribir(
        session, ctx["tenant_id"], ctx["user_id"], ctx["role"], {r["dimension"] for r in respuestas}
    )
    try:
        filas = await diagnostico_service.guardar_respuestas(
            session, ctx["tenant_id"], ctx["user_id"], respuestas
        )
    except diagnostico_service.RespuestaFueraDeCatalogo as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    # R2: guardar una pregunta objetada resuelve su objeción abierta; el historial se conserva.
    await diagnostico_service.resolver_por_guardado(
        session, ctx["tenant_id"], ctx["user_id"], [r["pregunta_id"] for r in respuestas]
    )
    return {"respuestas": filas}


# === ADPA-05 ===
# ¤adpa Los códigos de error del diagnóstico viven en features/diagnostico/domain/errores.py (vía su compuerta).
# === fin ADPA-05 ===
