# -*- coding: utf-8 -*-
# ¤demo
"""Entrada del vendedor a su demo (DEMO-02, FLUJOS §1.1, invariantes 60 a 63).

Orden: lista autorizada (403) → candado → vencer inactivas y la demo previa del vendedor (reemplazada) →
tope de 20 (409) → copia de la plantilla sala por sala, por sus pasillos → alta de la sesión como
administrador → evento `DEMO_INICIADA`. Todo, menos la lista, dentro de un SAVEPOINT: si algo falla no
queda ni sesión ni organización a medias (503 `DEMO_NO_DISPONIBLE`). No hace commit.
"""
from __future__ import annotations

import importlib
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.db.session import fijar_contexto_rls
from app_core.pasillo import organizacion as pasillo_organizacion
from features.demo.domain import vendedores
from features.demo.domain.contrato import EstadoDemo, ordenar
from features.demo.domain.errores import DEMO_NO_AUTORIZADO, DEMO_NO_DISPONIBLE, DEMO_OCUPADA, ErrorDemo
from features.demo.domain.eventos import EventoDemo
from features.demo.domain.personas import ETIQUETAS, ROL_INICIAL, PersonaDemo
from features.demo.domain.plantilla import ORDEN_DE_SALAS, PLANTILLA_TENANT_ID, MapaIds
from features.demo.domain.sesion import MINUTOS_INACTIVIDAD, TOPE, MotivoFin
from features.demo.repo import sesiones_repo
from features.demo.services import cierre_engine

_log = logging.getLogger(__name__)

Clonador = Callable[[AsyncSession, str, str, MapaIds], Awaitable[MapaIds]]


def _clonador(sala: str) -> Clonador | None:
    """`clonar_desde_plantilla` del pasillo de la sala, o None si la sala aún no lo registra."""
    nombre = f"app_core.pasillo.{sala}"
    try:
        modulo = importlib.import_module(nombre)
    except ModuleNotFoundError as exc:
        if exc.name == nombre:
            return None
        raise
    return getattr(modulo, "clonar_desde_plantilla", None)


async def copiar_plantilla(session: AsyncSession, destino: str) -> tuple[MapaIds, list[str]]:
    """Orquestador: llama a cada sala en `ORDEN_DE_SALAS` con el mapa que acumulan las anteriores.

    Devuelve el mapa final y las salas omitidas por no tener clon registrado. Cualquier fallo se propaga.
    """
    mapa: MapaIds = {}
    omitidas: list[str] = []
    for sala in ORDEN_DE_SALAS:
        clonar = _clonador(sala)
        if clonar is None:
            omitidas.append(sala)
            continue
        mapa = await clonar(session, PLANTILLA_TENANT_ID, destino, mapa)
    return mapa, omitidas


async def _personas(session: AsyncSession, tenant_id: str) -> list[PersonaDemo]:
    """Las personas de la organización demo, leídas por el pasillo de organización."""
    unidades = {a["id"]: a["nombre"] for a in await pasillo_organizacion.listar_areas(session, tenant_id)}
    personas = []
    for u in await pasillo_organizacion.listar_usuarios(session, tenant_id):
        rol = u["roles"][0]
        personas.append(PersonaDemo(u["id"], u["nombre"], rol["role"], ETIQUETAS.get(rol["role"], rol["role"]),
                                    unidades.get(rol["area_id"])))
    return ordenar(personas)


def _vence_en(ultima_actividad: datetime) -> datetime:
    return ultima_actividad + timedelta(minutes=MINUTOS_INACTIVIDAD)


async def entrar(session: AsyncSession, vendedor_sub: str, vendedor_email: str,
                 ahora: datetime | None = None) -> EstadoDemo:
    """Abre la demo del vendedor y devuelve su estado (el 201 de `POST /demo/entrar`)."""
    if not vendedores.es_autorizado(vendedor_email):
        raise ErrorDemo(DEMO_NO_AUTORIZADO)  # antes de escribir nada
    ahora = ahora or datetime.now(timezone.utc)
    try:
        async with session.begin_nested():
            return await _abrir(session, vendedor_sub, vendedor_email.strip().lower(), ahora)
    except ErrorDemo:
        raise
    except Exception as exc:  # noqa: BLE001 - la causa va al registro técnico; el cliente recibe el 503 congelado
        _log.error("DEMO-02: la copia de la plantilla falló (%s)", type(exc).__name__)
        raise ErrorDemo(DEMO_NO_DISPONIBLE) from exc


async def _abrir(session: AsyncSession, sub: str, email: str, ahora: datetime) -> EstadoDemo:
    await sesiones_repo.contar_activas_con_candado(session)  # serializa las entradas
    await cierre_engine.vencer_inactivas(session, ahora)
    previa = await sesiones_repo.obtener_activa(session, sub)
    if previa is not None:
        await cierre_engine.vencer(session, previa, MotivoFin.REEMPLAZADA, ahora)
    if await sesiones_repo.contar_activas_con_candado(session) >= TOPE:
        raise ErrorDemo(DEMO_OCUPADA)

    destino = f"demo-{uuid.uuid4().hex}"
    _mapa, omitidas = await copiar_plantilla(session, destino)
    personas = await _personas(session, destino)
    admin = next((p for p in personas if p.rol == ROL_INICIAL), None)
    if admin is None:
        raise RuntimeError("la copia no dejó la persona administradora")
    sesion = await sesiones_repo.insertar(session, sub, email, destino, admin.usuario_id, ahora)
    await fijar_contexto_rls(session, destino, admin.usuario_id)
    await registrar_evento(
        session, destino, cierre_engine.ENTIDAD, sesion.id, EventoDemo.DEMO_INICIADA.value, admin.usuario_id,
        {"vendedor_email": email, "salas_omitidas": [f"{s}: sin clonar_desde_plantilla registrado" for s in omitidas]},
    )
    organizacion = await pasillo_organizacion.configuracion_de_organizacion(session, destino)
    return EstadoDemo(destino, organizacion["nombre_comercial"], admin, tuple(personas), _vence_en(ahora))
