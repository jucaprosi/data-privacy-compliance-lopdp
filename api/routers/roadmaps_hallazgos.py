# ¤roadmap ¤hallazgos ¤rbac-tenant
"""Hallazgos con origen y su conversión en tareas del plan de acción único (RM-21).

Contrato: governance/especificaciones/RM-21.md §2. Convierte y registra quien gestiona la hoja de ruta
(`implementador`); el `dpo` consulta y no convierte (ORG-13, D-2). Organización y autor salen del
contexto autenticado; el cuerpo no fija organización, autor, estado ni fechas.
"""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from features.roadmap import roadmap_service

AUTO_REGISTRO = True
router = APIRouter(prefix="/roadmaps", tags=["Hoja de Ruta - Hallazgos"])

ROLES_CONSULTA = ("implementador", "coordinador", "dpo", "admin_organizacion")
ROLES_GESTION = ("implementador",)

_consulta = require_role(*ROLES_CONSULTA)
_gestion = require_role(*ROLES_GESTION)

FiltroEstado = Optional[Literal["abierto", "en_tratamiento", "cerrado"]]
FiltroOrigen = Optional[
    Literal["diagnostico", "auditoria", "eipd", "incidente", "tercero", "control_periodico", "rat"]
]


@router.get("/hallazgos")
async def listar(
    estado: FiltroEstado = None,
    origen: FiltroOrigen = None,
    ctx: dict = Depends(_consulta),
    session: AsyncSession = Depends(get_session),
):
    hallazgos = await roadmap_service.listar_hallazgos(
        session, ctx["tenant_id"], ctx["user_id"], estado=estado, origen=origen
    )
    return {"hallazgos": [h.a_dict() for h in hallazgos]}


@router.post("/hallazgos/desde-diagnostico", status_code=status.HTTP_201_CREATED)
async def registrar_desde_diagnostico(
    ctx: dict = Depends(_gestion),
    session: AsyncSession = Depends(get_session),
):
    resultado = await roadmap_service.registrar_desde_diagnostico(session, ctx["tenant_id"], ctx["user_id"])
    return {"creados": resultado.creados, "existentes": resultado.existentes}


@router.post("/{roadmap_id}/hallazgos/convertir", status_code=status.HTTP_201_CREATED)
async def convertir(
    roadmap_id: str,
    payload: roadmap_service.ConvertirHallazgosEntrada,
    ctx: dict = Depends(_gestion),
    session: AsyncSession = Depends(get_session),
):
    resultado = await roadmap_service.crear_tareas_desde_hallazgos(
        session, ctx["tenant_id"], ctx["user_id"], roadmap_id, payload.wave_id, payload.hallazgo_ids
    )
    return {"tareas": resultado.tareas, "omitidos": resultado.omitidos}
