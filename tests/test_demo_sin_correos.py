# -*- coding: utf-8 -*-
# ¤demo
"""DEMO-06: con APP_ENV=demo y la lista de permitidos vacía no sale ningún correo (invariante 62).

La guardia es de EP-08 (`destinatarios_entorno.py`); aquí solo se prueba para la demo, a través de la
compuerta de notificaciones y con el notificador que usa la API (`notificador_configurado`). El
proveedor se sustituye por un espía: si la guardia deja pasar algo, el espía lo registra.
Solo valores generados: destinos `.invalid` y dominios reservados (RFC 2606), nunca direcciones reales.
"""
from __future__ import annotations

import asyncio

import pytest

from features.notificaciones.notificaciones_service import (
    CanalNotificacion,
    CorreoLoteNotificacion,
    Destinatario,
    EstadoEnvio,
    NotificadorFalso,
    TareaAsignadaItem,
    despachar_lote_notificaciones,
    enviar_recordatorios,
    notificador_configurado,
    notificar_asignaciones_lote,
)

BASE_URL = "https://demo.evydentia.invalid"

# Destinos ficticios `.invalid` y destinos con forma de dirección real (dominios reservados).
DESTINOS = [
    "admin@cooperativa-demo.invalid",
    "dpo@cooperativa-demo.invalid",
    "vendedor@ventas.invalid",
    "persona@example.com",
    "Persona.Real@Example.org",
]


class _Espia(NotificadorFalso):
    """Proveedor falso que registra cada correo que le llega."""

    def __init__(self) -> None:
        super().__init__()
        self.llamadas: list[CorreoLoteNotificacion] = []

    async def enviar_correo(self, correo):
        self.llamadas.append(correo)
        return await super().enviar_correo(correo)


@pytest.fixture(params=["", "   ", " , ,"], ids=["vacia", "espacios", "comas"])
def notificador_demo(request, monkeypatch):
    monkeypatch.setenv("APP_ENV", "demo")
    monkeypatch.setenv("ENTORNO_CORREOS_PERMITIDOS", request.param)
    notificador = notificador_configurado()
    espia = _Espia()
    notificador.interno = espia  # el proveedor de verdad nunca se toca
    return notificador, espia


def _destinatario(i: int, email: str) -> Destinatario:
    return Destinatario(user_id=f"persona-{i}", email=email, nombre=f"Persona {i}", tenant_id="tenant-demo-generado")


def _tarea(i: int) -> TareaAsignadaItem:
    return TareaAsignadaItem(task_id=f"tarea-{i}", titulo=f"Tarea {i}", control_ref="C-01", prioridad="alta")


def _correo(i: int, email: str) -> CorreoLoteNotificacion:
    return CorreoLoteNotificacion(
        lote_id=f"lote-{i}",
        destinatario=_destinatario(i, email),
        canal=CanalNotificacion.CORREO,
        asunto="Asunto",
        cuerpo_texto="Texto",
        cuerpo_html="<p>Texto</p>",
        tareas=(),
    )


def test_asignacion_de_tareas_no_envia(notificador_demo):
    notificador, espia = notificador_demo
    asignaciones = [(_destinatario(i, e), _tarea(i)) for i, e in enumerate(DESTINOS)]
    resultados = asyncio.run(notificar_asignaciones_lote(asignaciones, BASE_URL, notificador))
    assert espia.llamadas == []
    assert len(resultados) == len(DESTINOS)
    assert all(r.estado != EstadoEnvio.ENVIADO for r in resultados)


def test_recordatorios_no_envian(notificador_demo):
    notificador, espia = notificador_demo
    for i, email in enumerate(DESTINOS):
        enviado = asyncio.run(enviar_recordatorios(_destinatario(i, email), [(_tarea(i), "7dias")], BASE_URL, notificador))
        assert enviado is False
    assert espia.llamadas == []


def test_despacho_directo_no_envia(notificador_demo):
    notificador, espia = notificador_demo
    correos = [_correo(i, e) for i, e in enumerate(DESTINOS)]
    resultados = asyncio.run(despachar_lote_notificaciones(correos, notificador))
    assert espia.llamadas == []
    assert all(r.estado != EstadoEnvio.ENVIADO for r in resultados)


def test_demo_en_mayusculas_tambien_retiene(monkeypatch):
    monkeypatch.setenv("APP_ENV", " DEMO ")
    monkeypatch.setenv("ENTORNO_CORREOS_PERMITIDOS", "")
    notificador = notificador_configurado()
    espia = _Espia()
    notificador.interno = espia
    asyncio.run(notificador.enviar_correo(_correo(0, DESTINOS[0])))
    assert espia.llamadas == []


def test_control_fuera_de_demo_el_espia_si_recibe(monkeypatch):
    """Sin esta comprobación, un espía roto haría pasar las pruebas anteriores sin probar nada."""
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("ENTORNO_CORREOS_PERMITIDOS", "")
    notificador = notificador_configurado()
    espia = _Espia()
    notificador.interno = espia
    asyncio.run(notificador.enviar_correo(_correo(0, DESTINOS[0])))
    assert len(espia.llamadas) == 1
