"""Informe anual del DPO armado desde su bitácora (DPO-02). ¤dpo-informe-anual ¤dpo-cockpit

El informe resume lo que el delegado dejó asentado en la bitácora de UNA organización durante
UN año; no ejecuta ni decide nada. Agrupación (convención de esta sala, no cita normativa):
- consultas atendidas: opiniones consultivas;
- escalamientos: advertencias y alertas de riesgo;
- dictámenes: recomendaciones, validaciones de EIPD, dictámenes de transferencia e informes de supervisión.
Sin plazos ni calendario de obligaciones (aplazados).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from app_core.errors import CodigoErrorNegocio
from features.dpo_cockpit.domain.models import DictamenDPO, TipoDictamenDPO
from features.dpo_cockpit.services.bitacora_service import (
    GENESIS_HASH,
    obtener_bitacora_tenant,
    verificar_cadena_organizacion,
)
from features.dpo_cockpit.services.inscripcion_engine import inscripcion_vigente

DPO_INFORME_ANIO_INVALIDO = CodigoErrorNegocio(
    codigo="DPO_INFORME_ANIO_INVALIDO",
    status_code=422,
    mensaje_defecto="El año del informe no es válido.",
    action_required=None,
)

ANIO_MINIMO = 2020

TIPOS_CONSULTA = (TipoDictamenDPO.OPINION_CONSULTIVA,)
TIPOS_ESCALAMIENTO = (TipoDictamenDPO.ADVERTENCIA_RIESGO, TipoDictamenDPO.ALERTA_RIESGO_GRAVE)
TIPOS_DICTAMEN = tuple(
    t for t in TipoDictamenDPO if t not in TIPOS_CONSULTA and t not in TIPOS_ESCALAMIENTO
)


def validar_anio(anio: int, hoy: Optional[datetime] = None) -> int:
    actual = (hoy or datetime.now(timezone.utc)).year
    if not isinstance(anio, int) or isinstance(anio, bool) or not ANIO_MINIMO <= anio <= actual:
        raise ErrorNegocio(
            DPO_INFORME_ANIO_INVALIDO,
            detail=f"El año debe estar entre {ANIO_MINIMO} y {actual}.",
        )
    return anio


def filtrar_por_anio(dictamenes: List[DictamenDPO], anio: int) -> List[DictamenDPO]:
    """Solo las actuaciones emitidas en `anio` (UTC)."""
    return [d for d in dictamenes if d.fecha_emision.astimezone(timezone.utc).year == anio]


def _tipo(d: DictamenDPO) -> TipoDictamenDPO:
    return d.tipo if isinstance(d.tipo, TipoDictamenDPO) else TipoDictamenDPO(str(d.tipo))


def resumir(dictamenes: List[DictamenDPO]) -> Dict[str, Any]:
    por_tipo = {t.value: 0 for t in TipoDictamenDPO}
    for d in dictamenes:
        por_tipo[_tipo(d).value] += 1

    def suma(tipos) -> int:
        return sum(por_tipo[t.value] for t in tipos)

    con_acuse = sum(1 for d in dictamenes if d.acuse_recibo_alta_direccion)
    return {
        "actuaciones_por_tipo": por_tipo,
        "resumen": {
            "total_actuaciones": len(dictamenes),
            "consultas_atendidas": suma(TIPOS_CONSULTA),
            "dictamenes": suma(TIPOS_DICTAMEN),
            "escalamientos": suma(TIPOS_ESCALAMIENTO),
            "con_acuse_de_direccion": con_acuse,
            "sin_acuse_de_direccion": len(dictamenes) - con_acuse,
        },
    }


async def armar_informe(
    session: AsyncSession, tenant_id: str, anio: int, hoy: Optional[datetime] = None
) -> Dict[str, Any]:
    """Informe de `anio` para `tenant_id`, leído de la bitácora y de la inscripción vigente."""
    validar_anio(anio, hoy)
    cadena = await obtener_bitacora_tenant(session, tenant_id)
    del_anio = filtrar_por_anio(cadena, anio)
    alterado = await verificar_cadena_organizacion(session, tenant_id)
    vigente = await inscripcion_vigente(session, tenant_id)
    informe: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "anio": anio,
        "generado_at": (hoy or datetime.now(timezone.utc)).isoformat(),
        **resumir(del_anio),
        "actuaciones": [
            {
                "id": d.id,
                "tipo": _tipo(d).value,
                "asunto": d.asunto,
                "fecha_emision": d.fecha_emision.isoformat(),
                "acuse_recibo_alta_direccion": d.acuse_recibo_alta_direccion,
            }
            for d in del_anio
        ],
        "inscripcion_spdp": (
            None
            if vigente is None
            else {
                "inscrito": vigente.inscrito,
                "fecha_inscripcion": (
                    vigente.fecha_inscripcion.isoformat() if vigente.fecha_inscripcion else None
                ),
                "numero_tramite": vigente.numero_tramite,
            }
        ),
        "cadena": {
            "huella": cadena[-1].sha256_hash if cadena else GENESIS_HASH,
            "integra": alterado is None,
            "dictamen_alterado": alterado.id if alterado is not None else None,
            "total_en_cadena": len(cadena),
        },
    }
    return informe


def renderizar_documento(informe: Dict[str, Any]) -> str:
    """Documento Markdown del informe; la huella de la cadena va en el pie."""
    r = informe["resumen"]
    ins = informe["inscripcion_spdp"]
    cadena = informe["cadena"]
    lineas = [
        f"# Informe anual del delegado de protección de datos · {informe['anio']}",
        "",
        f"Organización: {informe['tenant_id']}",
        f"Generado: {informe['generado_at']}",
        "",
        "El delegado supervisa y asesora. Este informe resume lo que dejó asentado en su "
        "bitácora; no ejecuta ni decide.",
        "",
        "## Resumen",
        f"- Actuaciones del año: {r['total_actuaciones']}",
        f"- Consultas atendidas: {r['consultas_atendidas']}",
        f"- Dictámenes: {r['dictamenes']}",
        f"- Escalamientos: {r['escalamientos']}",
        f"- Con acuse de la dirección: {r['con_acuse_de_direccion']}",
        f"- Sin acuse de la dirección: {r['sin_acuse_de_direccion']}",
        "",
        "## Actuaciones por tipo",
    ]
    lineas += [f"- {tipo}: {n}" for tipo, n in informe["actuaciones_por_tipo"].items()]
    lineas += ["", "## Detalle de actuaciones"]
    if informe["actuaciones"]:
        lineas += [
            f"- {a['fecha_emision'][:10]} · {a['tipo']} · {a['asunto']}"
            for a in informe["actuaciones"]
        ]
    else:
        lineas.append("- Sin actuaciones asentadas en este año.")
    lineas += ["", "## Inscripción ante la SPDP"]
    if ins is None:
        lineas.append("- Sin registro de inscripción en la plataforma.")
    elif ins["inscrito"]:
        lineas.append(
            f"- Inscrito el {ins['fecha_inscripcion']} · trámite {ins['numero_tramite']}"
        )
    else:
        lineas.append("- Declarado como no inscrito.")
    estado = (
        "íntegra"
        if cadena["integra"]
        else f"ALTERADA (primer dictamen alterado: {cadena['dictamen_alterado']})"
    )
    lineas += [
        "",
        "---",
        f"Huella de la cadena de la bitácora: {cadena['huella']}",
        f"Verificación de la cadena: {estado} · {cadena['total_en_cadena']} dictámenes en la cadena",
        "",
    ]
    return "\n".join(lineas)
