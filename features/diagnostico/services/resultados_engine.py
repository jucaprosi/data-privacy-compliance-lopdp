# ¤diagnostico ¤dpo-independencia ¤rbac-tenant
"""Sellado del diagnóstico por el DPO (DIAG-03).

El servidor sella lo que tiene: las respuestas guardadas de la organización (DIAG-01), el tamaño
de su configuración y los indicadores que calcula su propio motor (DIAG-02). No acepta respuestas,
niveles de evidencia ni puntajes del navegador. El único dato que llega del navegador es el perfil
de operación de la ficha, que sigue viviendo allí: el DPO lo confirma al sellar y queda sellado
como alcance declarado.

Escala SMARTCIDI (DIAG-08): el servidor toma el nivel asignado 1 a 5 y la evidencia 0 a 4 guardados,
deriva el estado y sella el nivel por dimensión, sin cifra global de la organización.

Regla de respaldo: un control cuyo documento el servidor no puede comprobar se sella como E0,
aunque se haya declarado un nivel mayor. Nunca se inventa respaldo.
"""
from __future__ import annotations

import hashlib
import json
import math
import uuid
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.db.session import fijar_contexto_rls
from features.diagnostico.domain.models import EstadoCumplimiento, RespuestaControl, estado_desde_nivel_asignado
from features.diagnostico.domain.resultados import (
    CLAVES_PERFIL,
    HUELLA_GENESIS,
    NORMATIVA_SELLADA,
    RESPUESTAS_PERFIL,
    VERSION_NORMATIVA,
    DimensionSellada,
    IndicadoresSellados,
    RespuestaSellada,
    ResultadoSellado,
    SelladoNoPermitido,
    respuesta_a_json,
    indicadores_desde_json,
)
from features.diagnostico.services.dimensiones_sgpdp import agregar_resultado_por_dimension

# --- Alcance: tamaño y perfil (espejo de frontend/src/lib/bancoPreguntas/perfil.ts) ----------

_RANGO_TAMANO = {"micro": 0, "pequena": 1, "mediana": 2, "corporativo": 3}

# Preguntas que se descartan cuando el selector se responde «No».
_DESCARTA_SI_NO: dict[str, tuple[int, ...]] = {
    "internet": (18, 35),
    "publicidad": (21, 22, 36),
    "camaras": (38,),
    "terceros": (41, 42, 43, 44, 47, 48),
    "nube": (45,),
    "exterior": (46,),
    "sistemas": (40, 55),
    "decisionesAutomaticas": (72,),
    "obligadaDpd": (4,),
}
_ESTRUCTURALES = (9, 10, 13, 28)
_PAQUETE_DELICADOS = (3, 4, 40, 52, 59, 61, 63, 64, 65, 71)
_PAQUETE_DELICADOS_CON_TERCEROS = (42, 47, 48)
_PAQUETE_GRAN_ESCALA = (3, 4, 5, 6, 8, 16, 34, 65, 76)


def normalizar_perfil(perfil: Optional[dict[str, Any]]) -> dict[str, Optional[str]]:
    """Perfil con las once claves; una respuesta sin contestar queda en None."""
    perfil = perfil or {}
    desconocidas = set(perfil) - set(CLAVES_PERFIL)
    if desconocidas:
        raise SelladoNoPermitido(f"El perfil trae claves desconocidas: {sorted(desconocidas)}")
    normalizado: dict[str, Optional[str]] = {}
    for clave in CLAVES_PERFIL:
        valor = perfil.get(clave)
        if valor not in RESPUESTAS_PERFIL:
            raise SelladoNoPermitido(f"El perfil «{clave}» solo admite «si», «no» o sin responder")
        normalizado[clave] = valor
    return normalizado


def ajuste_por_perfil(perfil: dict[str, Optional[str]]) -> tuple[set[int], set[int]]:
    """(descartadas, incluidas). Lo incluido gana y los estructurales nunca se descartan."""
    descartadas: set[int] = set()
    incluidas: set[int] = set()
    for clave, ids in _DESCARTA_SI_NO.items():
        if perfil.get(clave) == "no":
            descartadas.update(ids)
    if perfil.get("datosDelicados") == "no" and perfil.get("granCantidad") == "no" and perfil.get("decisionesAutomaticas") == "no":
        descartadas.add(67)
    if perfil.get("datosDelicados") == "si":
        incluidas.update(_PAQUETE_DELICADOS)
        if perfil.get("terceros") == "si":
            incluidas.update(_PAQUETE_DELICADOS_CON_TERCEROS)
    if perfil.get("granCantidad") == "si":
        incluidas.update(_PAQUETE_GRAN_ESCALA)
    if perfil.get("obligadaDpd") == "si":
        incluidas.update((3, 4))
    descartadas.difference_update(_ESTRUCTURALES)
    descartadas.difference_update(incluidas)
    return descartadas, incluidas


def controles_aplicables(banco: list[dict], tamano: str, perfil: dict[str, Optional[str]]) -> list[dict]:
    """Controles del banco exigibles a la organización, en el orden del banco."""
    rango = _RANGO_TAMANO[tamano]
    descartadas, incluidas = ajuste_por_perfil(perfil)
    aplicables = []
    for pregunta in banco:
        pid = pregunta["id"]
        if pid in incluidas or (
            pid not in descartadas and rango >= _RANGO_TAMANO.get(pregunta.get("tamanoMinimo", "micro"), 0)
        ):
            aplicables.append(pregunta)
    return aplicables


# --- Indicadores ----------------------------------------------------------------------------


def _redondear(valor: float, decimales: int) -> float:
    """Redondeo de Math.round de la pantalla (mitad hacia arriba), para que ambos lados coincidan."""
    factor = 10**decimales
    return math.floor(valor * factor + 0.5) / factor


def calcular_indicadores(
    aplicables: list[dict],
    respuestas_guardadas: Iterable[dict[str, Any]],
    controles_con_documento: set[int],
) -> tuple[IndicadoresSellados, list[RespuestaSellada]]:
    """Calcula los indicadores por dimensión y las respuestas tal como se sellan.

    Dimensión y criticidad salen del banco (fuente autoritativa), no de la fila guardada. Un
    control aplicable sin respuesta, o con nivel asignado nulo, entra como pendiente: computa
    cero, no se excluye. El estado sellado lo deriva el servidor del nivel asignado.
    """
    por_pregunta = {int(r["pregunta_id"]): r for r in respuestas_guardadas}
    entradas: list[RespuestaControl] = []
    selladas: list[RespuestaSellada] = []
    for pregunta in aplicables:
        pid = pregunta["id"]
        guardada = por_pregunta.get(pid)
        asignado = guardada.get("nivel_asignado") if guardada else None
        asignado = int(asignado) if asignado is not None else None
        estado = estado_desde_nivel_asignado(asignado)
        declarado = int(guardada["nivel_evidencia"]) if guardada else 0
        con_documento = pid in controles_con_documento
        sellado = declarado if con_documento else 0
        entradas.append(
            RespuestaControl(
                pregunta_id=pid,
                cumple=estado,
                evidencia_nivel=sellado,
                nivel_asignado=asignado,
                criticidad=int(pregunta["criticidad"]),
                dimension_id=pregunta["dimensionId"],
                control=pregunta.get("control", ""),
            )
        )
        if guardada:
            selladas.append(
                RespuestaSellada(
                    pregunta_id=pid,
                    control=pregunta.get("control", "") or str(guardada["control"]),
                    dimension=pregunta["dimensionId"],
                    estado=estado.value,
                    criticidad=int(pregunta["criticidad"]),
                    nivel_declarado=declarado,
                    nivel_sellado=sellado,
                    con_documento=con_documento,
                    nivel_asignado=asignado,
                )
            )

    resultado = agregar_resultado_por_dimension(entradas)
    evaluadas = [r for r in selladas if r.nivel_asignado is not None]
    # R5: describe la evidencia, no la madurez. media(nivel_evidencia_sellado) / 4 * 100.
    respaldo = (
        _redondear(sum(r.nivel_sellado for r in evaluadas) / len(evaluadas) / 4 * 100, 1)
        if evaluadas
        else 0.0
    )
    indicadores = IndicadoresSellados(
        cumplimiento=resultado.brechas_criticas == 0,
        brechas_criticas=resultado.brechas_criticas,
        brechas_altas=resultado.brechas_altas,
        por_dimension=[
            DimensionSellada(
                dimension=d.id,
                nombre=d.nombre,
                nivel=d.nivel,
                etiqueta=d.nivel_etiqueta,
                score=d.score,
                cobertura=d.cobertura_porcentaje,
                brechas_criticas=d.brechas_criticas,
                brechas_altas=d.brechas_altas,
            )
            for d in resultado.dimensiones
            if d.items_aplicables > 0
        ],
        respaldo_documental=respaldo,
        preguntas_evaluadas=resultado.total_evaluados,
        preguntas_aplicables=resultado.total_aplicables,
        cobertura=resultado.cobertura_porcentaje,
    )
    return indicadores, selladas


# --- Huella encadenada por organización -------------------------------------------------------


def calcular_huella(contenido: dict[str, Any]) -> str:
    crudo = json.dumps(contenido, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(crudo.encode("utf-8")).hexdigest()


_COLUMNAS = (
    "id, tenant_id, secuencia, sellado_por, sellado_en, normativa, version_normativa, tamano, "
    "perfil, respuestas, indicadores, huella_anterior, huella"
)


def _fila_a_resultado(fila: dict[str, Any]) -> ResultadoSellado:
    sellado_en = fila["sellado_en"]
    if sellado_en.tzinfo is None:
        sellado_en = sellado_en.replace(tzinfo=timezone.utc)
    return ResultadoSellado(
        id=fila["id"],
        tenant_id=fila["tenant_id"],
        secuencia=int(fila["secuencia"]),
        sellado_por=fila["sellado_por"],
        sellado_en=sellado_en.astimezone(timezone.utc),
        normativa=fila["normativa"],
        version_normativa=fila["version_normativa"],
        tamano=fila["tamano"],
        perfil=dict(fila["perfil"]),
        respuestas=[RespuestaSellada(**r) for r in fila["respuestas"]],
        indicadores=indicadores_desde_json(fila["indicadores"]),
        huella_anterior=fila["huella_anterior"],
        huella=fila["huella"],
    )


async def listar_resultados(session: AsyncSession, tenant_id: str, user_id: str) -> list[ResultadoSellado]:
    """Resultados sellados de la organización, del más antiguo al más reciente."""
    await fijar_contexto_rls(session, tenant_id, user_id)
    filas = await session.execute(
        text(f"SELECT {_COLUMNAS} FROM diagnostico_resultados WHERE tenant_id = :t ORDER BY secuencia"),
        {"t": tenant_id},
    )
    return [_fila_a_resultado(dict(f)) for f in filas.mappings().all()]


def primer_resultado_alterado(resultados: list[ResultadoSellado]) -> Optional[ResultadoSellado]:
    """Recorre la cadena en orden y devuelve el primer resultado que no cuadra, o None."""
    anterior = HUELLA_GENESIS
    for resultado in resultados:
        if resultado.huella_anterior != anterior or calcular_huella(resultado.contenido()) != resultado.huella:
            return resultado
        anterior = resultado.huella
    return None


async def sellar_resultado(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    *,
    tamano: Optional[str],
    perfil: dict[str, Optional[str]],
    banco: list[dict],
    respuestas_guardadas: list[dict[str, Any]],
    controles_con_documento: set[int],
) -> ResultadoSellado:
    """Sella el diagnóstico de la organización con lo que tiene el servidor."""
    if tamano not in _RANGO_TAMANO:
        raise SelladoNoPermitido(
            "La organización no tiene configurado su tamaño: el administrador debe fijarlo en "
            "Administración → Configuración antes de sellar."
        )
    perfil = normalizar_perfil(perfil)
    aplicables = controles_aplicables(banco, tamano, perfil)
    indicadores, selladas = calcular_indicadores(aplicables, respuestas_guardadas, controles_con_documento)
    if not any(r.estado != EstadoCumplimiento.PENDIENTE.value for r in selladas):
        raise SelladoNoPermitido("No hay respuestas guardadas que sellar en esta organización.")

    await fijar_contexto_rls(session, tenant_id, user_id)
    # Serializa los sellados de una organización, también el primero: dos sellados simultáneos
    # no pueden colgar del mismo eslabón (además lo impide la restricción única de la tabla).
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:clave))"),
        {"clave": f"diagnostico_resultados:{tenant_id}"},
    )
    ultimo = (
        await session.execute(
            text(
                "SELECT secuencia, huella, sellado_en FROM diagnostico_resultados "
                "WHERE tenant_id = :t ORDER BY secuencia DESC LIMIT 1"
            ),
            {"t": tenant_id},
        )
    ).mappings().first()

    ahora = datetime.now(timezone.utc)
    if ultimo is not None and ahora <= ultimo["sellado_en"]:
        ahora = ultimo["sellado_en"].astimezone(timezone.utc) + timedelta(microseconds=1)
    resultado = ResultadoSellado(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        secuencia=(int(ultimo["secuencia"]) + 1) if ultimo else 1,
        sellado_por=user_id,
        sellado_en=ahora,
        normativa=NORMATIVA_SELLADA,
        version_normativa=VERSION_NORMATIVA,
        tamano=tamano,
        perfil=perfil,
        respuestas=selladas,
        indicadores=indicadores,
        huella_anterior=str(ultimo["huella"]) if ultimo else HUELLA_GENESIS,
    )
    resultado.huella = calcular_huella(resultado.contenido())

    await session.execute(
        text(
            f"INSERT INTO diagnostico_resultados ({_COLUMNAS}) VALUES "
            "(:id, :tenant_id, :secuencia, :sellado_por, :sellado_en, :normativa, :version_normativa, "
            ":tamano, CAST(:perfil AS jsonb), CAST(:respuestas AS jsonb), CAST(:indicadores AS jsonb), "
            ":huella_anterior, :huella)"
        ),
        {
            "id": resultado.id,
            "tenant_id": tenant_id,
            "secuencia": resultado.secuencia,
            "sellado_por": user_id,
            "sellado_en": resultado.sellado_en,
            "normativa": resultado.normativa,
            "version_normativa": resultado.version_normativa,
            "tamano": tamano,
            "perfil": json.dumps(perfil, ensure_ascii=False),
            "respuestas": json.dumps([respuesta_a_json(r) for r in selladas], ensure_ascii=False),
            "indicadores": json.dumps(asdict(indicadores), ensure_ascii=False),
            "huella_anterior": resultado.huella_anterior,
            "huella": resultado.huella,
        },
    )
    await registrar_evento(
        session,
        tenant_id,
        "diagnostico_resultado",
        resultado.id,
        "diagnostico_resultado_sellado",
        user_id,
        {
            "secuencia": resultado.secuencia,
            "huella": resultado.huella,
            "preguntas_evaluadas": indicadores.preguntas_evaluadas,
            "escala": indicadores.escala,
            "niveles_por_dimension": {d.dimension: d.nivel for d in indicadores.por_dimension},
        },
    )
    return resultado
