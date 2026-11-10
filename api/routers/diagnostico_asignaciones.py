"""API de la asignación de dominios del assessment a encargados del diagnóstico (DIAG-04). ¤diagnostico-asignacion"""
from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from features.diagnostico import diagnostico_service

AUTO_REGISTRO = True
router = APIRouter(prefix="/diagnostico", tags=["Diagnóstico"])

_DIMENSION = r"^D(0[1-9]|10)$"
_asigna = require_role("admin_organizacion")
_lectura = require_role("implementador", "coordinador", "dpo", "admin_organizacion", "responsable_area")
_historial = require_role("implementador", "coordinador", "dpo")


class AsignacionEntrada(BaseModel):
    """Identidad y organización salen del token; el cuerpo solo nombra al encargado (nulo desasigna)."""

    model_config = ConfigDict(extra="forbid")

    responsable_user_id: str | None


@router.get("/asignaciones")
async def get_asignaciones(ctx: dict = Depends(_lectura), session: AsyncSession = Depends(get_session)):
    return {"asignaciones": await diagnostico_service.listar_asignaciones(session, ctx["tenant_id"], ctx["user_id"])}


@router.get("/asignaciones/historial")
async def get_historial(
    dimension: str | None = Query(default=None, pattern=_DIMENSION),
    ctx: dict = Depends(_historial),
    session: AsyncSession = Depends(get_session),
):
    return {
        "historial": await diagnostico_service.historial_asignaciones(
            session, ctx["tenant_id"], ctx["user_id"], dimension
        )
    }


@router.put("/asignaciones/{dimension}")
async def put_asignacion(
    payload: AsignacionEntrada,
    dimension: str = Path(pattern=_DIMENSION),
    ctx: dict = Depends(_asigna),
    session: AsyncSession = Depends(get_session),
):
    return await diagnostico_service.asignar_dominio(
        session, ctx["tenant_id"], ctx["user_id"], dimension, payload.responsable_user_id
    )
