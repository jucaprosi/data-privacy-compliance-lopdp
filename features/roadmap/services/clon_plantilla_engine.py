# -*- coding: utf-8 -*-
# ¤demo ¤adpa ¤seguridad-tenant
"""DEMO-03c: copia y siembra de la sala Hoja de Ruta para la demo «Cooperativa Demo».

`clonar_desde_plantilla` copia solo las filas de esta sala (hallazgos, hojas de ruta, olas, tareas y
dependencias) del tenant plantilla al tenant nuevo. Cada id nuevo se deriva de forma determinista del
tenant destino y del id de origen (uuid5): repetir la copia en la misma transacción no duplica nada.
Nunca escribe en el tenant de origen, nunca hace commit y no deja en el mapa ni en las filas ningún id de
la plantilla. Quedan fuera la evidencia y el registro de auditoría (la evidencia es de la sala Evidencias).
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import JSON, column, select, table, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

MapaIds = dict[str, str]

_ESPACIO = uuid.UUID("5f0c7a52-3d0e-4b57-9c53-0d3a6c1b7d03")

# Columnas por tabla, sin tenant_id (lo fija el destino).
_HALLAZGOS = ("id", "origen", "origen_ref", "control_ref", "dimension", "severidad", "titulo",
              "descripcion", "estado", "creado_por", "creado_en", "actualizado_en")
_ROADMAPS = ("id", "created_at", "updated_at", "status", "variables_json", "summary", "score_objetivo")
_OLAS = ("id", "roadmap_id", "name", "start_date", "end_date", "objective", "sort_order")
_TAREAS = ("id", "wave_id", "area_id", "control_ref", "dimension", "title", "description", "owner", "priority",
           "effort_hours", "start_date", "end_date", "status", "completed_at", "kpi", "deliverable",
           "evidence_required", "hallazgo_id")

# Datos de la siembra: un hallazgo y una tarea por cada elemento del bloque `roadmap` del JSON.
_ESTADO_TAREA = {"pendiente": "pendiente", "en_curso": "en_progreso", "en_validacion": "en_progreso"}
_ESTADO_HALLAZGO = {"pendiente": "abierto", "en_curso": "en_tratamiento", "en_validacion": "en_tratamiento"}
_CONTROLES = (("P1", "D01"), ("P12", "D03"), ("P30", "D05"))
_INICIO, _FIN = "2026-12-01", "2027-02-28"


def _id_nuevo(destino: str, id_origen: str) -> str:
    return str(uuid.uuid5(_ESPACIO, f"{destino}|{id_origen}"))


async def _tenant(session: AsyncSession, tenant_id: str) -> None:
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant_id})


_TABLAS_DE_LA_SALA = ("hallazgos", "roadmaps", "roadmap_waves", "roadmap_tasks")
_JSON = frozenset({"variables_json", "evidence_required"})


def _tabla(nombre: str, columnas: tuple[str, ...]):
    """Tabla de Core con identificadores citados; el nombre sale solo de la lista cerrada de la sala."""
    assert nombre in _TABLAS_DE_LA_SALA
    return table(nombre, column("tenant_id"), *[column(c, JSON) if c in _JSON else column(c) for c in columnas])


async def _leer(session: AsyncSession, tabla: str, columnas: tuple[str, ...], tenant_id: str) -> list[dict[str, Any]]:
    t = _tabla(tabla, columnas)
    consulta = select(*[t.c[c] for c in columnas]).where(t.c.tenant_id == tenant_id).order_by(t.c.id)
    return [dict(f) for f in (await session.execute(consulta)).mappings().all()]


_CON_DEFECTO = frozenset({"created_at", "updated_at", "creado_en", "actualizado_en"})


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
    hallazgos = await _leer(session, "hallazgos", _HALLAZGOS, origen)
    roadmaps = await _leer(session, "roadmaps", _ROADMAPS, origen)
    olas = await _leer(session, "roadmap_waves", _OLAS, origen)
    tareas = await _leer(session, "roadmap_tasks", _TAREAS, origen)
    ids_tareas = [t["id"] for t in tareas]
    dependencias = []
    if ids_tareas:
        dependencias = [dict(f) for f in (await session.execute(
            text("SELECT task_id, depends_on_task_id FROM task_dependencies WHERE task_id = ANY(:ids) "
                 "ORDER BY task_id, depends_on_task_id"), {"ids": ids_tareas})).mappings().all()]

    mapa: MapaIds = dict(mapa_ids)
    for fila in hallazgos + roadmaps + olas + tareas:
        mapa[fila["id"]] = _id_nuevo(destino, fila["id"])

    await _tenant(session, destino)
    admin_destino = await _administrador(session, destino)
    for h in hallazgos:
        await _insertar(session, "hallazgos", _HALLAZGOS, destino, {
            **h, "id": mapa[h["id"]], "creado_por": mapa_ids.get(h["creado_por"], admin_destino)})
    for r in roadmaps:
        await _insertar(session, "roadmaps", _ROADMAPS, destino, {**r, "id": mapa[r["id"]]})
    for o in olas:
        await _insertar(session, "roadmap_waves", _OLAS, destino, {
            **o, "id": mapa[o["id"]], "roadmap_id": mapa[o["roadmap_id"]]})
    for t in tareas:
        await _insertar(session, "roadmap_tasks", _TAREAS, destino, {
            **t, "id": mapa[t["id"]], "wave_id": mapa[t["wave_id"]],
            "area_id": mapa_ids.get(t["area_id"]) if t["area_id"] else None,
            "hallazgo_id": mapa.get(t["hallazgo_id"]) if t["hallazgo_id"] else None})
    for d in dependencias:
        if d["depends_on_task_id"] in mapa:
            await session.execute(
                text("INSERT INTO task_dependencies (task_id, depends_on_task_id) VALUES (:a, :b) "
                     "ON CONFLICT DO NOTHING"),
                {"a": mapa[d["task_id"]], "b": mapa[d["depends_on_task_id"]]})
    return mapa


async def sembrar_en_plantilla(session: AsyncSession, plantilla_id: str, datos: dict) -> None:
    """Siembra idempotente del bloque `roadmap` de la plantilla; no hace commit."""
    elementos = (datos or {}).get("hallazgos_y_tareas") or []
    if not elementos:
        return
    await _tenant(session, plantilla_id)
    admin = await _administrador(session, plantilla_id)
    id_ruta, id_ola = _id_nuevo(plantilla_id, "ruta"), _id_nuevo(plantilla_id, "ola")
    await _insertar(session, "roadmaps", _ROADMAPS, plantilla_id, {
        "id": id_ruta, "created_at": None, "updated_at": None, "status": "active",
        "variables_json": {"plazo_meses": 3, "presupuesto": 0, "moneda": "USD", "equipo": ["Equipo ficticio"],
                           "dpo": "DPO ficticio", "idioma": "ES"},
        "summary": "Hoja de ruta ficticia de la demo", "score_objetivo": None})
    await _insertar(session, "roadmap_waves", _OLAS, plantilla_id, {
        "id": id_ola, "roadmap_id": id_ruta, "name": "Ola 1 (ficticia)", "start_date": _INICIO,
        "end_date": _FIN, "objective": "Poner en marcha las acciones de la demo", "sort_order": 1})
    for i, e in enumerate(elementos):
        control, dimension = _CONTROLES[i % len(_CONTROLES)]
        id_h, id_t = _id_nuevo(plantilla_id, f"hallazgo-{i}"), _id_nuevo(plantilla_id, f"tarea-{i}")
        estado = e.get("estado", "pendiente")
        await _insertar(session, "hallazgos", _HALLAZGOS, plantilla_id, {
            "id": id_h, "origen": "diagnostico", "origen_ref": f"demo-ruta-{i}", "control_ref": control,
            "dimension": dimension, "severidad": "media", "titulo": e["titulo"], "descripcion": None,
            "estado": _ESTADO_HALLAZGO[estado], "creado_por": admin, "creado_en": None, "actualizado_en": None})
        await _insertar(session, "roadmap_tasks", _TAREAS, plantilla_id, {
            "id": id_t, "wave_id": id_ola, "area_id": None, "control_ref": control, "dimension": dimension,
            "title": e["titulo"], "description": None, "owner": None, "priority": "media",
            "effort_hours": 8, "start_date": _INICIO, "end_date": _FIN, "status": _ESTADO_TAREA[estado],
            "completed_at": None, "kpi": "Acción cerrada", "deliverable": "Evidencia de la acción",
            "evidence_required": ["Documento de respaldo"], "hallazgo_id": id_h})
