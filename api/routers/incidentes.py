# ¤incidentes ¤rbac-tenant ¤seguridad
"""API de la bitácora de incidentes de seguridad (INC-01).

Registran los roles de la organización y consulta además el DPO (ver ROLES_REGISTRO y
ROLES_CONSULTA en la sala). Un incidente registrado no se edita ni se borra. Esta API no calcula
plazos legales: siguen aplazados por decisión del propietario (LEG-02).
"""
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from features.incidentes import incidentes_service

AUTO_REGISTRO = True
router = APIRouter(prefix="/incidentes", tags=["Incidentes y vulneraciones"])

_registro = require_role(*incidentes_service.ROLES_REGISTRO)
_consulta = require_role(*incidentes_service.ROLES_CONSULTA)


class IncidenteEntrada(BaseModel):
    """Lo que declara quien registra. Autoría, hora de registro, plazos y huellas los pone el
    servidor: si llegan en el cuerpo, se ignoran."""

    fecha_deteccion: datetime
    titulo: str = Field(min_length=1, max_length=200)
    descripcion: str = Field(default="", max_length=4000)
    severidad: Literal["Baja", "Media", "Alta", "Crítica"]
    afecta_datos_personales: bool
    categorias_datos: list[str] = Field(default_factory=list, max_length=20)
    medidas_inmediatas: str = Field(default="", max_length=4000)


def _a_salida(incidente: incidentes_service.Incidente) -> dict:
    return {
        "id": incidente.id,
        "secuencia": incidente.secuencia,
        "fecha_deteccion": incidente.fecha_deteccion.isoformat(),
        "titulo": incidente.titulo,
        "descripcion": incidente.descripcion,
        "severidad": incidente.severidad,
        "afecta_datos_personales": incidente.afecta_datos_personales,
        "categorias_datos": incidente.categorias_datos,
        "medidas_inmediatas": incidente.medidas_inmediatas,
        "registrado_por": incidente.registrado_por,
        "registrado_en": incidente.registrado_en.isoformat(),
        "huella_anterior": incidente.huella_anterior,
        "huella": incidente.huella,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def registrar(
    payload: IncidenteEntrada,
    ctx: dict = Depends(_registro),
    session: AsyncSession = Depends(get_session),
):
    try:
        incidente = await incidentes_service.registrar_incidente(
            session,
            ctx["tenant_id"],
            ctx["user_id"],
            fecha_deteccion=payload.fecha_deteccion,
            titulo=payload.titulo.strip(),
            descripcion=payload.descripcion.strip(),
            severidad=payload.severidad,
            afecta_datos_personales=payload.afecta_datos_personales,
            categorias_datos=[c.strip() for c in payload.categorias_datos if c.strip()],
            medidas_inmediatas=payload.medidas_inmediatas.strip(),
        )
    except incidentes_service.FechaDeteccionFutura as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    return _a_salida(incidente)


@router.get("")
async def bitacora(ctx: dict = Depends(_consulta), session: AsyncSession = Depends(get_session)):
    incidentes = await incidentes_service.listar_incidentes(session, ctx["tenant_id"], ctx["user_id"])
    alterado = incidentes_service.primer_incidente_alterado(incidentes)
    return {
        "incidentes": [_a_salida(i) for i in reversed(incidentes)],
        "cadena_integra": alterado is None,
        "primer_alterado": alterado.id if alterado else None,
    }
