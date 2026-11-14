# ¤incidentes ¤hallazgos ¤rbac-tenant ¤seguridad
"""Asistente de vulneración en ocho secciones e informes (INC-02).

Identidad, organización y rol salen del token (require_role). Las secciones solo se agregan. No se
calcula ni se compara ningún plazo (R5). La custodia de informes y la validación de la evidencia de la
notificación van por el pasillo de evidencias.
"""
from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from app_core.errors import ErrorNegocio
from app_core.pasillo import evidencias as pasillo_evidencias
from features.incidentes import incidentes_service as inc

AUTO_REGISTRO = True
router = APIRouter(prefix="/incidentes", tags=["Incidentes y vulneraciones"])

_lectura = require_role(*inc.ROLES_LECTURA)
_escritura = require_role("implementador", "coordinador", "dpo")
_informes = require_role(*inc.ROLES_INFORMES)


class NotificacionEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    destino: Literal["spdp", "titulares"]
    notificado_en: datetime
    evidencia_sha256: str = Field(min_length=64, max_length=71)


class InformeEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    destino: Literal["spdp", "titulares"]


def _traducir(exc: Exception) -> ErrorNegocio:
    if isinstance(exc, inc.IncidenteNoEncontrado):
        return ErrorNegocio("INCIDENTE_NO_ENCONTRADO")
    if isinstance(exc, inc.RolNoAutorizado):
        raise HTTPException(status_code=403, detail="No tienes permiso para esta acción.")
    if isinstance(exc, inc.DecisionSinJustificacion):
        return ErrorNegocio("DECISION_SIN_JUSTIFICACION")
    if isinstance(exc, inc.SeccionAnteriorIncompleta):
        return ErrorNegocio("SECCION_ANTERIOR_INCOMPLETA", detail=f"Antes de seguir, completa el paso {exc.seccion}.")
    if isinstance(exc, inc.SeccionInvalida):
        return ErrorNegocio("SECCION_INCOMPLETA", detail=", ".join(exc.faltan) or str(exc))
    raise exc


_ERRORES = (
    inc.IncidenteNoEncontrado, inc.RolNoAutorizado, inc.DecisionSinJustificacion,
    inc.SeccionAnteriorIncompleta, inc.SeccionInvalida,
)


@router.get("/asistentes")
async def resumen(ctx: dict = Depends(_lectura), session: AsyncSession = Depends(get_session)):
    return await inc.resumen_asistentes(session, ctx["tenant_id"], ctx["user_id"])


@router.get("/{incidente_id}/asistente")
async def leer(incidente_id: str, ctx: dict = Depends(_lectura), session: AsyncSession = Depends(get_session)):
    try:
        estado = await inc.estado_asistente(session, ctx["tenant_id"], ctx["user_id"], incidente_id)
    except _ERRORES as exc:
        raise _traducir(exc) from exc
    return estado.a_salida()


@router.put("/{incidente_id}/asistente/{seccion}")
async def guardar(
    incidente_id: str,
    cuerpo: dict[str, Any],
    seccion: int = Path(ge=1, le=8),
    ctx: dict = Depends(_escritura),
    session: AsyncSession = Depends(get_session),
):
    try:
        if seccion == 8:
            entrada = NotificacionEntrada.model_validate(cuerpo)
            estado = await inc.registrar_notificacion(
                session, ctx["tenant_id"], ctx["user_id"], ctx["role"], incidente_id,
                entrada.destino, entrada.notificado_en, entrada.evidencia_sha256,
                pasillo_evidencias.huella_custodiada,
            )
        else:
            estado = await inc.guardar_seccion(
                session, ctx["tenant_id"], ctx["user_id"], ctx["role"], incidente_id, seccion, cuerpo
            )
    except _ERRORES as exc:
        raise _traducir(exc) from exc
    return estado.a_salida()


@router.post("/{incidente_id}/informes", status_code=201)
async def informe(
    incidente_id: str,
    entrada: InformeEntrada,
    ctx: dict = Depends(_informes),
    session: AsyncSession = Depends(get_session),
):
    try:
        resultado = await inc.generar_informe(
            session, ctx["tenant_id"], ctx["user_id"], ctx["role"], incidente_id, entrada.destino,
            pasillo_evidencias.custodiar_documento_generado,
        )
    except _ERRORES as exc:
        raise _traducir(exc) from exc
    return resultado
