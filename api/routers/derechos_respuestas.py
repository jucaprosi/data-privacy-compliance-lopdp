# ¤evidencias ¤rbac-tenant
"""DER-01: verificación de identidad, modelos de respuesta y respuesta como evidencia.

Identidad y organización salen del token. El cuerpo de la respuesta se declara con `extra="forbid"`: el
cliente nunca manda hash, URL ni identificador de evidencia; el hash lo calcula el servidor. El DPO consulta
y no responde (decisión 1). Sin plazos: el semáforo llega con REG-01.
"""
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import get_context, require_role
from app_core.db.session import get_session
from app_core.pasillo import evidencias as pasillo_evidencias
from features.derechos_arco import derechos_arco_service as sala

AUTO_REGISTRO = True
router = APIRouter(prefix="/derechos", tags=["Derechos de los titulares"])

_verifica = require_role(*sala.ROLES_VERIFICAN)
_responde = require_role(*sala.ROLES_RESPONDEN)


class VerificarIdentidadEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metodo: Literal["documento", "correo", "presencial"]


class RespuestaEntrada(BaseModel):
    """Solo modelo, variables y resultado: cualquier otro campo (hash, URL de evidencia) da 422."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    modelo_id: str = Field(min_length=1, max_length=64)
    variables: dict[str, str] = Field(default_factory=dict)
    resultado: Literal["concedido", "denegado", "parcial"]


@router.post("/solicitudes/{solicitud_id}/verificar-identidad")
async def verificar_identidad(
    solicitud_id: str,
    entrada: VerificarIdentidadEntrada,
    ctx: dict = Depends(_verifica),
    session: AsyncSession = Depends(get_session),
):
    return await sala.verificar_identidad(session, ctx["tenant_id"], ctx["user_id"], solicitud_id, entrada.metodo)


@router.get("/solicitudes/{solicitud_id}")
async def solicitud(
    solicitud_id: str,
    ctx: dict = Depends(get_context),
    session: AsyncSession = Depends(get_session),
):
    return await sala.obtener_solicitud(session, ctx["tenant_id"], solicitud_id)


@router.get("/modelos")
async def modelos(
    derecho: str | None = None,
    resultado: Literal["concedido", "denegado", "parcial"] | None = None,
    ctx: dict = Depends(get_context),
    session: AsyncSession = Depends(get_session),
):
    return {"modelos": await sala.listar_modelos(session, ctx["tenant_id"], derecho, resultado)}


@router.post("/solicitudes/{solicitud_id}/respuesta", status_code=201)
async def responder(
    solicitud_id: str,
    entrada: RespuestaEntrada,
    ctx: dict = Depends(_responde),
    session: AsyncSession = Depends(get_session),
):
    return await sala.responder(
        session, ctx["tenant_id"], ctx["user_id"], solicitud_id,
        entrada.modelo_id, entrada.variables, entrada.resultado,
        pasillo_evidencias.custodiar_documento_generado,
    )
