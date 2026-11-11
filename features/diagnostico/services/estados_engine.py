# ¤diagnostico ¤diagnostico-estados ¤diagnostico-comparativo ¤roadmap
"""Estados del diagnóstico: el assessment actual (DIAG-12, invariante 58 de EVYDENTIA).

Después del diagnóstico real (DIAG-11) no se repite el diagnóstico: el DPO emite estados. Un estado
parte de los niveles del diagnóstico real y suma, por control, las tareas del plan de acción cerradas
con evidencia validada por cuatro ojos (`INV_LOPDP_FOUR_EYES_CLOSURE`). Queda sellado con una huella
SHA-256 encadenada por organización y nunca cambia un diagnóstico sellado: esta sala solo lee
`diagnostico_resultados`.

Regla de suma: la validación de una evidencia sube el nivel de evidencia (0 a 4) del control, nunca la madurez
SMARTCIDI. Por control, el nivel de evidencia del estado es el máximo entre el del diagnóstico real y el
`nivel_acreditado` de las evidencias con doble validación (lo añadirá RM-25a; hoy ninguna lo trae, así que suma 0).
Tomar el máximo nunca baja el nivel (suposición del Arquitecto, marcada al CTO). El nivel asignado de cada control
es el del real. Sin cifra única de avance (D-1): los indicadores son los de DIAG-08, por dimensión. Las tareas se leen por el pasillo de la
Hoja de Ruta, nunca de sus tablas.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.db.session import fijar_contexto_rls
from app_core.errors import ErrorNegocio
from app_core.pasillo import roadmap as pasillo_roadmap
from features.diagnostico.domain.errores import (
    ESTADO_NO_ENCONTRADO,
    ESTADO_SIN_ANTERIOR,
    ESTADO_SIN_DIAGNOSTICO_REAL,
)
from features.diagnostico.domain.resultados import (
    HUELLA_GENESIS,
    NORMATIVA_SELLADA,
    VERSION_NORMATIVA,
    IndicadoresSellados,
    RespuestaSellada,
    ResultadoSellado,
    es_resultado_anterior,
    indicadores_a_salida,
    indicadores_desde_json,
    respuesta_a_json,
)
from features.diagnostico.services.comparativo_engine import comparar
from features.diagnostico.services.engine import cargar_banco_preguntas_raw
from features.diagnostico.services.resultados_engine import (
    EVIDENCIA_DECLARADA,
    TIPO_REAL,
    calcular_huella,
    calcular_indicadores,
    controles_aplicables,
    listar_resultados,
    tipo_de_secuencia,
)

NIVEL_EVIDENCIA_MAXIMO = 4
COMPARAR_CON_REAL = "real"
COMPARAR_CON_ANTERIOR = "anterior"
MODOS_COMPARACION = (COMPARAR_CON_REAL, COMPARAR_CON_ANTERIOR)

_COLUMNAS = (
    "id, tenant_id, secuencia, emitido_por, fecha_corte, resultado_real_id, escala, respuestas, tareas, "
    "indicadores, huella_anterior, huella"
)


def _pregunta_de(control_ref: str) -> int:
    return int(control_ref.lstrip("P"))


def sumar_tareas(
    real: ResultadoSellado, tareas: list[dict[str, Any]], banco: Optional[list[dict]] = None
) -> tuple[IndicadoresSellados, list[RespuestaSellada]]:
    """Niveles del estado: los del real con la evidencia acreditada por las tareas validadas, sin cifra única.

    Cada tarea puede traer `nivel_acreditado` (0 a 4); sin él suma 0. Por control se toma el máximo entre el
    nivel de evidencia del real y el acreditado; el nivel asignado (madurez) no cambia.
    """
    acreditado: dict[int, int] = {}
    for t in tareas:
        pid = _pregunta_de(t["control_ref"])
        nivel = max(0, min(NIVEL_EVIDENCIA_MAXIMO, int(t.get("nivel_acreditado") or 0)))
        acreditado[pid] = max(acreditado.get(pid, 0), nivel)
    guardadas = [
        {
            "pregunta_id": r.pregunta_id,
            "control": r.control,
            "nivel_asignado": r.nivel_asignado,
            "nivel_evidencia": max(r.nivel_declarado, acreditado.get(r.pregunta_id, 0)),
        }
        for r in real.respuestas
    ]
    banco = banco if banco is not None else cargar_banco_preguntas_raw()
    aplicables = controles_aplicables(banco, real.tamano, real.perfil)
    return calcular_indicadores(aplicables, guardadas, set(), EVIDENCIA_DECLARADA)


def _contenido(estado: dict[str, Any]) -> dict[str, Any]:
    """Lo que se sella: todo salvo la huella propia."""
    return {k: v for k, v in estado.items() if k != "huella"}


def _fila_a_estado(fila: dict[str, Any]) -> dict[str, Any]:
    corte = fila["fecha_corte"]
    if corte.tzinfo is None:
        corte = corte.replace(tzinfo=timezone.utc)
    return {
        "id": fila["id"],
        "tenant_id": fila["tenant_id"],
        "secuencia": int(fila["secuencia"]),
        "emitido_por": fila["emitido_por"],
        "fecha_corte": corte.astimezone(timezone.utc).isoformat(),
        "resultado_real_id": fila["resultado_real_id"],
        "escala": fila["escala"],
        "respuestas": fila["respuestas"],
        "tareas": fila["tareas"],
        "indicadores": fila["indicadores"],
        "huella_anterior": fila["huella_anterior"],
        "huella": fila["huella"],
    }


def estado_a_salida(estado: dict[str, Any]) -> dict[str, Any]:
    return {**estado, "indicadores": indicadores_a_salida(indicadores_desde_json(estado["indicadores"]))}


async def listar_estados(session: AsyncSession, tenant_id: str, user_id: str) -> list[dict[str, Any]]:
    """Estados de la organización, del más antiguo al más reciente."""
    await fijar_contexto_rls(session, tenant_id, user_id)
    filas = await session.execute(
        text(f"SELECT {_COLUMNAS} FROM diagnostico_estados WHERE tenant_id = :t ORDER BY secuencia"),
        {"t": tenant_id},
    )
    return [_fila_a_estado(dict(f)) for f in filas.mappings().all()]


def primer_estado_alterado(estados: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Recorre la cadena en orden y devuelve el primer estado que no cuadra, o None."""
    anterior = HUELLA_GENESIS
    for estado in estados:
        if estado["huella_anterior"] != anterior or calcular_huella(_contenido(estado)) != estado["huella"]:
            return estado
        anterior = estado["huella"]
    return None


async def _real_sellado(session: AsyncSession, tenant_id: str, user_id: str) -> ResultadoSellado:
    for resultado in await listar_resultados(session, tenant_id, user_id):
        if tipo_de_secuencia(resultado.secuencia) == TIPO_REAL:
            return resultado
    raise ErrorNegocio(ESTADO_SIN_DIAGNOSTICO_REAL)


async def emitir_estado(session: AsyncSession, tenant_id: str, user_id: str) -> dict[str, Any]:
    """Emite un estado a partir del diagnóstico real; 409 si el real no está sellado."""
    real = await _real_sellado(session, tenant_id, user_id)
    if es_resultado_anterior(real.indicadores):
        raise ErrorNegocio(ESTADO_SIN_DIAGNOSTICO_REAL, detail="El diagnóstico real se selló con la escala anterior.")
    tareas = await pasillo_roadmap.tareas_cerradas_con_evidencia_validada(session, tenant_id, user_id)
    indicadores, selladas = sumar_tareas(real, tareas)

    await fijar_contexto_rls(session, tenant_id, user_id)
    # Serializa los estados de una organización: dos emisiones simultáneas no cuelgan del mismo eslabón.
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:clave))"), {"clave": f"diagnostico_estados:{tenant_id}"}
    )
    ultimo = (
        await session.execute(
            text(
                "SELECT secuencia, huella, fecha_corte FROM diagnostico_estados "
                "WHERE tenant_id = :t ORDER BY secuencia DESC LIMIT 1"
            ),
            {"t": tenant_id},
        )
    ).mappings().first()
    corte = datetime.now(timezone.utc)
    if ultimo is not None and corte <= ultimo["fecha_corte"]:
        corte = ultimo["fecha_corte"].astimezone(timezone.utc) + timedelta(microseconds=1)
    estado = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "secuencia": (int(ultimo["secuencia"]) + 1) if ultimo else 1,
        "emitido_por": user_id,
        "fecha_corte": corte.isoformat(),
        "resultado_real_id": real.id,
        "escala": indicadores.escala,
        "respuestas": [respuesta_a_json(r) for r in selladas],
        "tareas": [
            {"tarea_id": t["tarea_id"], "control_ref": t["control_ref"]} for t in tareas
        ],
        "indicadores": asdict(indicadores),
        "huella_anterior": str(ultimo["huella"]) if ultimo else HUELLA_GENESIS,
    }
    estado["huella"] = calcular_huella(_contenido(estado))
    await session.execute(
        text(
            f"INSERT INTO diagnostico_estados ({_COLUMNAS}) VALUES "
            "(:id, :tenant_id, :secuencia, :emitido_por, :fecha_corte, :resultado_real_id, :escala, "
            "CAST(:respuestas AS jsonb), CAST(:tareas AS jsonb), CAST(:indicadores AS jsonb), "
            ":huella_anterior, :huella)"
        ),
        {
            **{k: estado[k] for k in ("id", "tenant_id", "secuencia", "emitido_por", "resultado_real_id", "escala",
                                      "huella_anterior", "huella")},
            "fecha_corte": corte,
            "respuestas": json.dumps(estado["respuestas"], ensure_ascii=False),
            "tareas": json.dumps(estado["tareas"], ensure_ascii=False),
            "indicadores": json.dumps(estado["indicadores"], ensure_ascii=False),
        },
    )
    await registrar_evento(
        session,
        tenant_id,
        "diagnostico_estado",
        estado["id"],
        "diagnostico_estado_emitido",
        user_id,
        {
            "secuencia": estado["secuencia"],
            "huella": estado["huella"],
            "tareas_sumadas": len(tareas),
            "niveles_por_dimension": {d.dimension: d.nivel for d in indicadores.por_dimension},
        },
    )
    return estado_a_salida(estado)


def _como_resultado(estado: dict[str, Any], secuencia: int, real: ResultadoSellado) -> ResultadoSellado:
    """Estado con la forma de un resultado sellado, para reutilizar `comparar` de DIAG-06.

    `secuencia` es solo la posición en la comparación (1 = punto de partida, 2 = de llegada): el resumen
    que devuelve `comparar` se sustituye por el del estado en `comparar_estado`.
    """
    return ResultadoSellado(
        id=estado["id"],
        tenant_id=estado["tenant_id"],
        secuencia=secuencia,
        sellado_por=estado["emitido_por"],
        sellado_en=datetime.fromisoformat(estado["fecha_corte"]),
        normativa=NORMATIVA_SELLADA,
        version_normativa=VERSION_NORMATIVA,
        tamano=real.tamano,
        perfil=real.perfil,
        respuestas=[RespuestaSellada(**r) for r in estado["respuestas"]],
        indicadores=indicadores_desde_json(estado["indicadores"]),
        huella_anterior=estado["huella_anterior"],
        huella=estado["huella"],
    )


def _resumen_estado(estado: dict[str, Any]) -> dict[str, Any]:
    return {"id": estado["id"], "tipo": "estado", "secuencia": estado["secuencia"], "sellado_en": estado["fecha_corte"]}


async def comparar_estado(
    session: AsyncSession, tenant_id: str, user_id: str, estado_id: str, con: str = COMPARAR_CON_REAL
) -> dict[str, Any]:
    """Compara un estado con el diagnóstico real o con el estado anterior (por dimensión y por control)."""
    estados = await listar_estados(session, tenant_id, user_id)
    indice = next((i for i, e in enumerate(estados) if e["id"] == estado_id), None)
    if indice is None:
        raise ErrorNegocio(ESTADO_NO_ENCONTRADO)
    real = await _real_sellado(session, tenant_id, user_id)
    estado = estados[indice]
    llegada = _como_resultado(estado, 2, real)
    if con == COMPARAR_CON_ANTERIOR:
        if indice == 0:
            raise ErrorNegocio(ESTADO_SIN_ANTERIOR)
        partida_estado = estados[indice - 1]
        partida = _como_resultado(partida_estado, 1, real)
        resumen_partida = _resumen_estado(partida_estado)
    else:
        partida = real
        resumen_partida = {"id": real.id, "tipo": TIPO_REAL, "sellado_en": real.sellado_en.isoformat()}
    comparativo = comparar(partida, llegada)
    comparativo["linea_base"] = resumen_partida
    comparativo["actual"] = _resumen_estado(estado)
    comparativo["con"] = con if con in MODOS_COMPARACION else COMPARAR_CON_REAL
    return comparativo
