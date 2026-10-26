"""Plantillas sectoriales del RAT (RAT-02).

Mismos permisos que el RAT (RAT-01): consultan coordinador, implementador, DPO y administrador;
solo el coordinador carga una plantilla (el DPO no modifica el RAT: SoD, art. 48 LOPDP).
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.rat import ESCRITURA, LECTURA, get_rat_session
from app_core.audit import registrar_evento
from features.rat import rat_service

AUTO_REGISTRO = True
router = APIRouter(prefix="/rat", tags=["Registro de Actividades de Tratamiento (RAT)"])


class AplicarPlantillaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    codigos: list[str] = Field(min_length=1, description="Actividades de la plantilla que aplican")


@router.get("/plantillas")
async def listar_plantillas(ctx: dict = Depends(LECTURA), session: AsyncSession = Depends(get_rat_session)):
    """Plantillas que corresponden al sector de la organización (vacío si ninguna)."""
    return {"plantillas": await rat_service.plantillas_rat_disponibles(session, ctx["tenant_id"])}


@router.post("/plantillas/{sector}/aplicar")
async def aplicar_plantilla(
    sector: str,
    payload: AplicarPlantillaRequest,
    ctx: dict = Depends(ESCRITURA),
    session: AsyncSession = Depends(get_rat_session),
):
    """Carga en el RAT las actividades elegidas; las ya cargadas desde la plantilla no se duplican."""
    try:
        resultado = await rat_service.aplicar_plantilla_rat(
            session, ctx["tenant_id"], ctx["user_id"], sector, payload.codigos
        )
    except rat_service.PlantillaNoDisponible as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    await registrar_evento(
        session, ctx["tenant_id"], "rat_plantilla", sector, "rat_plantilla_aplicada", ctx["user_id"],
        {"creadas": resultado["creadas"], "omitidas": resultado["omitidas"]},
    )
    return resultado
