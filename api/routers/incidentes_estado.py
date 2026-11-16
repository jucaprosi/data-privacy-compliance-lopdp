# ¤incidentes ¤rbac-tenant ¤seguridad
"""Cierre y reapertura de incidentes (INC-03).

Cambian el estado los mismos roles que registran (ROLES_REGISTRO); el DPO consulta y no lo cambia
(art. 49, ORG-01). El estado es un evento que se agrega: el incidente y su huella no se tocan. Esta
API no calcula ni exige plazos para cerrar (REG-01). Identidad y organización salen del token.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import get_session
from app_core.errors import ErrorNegocio
from api.rbac import require_role
from features.incidentes import incidentes_service

AUTO_REGISTRO = True
router = APIRouter(prefix="/incidentes", tags=["Incidentes y vulneraciones"])

_cambia_estado = require_role(*incidentes_service.ROLES_REGISTRO)


class CambioEstadoEntrada(BaseModel):
    """Solo el motivo: autoría, hora y decisión de notificar las pone el servidor."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    motivo: str = Field(min_length=incidentes_service.MOTIVO_MINIMO, max_length=2000)


async def _aplicar(accion, incidente_id: str, payload: CambioEstadoEntrada, ctx: dict, session: AsyncSession) -> dict:
    try:
        estado = await accion(session, ctx["tenant_id"], ctx["user_id"], incidente_id, payload.motivo)
    except incidentes_service.IncidenteNoEncontrado as exc:
        raise ErrorNegocio("INCIDENTE_NO_ENCONTRADO") from exc
    except incidentes_service.TransicionInvalida as exc:
        raise ErrorNegocio(exc.codigo) from exc
    return {"id": incidente_id, **estado.a_salida()}


@router.post("/{incidente_id}/cerrar")
async def cerrar(
    incidente_id: str,
    payload: CambioEstadoEntrada,
    ctx: dict = Depends(_cambia_estado),
    session: AsyncSession = Depends(get_session),
):
    return await _aplicar(incidentes_service.cerrar_incidente, incidente_id, payload, ctx, session)


@router.post("/{incidente_id}/reabrir")
async def reabrir(
    incidente_id: str,
    payload: CambioEstadoEntrada,
    ctx: dict = Depends(_cambia_estado),
    session: AsyncSession = Depends(get_session),
):
    return await _aplicar(incidentes_service.reabrir_incidente, incidente_id, payload, ctx, session)
