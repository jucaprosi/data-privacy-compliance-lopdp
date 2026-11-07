# -*- coding: utf-8 -*-
# ¤entorno-pruebas
# ¤seguridad
"""EP-08: en los entornos aislados el correo sale solo hacia destinatarios permitidos."""
from __future__ import annotations

import asyncio
import logging

import pytest

from features.notificaciones.notificaciones_service import (
    CanalNotificacion,
    CorreoLoteNotificacion,
    Destinatario,
    EstadoEntorno,
    EstadoEnvio,
    NotificadorEntornoPermitido,
    NotificadorFalso,
    notificador_configurado,
)


class _Espia(NotificadorFalso):
    def __init__(self) -> None:
        super().__init__()
        self.llamadas: list[CorreoLoteNotificacion] = []

    async def enviar_correo(self, correo):
        self.llamadas.append(correo)
        return await super().enviar_correo(correo)


def _correo(email: str) -> CorreoLoteNotificacion:
    return CorreoLoteNotificacion(
        lote_id="lote-1",
        destinatario=Destinatario(user_id="u1", email=email, nombre="Persona", tenant_id="t1"),
        canal=CanalNotificacion.CORREO,
        asunto="Asunto",
        cuerpo_texto="Texto",
        cuerpo_html="<p>Texto</p>",
        tareas=(),
    )


def _enviar(notificador, email):
    return asyncio.run(notificador.enviar_correo(_correo(email)))


@pytest.mark.parametrize("entorno", ["pruebas", "demo"])
def test_retiene_no_permitidos_en_entorno_aislado(entorno):
    espia = _Espia()
    n = NotificadorEntornoPermitido(espia, entorno=entorno, permitidos="ana@pruebas.invalid")
    resultado = _enviar(n, "otro@pruebas.invalid")
    assert resultado.estado == EstadoEntorno.RETENIDO_POR_ENTORNO
    assert resultado.estado != EstadoEnvio.ENVIADO
    assert espia.llamadas == []
    assert _enviar(n, "ANA@pruebas.invalid ").estado == EstadoEnvio.ENVIADO
    assert len(espia.llamadas) == 1


@pytest.mark.parametrize("lista", ["", "  ", " , ,"])
def test_lista_vacia_no_sale_ningun_correo(lista):
    espia = _Espia()
    n = NotificadorEntornoPermitido(espia, entorno="pruebas", permitidos=lista)
    for email in ("a@x.invalid", "b@pruebas.invalid", ""):
        assert _enviar(n, email).estado == EstadoEntorno.RETENIDO_POR_ENTORNO
    assert espia.llamadas == []


def test_dominio_sin_falsos_positivos():
    espia = _Espia()
    n = NotificadorEntornoPermitido(espia, entorno="pruebas", permitidos="@example.test")
    assert _enviar(n, "x@example.test").estado == EstadoEnvio.ENVIADO
    for email in ("x@example.test.com", "x@sub.example.test", "x@otroexample.test", "example.test"):
        assert _enviar(n, email).estado == EstadoEntorno.RETENIDO_POR_ENTORNO
    assert len(espia.llamadas) == 1


@pytest.mark.parametrize("entorno", ["production", "development", "test", ""])
def test_delegacion_identica_fuera_de_pruebas(entorno):
    espia = _Espia()
    n = NotificadorEntornoPermitido(espia, entorno=entorno, permitidos="")
    correo = _correo("cualquiera@x.invalid")
    resultado = asyncio.run(n.enviar_correo(correo))
    assert espia.llamadas == [correo]
    assert resultado.estado == EstadoEnvio.ENVIADO


def test_registro_sin_la_direccion_retenida(caplog):
    n = NotificadorEntornoPermitido(_Espia(), entorno="pruebas", permitidos="")
    with caplog.at_level(logging.DEBUG):
        _enviar(n, "secreta@retenida.invalid")
    assert caplog.records
    assert "secreta" not in caplog.text and "retenida.invalid" not in caplog.text


def test_notificador_configurado_va_envuelto(monkeypatch):
    monkeypatch.setenv("APP_ENV", "pruebas")
    monkeypatch.setenv("ENTORNO_CORREOS_PERMITIDOS", "")
    n = notificador_configurado()
    assert isinstance(n, NotificadorEntornoPermitido)
    assert _enviar(n, "a@x.invalid").estado == EstadoEntorno.RETENIDO_POR_ENTORNO
