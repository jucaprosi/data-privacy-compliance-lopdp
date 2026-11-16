# ¤diagnostico ¤diagnostico-comparativo ¤tablero-dimensiones
"""Comparativo del diagnóstico de prueba con el real, por dimensión y por control (DIAG-06).

El diagnóstico se sella dos veces como máximo (DIAG-11): el primero es el de prueba y el segundo, el
real (línea base). Aquí se compara el de prueba (punto de partida) con el real (punto de llegada) de
la MISMA organización: nunca se leen resultados de otra (la base lo impide con RLS). Sin cifra única:
no hay «avance global» (D-1); cada dimensión se compara con su propio nivel.

Una brecha es un control con estado «No Conforme» o «Parcial». Un control sin respuesta sellada en
alguno de los dos lados no se compara. Brecha cerrada: lo era en el de prueba y ya no en el real;
nueva: no lo era y ahora sí; sigue: lo es en ambos.
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app_core.errors import ErrorNegocio
from features.diagnostico.domain.errores import COMPARATIVO_ESCALA_ANTERIOR
from features.diagnostico.domain.models import EstadoCumplimiento
from features.diagnostico.domain.resultados import (
    DimensionSellada,
    IndicadoresSellados,
    RespuestaSellada,
    ResultadoSellado,
    es_resultado_anterior,
)
from features.diagnostico.services.resultados_engine import (
    SELLOS_MAXIMOS,
    TIPO_PRUEBA,
    TIPO_REAL,
    listar_resultados,
    tipo_de_secuencia,
)

ESTADOS_BRECHA = frozenset({EstadoCumplimiento.NO_CONFORME.value, EstadoCumplimiento.PARCIAL.value})


def _es_brecha(respuesta: RespuestaSellada) -> bool:
    return respuesta.estado in ESTADOS_BRECHA


def _por_control(resultado: ResultadoSellado) -> dict[int, RespuestaSellada]:
    return {r.pregunta_id: r for r in resultado.respuestas}


def _por_dimension(resultado: ResultadoSellado) -> dict[str, DimensionSellada]:
    indicadores = resultado.indicadores
    assert isinstance(indicadores, IndicadoresSellados)
    return {d.dimension: d for d in indicadores.por_dimension}


def _control(respuesta: RespuestaSellada) -> dict[str, Any]:
    return {
        "pregunta_id": respuesta.pregunta_id,
        "control": respuesta.control,
        "dimension": respuesta.dimension,
        "criticidad": respuesta.criticidad,
    }


def _resumen(resultado: ResultadoSellado) -> dict[str, Any]:
    return {
        "id": resultado.id,
        "tipo": tipo_de_secuencia(resultado.secuencia),
        "sellado_en": resultado.sellado_en.isoformat(),
    }


def comparar(linea_base: ResultadoSellado, actual: ResultadoSellado) -> dict[str, Any]:
    """Compara `linea_base` (el de prueba, de partida) con `actual` (el real, de llegada)."""
    if es_resultado_anterior(linea_base.indicadores) or es_resultado_anterior(actual.indicadores):
        raise ErrorNegocio(COMPARATIVO_ESCALA_ANTERIOR)
    antes, despues = _por_control(linea_base), _por_control(actual)
    cerradas: list[dict[str, Any]] = []
    nuevas: list[dict[str, Any]] = []
    siguen: list[dict[str, Any]] = []
    for pid in sorted(set(antes) & set(despues)):
        era, es = _es_brecha(antes[pid]), _es_brecha(despues[pid])
        if era and not es:
            cerradas.append(_control(despues[pid]))
        elif es and not era:
            nuevas.append(_control(despues[pid]))
        elif era and es:
            siguen.append(_control(despues[pid]))

    dims_antes, dims_despues = _por_dimension(linea_base), _por_dimension(actual)
    por_dimension = []
    for dim in sorted(set(dims_antes) | set(dims_despues)):
        a, d = dims_antes.get(dim), dims_despues.get(dim)
        por_dimension.append(
            {
                "dimension": dim,
                "nombre": (d or a).nombre,
                "nivel_base": a.nivel if a else None,
                "nivel_actual": d.nivel if d else None,
                "diferencia_nivel": (d.nivel - a.nivel) if a and d else None,
                "cerradas": sum(1 for c in cerradas if c["dimension"] == dim),
                "nuevas": sum(1 for c in nuevas if c["dimension"] == dim),
                "siguen": sum(1 for c in siguen if c["dimension"] == dim),
            }
        )
    return {
        "comparable": True,
        "motivo": None,
        "codigo_motivo": None,
        "linea_base": _resumen(linea_base),
        "actual": _resumen(actual),
        "por_dimension": por_dimension,
        "brechas": {"cerradas": cerradas, "nuevas": nuevas, "siguen": siguen},
    }


async def comparativo_de_organizacion(
    session: AsyncSession, tenant_id: str, user_id: Optional[str]
) -> dict[str, Any]:
    """Comparativo de prueba y real de la organización; con un solo sello lo dice y no compara."""
    resultados = await listar_resultados(session, tenant_id, user_id or "")
    por_tipo = {tipo_de_secuencia(r.secuencia): r for r in resultados[:SELLOS_MAXIMOS]}
    if TIPO_PRUEBA in por_tipo and TIPO_REAL in por_tipo:
        return comparar(por_tipo[TIPO_PRUEBA], por_tipo[TIPO_REAL])
    motivo = (
        "Falta el diagnóstico real: cuando el DPO lo selle podrás compararlo con el de prueba."
        if por_tipo
        else "Todavía no hay diagnósticos sellados. El DPO sella primero el de prueba y después el real; entonces podrás compararlos."
    )
    return {
        "comparable": False,
        "motivo": motivo,
        "codigo_motivo": "sin_real" if por_tipo else "sin_sellos",
        "linea_base": _resumen(por_tipo[TIPO_PRUEBA]) if TIPO_PRUEBA in por_tipo else None,
        "actual": None,
        "por_dimension": [],
        "brechas": {"cerradas": [], "nuevas": [], "siguen": []},
    }
