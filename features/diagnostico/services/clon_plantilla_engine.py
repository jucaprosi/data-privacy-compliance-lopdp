# -*- coding: utf-8 -*-
# ¤demo ¤adpa ¤seguridad-tenant ¤diagnostico
"""DEMO-03b: copia y siembra de la sala Diagnóstico para la demo «Cooperativa Demo».

`clonar_desde_plantilla` copia solo las filas de esta sala (respuestas, asignaciones de dominios y
resultados sellados) del tenant plantilla al tenant nuevo. Cada id nuevo se deriva de forma determinista
del tenant destino y del id de origen (uuid5): repetir la copia en la misma transacción no duplica nada.
Nunca escribe en el tenant de origen, nunca hace commit y no deja en las filas ningún id de la plantilla.

Los resultados sellados llevan el id y el tenant dentro de su huella: al copiarlos se vuelve a calcular la
huella de cada eslabón con los datos del destino, de modo que la cadena del clon es íntegra y propia. Como la
plantilla tiene como máximo los dos sellos de DIAG-11 (prueba y real), el clon tampoco pasa de dos.
Quedan fuera los estados de DIAG-12: la plantilla no los tiene y llevan ids de tareas de otra sala.
"""
from __future__ import annotations

import dataclasses
import uuid
from typing import Any

from sqlalchemy import column, select, table, text
from sqlalchemy.dialects.postgresql import JSONB, insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from features.diagnostico.domain.models import estado_desde_nivel_asignado
from features.diagnostico.services.engine import cargar_banco_preguntas_raw
from features.diagnostico.services.resultados_engine import (
    SELLOS_MAXIMOS,
    _fila_a_resultado,
    calcular_huella,
    tipo_de_secuencia,
)

MapaIds = dict[str, str]

_ESPACIO = uuid.UUID("8c2f4e1a-6b3d-4f0e-a7c5-2d9e1b4f6a08")

# Columnas por tabla, sin tenant_id (lo fija el destino).
_RESPUESTAS = ("pregunta_id", "control", "dimension", "estado", "nivel_asignado", "nivel_evidencia", "criticidad",
               "es_critica", "riesgo_base", "respondido_por", "actualizado_en", "no_aplica",
               "justificacion_no_aplica", "justificado_por", "justificado_en")
_ASIGNACIONES = ("id", "dimension", "responsable_user_id", "asignado_por", "asignado_en")
_RESULTADOS = ("id", "secuencia", "sellado_por", "sellado_en", "normativa", "version_normativa", "tamano",
               "perfil", "respuestas", "indicadores", "huella_anterior", "huella", "tipo")
_JSON = frozenset({"perfil", "respuestas", "indicadores"})
_CON_DEFECTO = frozenset({"actualizado_en", "asignado_en"})
_TABLAS_DE_LA_SALA = ("diagnostico_respuestas", "diagnostico_asignaciones", "diagnostico_resultados")
# Datos de la siembra: niveles que se repiten en ciclo, para que la plantilla muestre cada color.
_NIVELES_ASIGNADOS = (3, 2, 4, 1, 3, 5)
_NIVELES_EVIDENCIA = (1, 0, 2, 1, 3)


def _id_nuevo(destino: str, id_origen: str) -> str:
    return str(uuid.uuid5(_ESPACIO, f"{destino}|{id_origen}"))


async def _tenant(session: AsyncSession, tenant_id: str) -> None:
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant_id})


def _tabla(nombre: str, columnas: tuple[str, ...]):
    """Tabla de Core con identificadores citados; el nombre sale solo de la lista cerrada de la sala."""
    assert nombre in _TABLAS_DE_LA_SALA
    return table(nombre, column("tenant_id"), *[column(c, JSONB) if c in _JSON else column(c) for c in columnas])


async def _leer(session: AsyncSession, tabla: str, columnas: tuple[str, ...], tenant_id: str,
                orden: str) -> list[dict[str, Any]]:
    t = _tabla(tabla, columnas)
    consulta = select(*[t.c[c] for c in columnas]).where(t.c.tenant_id == tenant_id).order_by(t.c[orden])
    return [dict(f) for f in (await session.execute(consulta)).mappings().all()]


async def _insertar(session: AsyncSession, tabla: str, columnas: tuple[str, ...], tenant_id: str,
                    fila: dict[str, Any]) -> None:
    # Una marca de tiempo en None se omite para que la base aplique su valor por defecto.
    cols = tuple(c for c in columnas if not (c in _CON_DEFECTO and fila.get(c) is None))
    valores = {c: fila[c] for c in cols}
    valores["tenant_id"] = tenant_id
    await session.execute(pg_insert(_tabla(tabla, columnas)).values(**valores).on_conflict_do_nothing())


async def _administrador(session: AsyncSession, tenant_id: str) -> str:
    fila = (await session.execute(
        text("SELECT user_id FROM user_tenant_roles WHERE tenant_id = :t AND role = 'admin_organizacion' "
             "AND (valid_to IS NULL OR valid_to > now()) ORDER BY user_id LIMIT 1"), {"t": tenant_id})).first()
    return fila[0] if fila else "demo-sistema"


async def clonar_desde_plantilla(session: AsyncSession, origen: str, destino: str, mapa_ids: MapaIds) -> MapaIds:
    """Copia las filas de la sala del tenant `origen` al `destino` y devuelve el mapa de ids ampliado."""
    if origen == destino:
        raise ValueError("El tenant destino de la copia debe ser distinto del de origen.")
    await _tenant(session, origen)
    respuestas = await _leer(session, "diagnostico_respuestas", _RESPUESTAS, origen, "pregunta_id")
    asignaciones = await _leer(session, "diagnostico_asignaciones", _ASIGNACIONES, origen, "id")
    resultados = await _leer(session, "diagnostico_resultados", _RESULTADOS, origen, "secuencia")
    if len(resultados) > SELLOS_MAXIMOS:
        raise ValueError(f"La plantilla tiene más de {SELLOS_MAXIMOS} sellos de diagnóstico.")

    mapa: MapaIds = dict(mapa_ids)
    for fila in asignaciones + resultados:
        mapa[fila["id"]] = _id_nuevo(destino, fila["id"])

    await _tenant(session, destino)
    admin_destino = await _administrador(session, destino)

    def persona(id_origen: str | None) -> str | None:
        return None if id_origen is None else mapa_ids.get(id_origen, admin_destino)

    for r in respuestas:
        await _insertar(session, "diagnostico_respuestas", _RESPUESTAS, destino, {
            **r, "respondido_por": persona(r["respondido_por"]), "justificado_por": persona(r["justificado_por"])})
    for a in asignaciones:
        # Un responsable que no es una persona del mapa queda sin asignar: nunca apunta a la plantilla.
        await _insertar(session, "diagnostico_asignaciones", _ASIGNACIONES, destino, {
            **a, "id": mapa[a["id"]], "responsable_user_id": mapa_ids.get(a["responsable_user_id"]),
            "asignado_por": persona(a["asignado_por"])})

    anterior: str | None = None
    for fila in resultados:
        sellado = _fila_a_resultado({**fila, "tenant_id": origen})
        sellado = dataclasses.replace(
            sellado, id=mapa[fila["id"]], tenant_id=destino, sellado_por=persona(fila["sellado_por"]),
            huella_anterior=anterior if anterior is not None else sellado.huella_anterior)
        sellado = dataclasses.replace(sellado, huella=calcular_huella(sellado.contenido()))
        anterior = sellado.huella
        contenido = sellado.contenido()
        await _insertar(session, "diagnostico_resultados", _RESULTADOS, destino, {
            "id": sellado.id, "secuencia": sellado.secuencia, "sellado_por": sellado.sellado_por,
            "sellado_en": sellado.sellado_en, "normativa": sellado.normativa,
            "version_normativa": sellado.version_normativa, "tamano": sellado.tamano,
            "perfil": contenido["perfil"], "respuestas": contenido["respuestas"],
            "indicadores": contenido["indicadores"], "huella_anterior": sellado.huella_anterior,
            "huella": sellado.huella, "tipo": tipo_de_secuencia(sellado.secuencia)})
    return mapa


async def sembrar_en_plantilla(session: AsyncSession, plantilla_id: str, datos: dict) -> None:
    """Siembra idempotente del bloque `diagnostico` de la plantilla; no hace commit.

    El diagnóstico de la plantilla está «en revisión»: solo tiene respuestas (las primeras `respondidas`
    preguntas del banco) y ningún sello, así que no gasta ninguno de los dos de DIAG-11.
    """
    respondidas = int((datos or {}).get("respondidas") or 0)
    if respondidas <= 0:
        return
    await _tenant(session, plantilla_id)
    admin = await _administrador(session, plantilla_id)
    banco = sorted(cargar_banco_preguntas_raw(), key=lambda p: p["id"])[:respondidas]
    for i, pregunta in enumerate(banco):
        nivel = _NIVELES_ASIGNADOS[i % len(_NIVELES_ASIGNADOS)]
        criticidad = int(pregunta["criticidad"])
        await _insertar(session, "diagnostico_respuestas", _RESPUESTAS, plantilla_id, {
            "pregunta_id": int(pregunta["id"]), "control": pregunta["control"], "dimension": pregunta["dimensionId"],
            "estado": estado_desde_nivel_asignado(nivel).value, "nivel_asignado": nivel,
            "nivel_evidencia": _NIVELES_EVIDENCIA[i % len(_NIVELES_EVIDENCIA)], "criticidad": criticidad,
            "es_critica": bool(pregunta.get("esEstructural")),
            "riesgo_base": min(10, max(1, (5 - nivel) * criticidad)), "respondido_por": admin,
            "actualizado_en": None, "no_aplica": False, "justificacion_no_aplica": None,
            "justificado_por": None, "justificado_en": None})
