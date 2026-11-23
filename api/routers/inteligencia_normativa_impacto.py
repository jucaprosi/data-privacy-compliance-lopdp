# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤inteligencia-normativa ¤copiloto-ia ¤dpo-independencia ¤seguridad
"""Análisis de impacto de una resolución (NORM-03), bajo /api/v1/normativa.

Pide el análisis la persona administradora o el DPO de la organización; lo acepta o rechaza solo el DPO (R3).
La organización y la persona salen del contexto autenticado, nunca del cuerpo. Una propuesta de la IA no cambia
nada de la organización hasta que el DPO la acepta (R1).
"""
from __future__ import annotations

import uuid
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from features.inteligencia_normativa import inteligencia_normativa_service as svc

errores = svc.errores
AUTO_REGISTRO = True
PREFIJO = "/api/v1"

router = APIRouter(prefix="/normativa", tags=["Impacto normativo (NORM-03)"])

ROLES_PEDIDO = ("dpo", "admin_organizacion")
ROLES_LECTURA = ("dpo", "admin_organizacion", "coordinador", "implementador", "auditor")

_pide = require_role(*ROLES_PEDIDO)
_lee = require_role(*ROLES_LECTURA)
_decide = require_role("dpo")

_ESTADOS_HTTP = {
    errores.NORMATIVA_RESOLUCION_NO_ENCONTRADA: status.HTTP_404_NOT_FOUND,
    errores.NORMATIVA_IMPACTO_NO_ENCONTRADO: status.HTTP_404_NOT_FOUND,
    errores.NORMATIVA_IMPACTO_YA_DECIDIDO: status.HTTP_409_CONFLICT,
    errores.NORMATIVA_IMPACTO_DECISION_INVALIDA: status.HTTP_422_UNPROCESSABLE_ENTITY,
    errores.NORMATIVA_IMPACTO_NOTA_OBLIGATORIA: status.HTTP_422_UNPROCESSABLE_ENTITY,
    errores.NORMATIVA_IMPACTO_SIN_TEXTO: status.HTTP_422_UNPROCESSABLE_ENTITY,
    errores.NORMATIVA_IMPACTO_IA_NO_DISPONIBLE: status.HTTP_503_SERVICE_UNAVAILABLE,
    errores.NORMATIVA_ORIGINAL_NO_DISPONIBLE: status.HTTP_503_SERVICE_UNAVAILABLE,
}


def _http(exc: svc.ErrorNormativo) -> HTTPException:
    """Solo el código estable; nunca texto de la resolución ni del modelo."""
    return HTTPException(_ESTADOS_HTTP.get(exc.codigo, status.HTTP_500_INTERNAL_SERVER_ERROR), {"codigo": exc.codigo})


def _uuid(valor: Optional[str]) -> Optional[str]:
    if valor is None:
        return None
    try:
        return str(uuid.UUID(valor))
    except ValueError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, {"codigo": "NORMATIVA_ID_INVALIDO"}) from None


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["aceptar", "rechazar"]
    nota: str = Field(default="", max_length=4000)


@router.post("/resoluciones/{id_resolucion}/impacto", status_code=status.HTTP_202_ACCEPTED)
async def pedir_impacto(
    id_resolucion: str, ctx: dict = Depends(_pide), session: AsyncSession = Depends(get_session),
) -> dict:
    try:
        analisis = await svc.analizar_impacto(session, ctx["tenant_id"], ctx["user_id"], _uuid(id_resolucion))
    except svc.ErrorNormativo as exc:
        raise _http(exc) from exc
    return analisis.model_dump(mode="json")


@router.get("/impacto")
async def listar_impacto(
    resolucion_id: Optional[str] = Query(None, max_length=64),
    ctx: dict = Depends(_lee), session: AsyncSession = Depends(get_session),
) -> list[dict]:
    try:
        filas = await svc.listar_impactos(session, ctx["tenant_id"], ctx["user_id"], _uuid(resolucion_id))
    except svc.ErrorNormativo as exc:
        raise _http(exc) from exc
    return [f.model_dump(mode="json") for f in filas]


@router.post("/impacto/{id_analisis}/decision")
async def decidir(
    id_analisis: str, cuerpo: DecisionRequest, ctx: dict = Depends(_decide),
    session: AsyncSession = Depends(get_session),
) -> dict:
    try:
        analisis = await svc.decidir_impacto(
            session, ctx["tenant_id"], ctx["user_id"], _uuid(id_analisis), cuerpo.decision, cuerpo.nota
        )
    except svc.ErrorNormativo as exc:
        raise _http(exc) from exc
    return analisis.model_dump(mode="json")
