# ¤diagnostico ¤dpo-independencia ¤rbac-tenant
"""API del resultado sellado del diagnóstico (DIAG-03).

Solo el DPO sella (decisión del propietario, 2026-10-27): el delegado supervisa el cumplimiento
(art. 49 LOPDP) y diagnosticarlo es supervisarlo. Implementador, coordinador y administrador
consultan. Un resultado sellado no se edita ni se borra.
"""
from dataclasses import asdict
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from features.diagnostico import diagnostico_service
from features.diagnostico.domain.resultados import indicadores_a_salida
from features.evidencias import evidencias_service
from features.organizacion import organizacion_service

AUTO_REGISTRO = True
router = APIRouter(prefix="/diagnostico", tags=["Diagnóstico"])

ROLES_SELLO = ("dpo",)
ROLES_CONSULTA = ("dpo", "implementador", "coordinador", "admin_organizacion")

_sello = require_role(*ROLES_SELLO)
_consulta = require_role(*ROLES_CONSULTA)

RespuestaPerfil = Optional[Literal["si", "no"]]


class PerfilEntrada(BaseModel):
    """Perfil de operación de la ficha (sigue en el navegador); el DPO lo confirma al sellar."""

    model_config = ConfigDict(extra="forbid")

    internet: RespuestaPerfil = None
    publicidad: RespuestaPerfil = None
    camaras: RespuestaPerfil = None
    terceros: RespuestaPerfil = None
    nube: RespuestaPerfil = None
    exterior: RespuestaPerfil = None
    sistemas: RespuestaPerfil = None
    decisionesAutomaticas: RespuestaPerfil = None
    datosDelicados: RespuestaPerfil = None
    granCantidad: RespuestaPerfil = None
    obligadaDpd: RespuestaPerfil = None


class SellarEntrada(BaseModel):
    """Solo el perfil. Respuestas, niveles o puntajes que lleguen en el cuerpo se ignoran."""

    perfil: PerfilEntrada = PerfilEntrada()


def _a_salida(resultado: diagnostico_service.ResultadoSellado) -> dict:
    return {
        "id": resultado.id,
        "secuencia": resultado.secuencia,
        "sellado_por": resultado.sellado_por,
        "sellado_en": resultado.sellado_en.isoformat(),
        "normativa": resultado.normativa,
        "version_normativa": resultado.version_normativa,
        "tamano": resultado.tamano,
        "perfil": resultado.perfil,
        "respuestas": [asdict(r) for r in resultado.respuestas],
        "indicadores": indicadores_a_salida(resultado.indicadores),
        "huella_anterior": resultado.huella_anterior,
        "huella": resultado.huella,
    }


def _controles_con_documento(tenant_id: str) -> set[int]:
    """Controles con un documento que el servidor puede comprobar en la bóveda de evidencias."""
    return {
        control
        for evidencia in evidencias_service.listar_evidencias_tenant(tenant_id)
        for control in evidencia.controles_vinculados
    }


@router.post("/resultados", status_code=status.HTTP_201_CREATED)
async def sellar(
    payload: SellarEntrada,
    ctx: dict = Depends(_sello),
    session: AsyncSession = Depends(get_session),
):
    configuracion = await organizacion_service.get_tenant_config(session, ctx["tenant_id"])
    try:
        resultado = await diagnostico_service.sellar_diagnostico(
            session,
            ctx["tenant_id"],
            ctx["user_id"],
            tamano=configuracion.get("tamano"),
            perfil=payload.perfil.model_dump(),
            controles_con_documento=_controles_con_documento(ctx["tenant_id"]),
        )
    except diagnostico_service.SelladoNoPermitido as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return _a_salida(resultado)


@router.get("/resultados")
async def historial(ctx: dict = Depends(_consulta), session: AsyncSession = Depends(get_session)):
    asignaciones = await organizacion_service.list_role_assignments(session, ctx["tenant_id"])
    resultados = await diagnostico_service.listar_resultados(session, ctx["tenant_id"], ctx["user_id"])
    alterado = diagnostico_service.primer_resultado_alterado(resultados)
    return {
        "resultados": [_a_salida(r) for r in reversed(resultados)],
        "cadena_integra": alterado is None,
        "primer_alterado": alterado.id if alterado else None,
        "dpo_vigente": any(a["role"] == "dpo" for a in asignaciones),
    }
