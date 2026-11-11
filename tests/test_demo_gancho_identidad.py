# -*- coding: utf-8 -*-
# ¤demo
# ¤seguridad
"""DEMO-08 · Gancho de identidad demo en `usuario_verificado()`.

Sin base de datos: el token de Google y la búsqueda de usuario se sustituyen por dobles y se cuentan sus
llamadas. Solo valores simulados y correos `.invalid`; nunca `AUTH_MODE=headers`.

Mutaciones documentadas (ficha DEMO-08); cada una pone en rojo la prueba que se indica:
- M1: quitar `entorno_actual() != "demo"` de `registrar_resolutor_identidad` ⟹ test_registrar_fuera_de_demo.
- M2: quitar la comprobación del segundo registro ⟹ test_un_segundo_registro_falla.
- M3: «falla cerrado»: que un resolutor que devuelve `None` o una persona sin `usuario_id` caiga a
  `usuario_de_identidad` ⟹ test_resolutor_sin_persona_es_demo_vencida.
- M4: que un resolutor que lanza propague su excepción o caiga al camino normal ⟹
  test_resolutor_que_lanza_es_demo_vencida.
- M5: `_resolutor_activo` sin mirar el entorno ⟹ test_resolutor_ignorado_si_el_entorno_no_es_demo.
- M6: llamar al resolutor antes de verificar el token ⟹ test_sin_token_valido_no_se_llama_al_resolutor
  (y test_con_resolutor_devuelve_la_persona_y_no_busca_en_users, que cuenta lo que recibe).
"""
from __future__ import annotations

import ast
import asyncio
import re
from pathlib import Path

import pytest
from fastapi import HTTPException

from app_core import security
from app_core.errors import ErrorNegocio
from app_core.security import IdentidadVerificada, UsuarioAutenticado

SUB = "sub-vendedor-ficticio"
EMAIL = "vendedor@demo.invalid"
PERSONA_ID = "persona-ficticia-dpo"
USUARIO_NORMAL = "usuario-normal-ficticio"


class _Persona:
    """Lo mínimo que devuelve el motor de la demo (`PersonaDemo`)."""

    def __init__(self, usuario_id):
        self.usuario_id = usuario_id


@pytest.fixture
def entorno(monkeypatch):
    monkeypatch.setattr(security, "_resolutor_identidad", None)
    monkeypatch.setenv("APP_ENV", "demo")
    llamadas = {"token": [], "usuario_de_identidad": []}

    async def token(valor):
        llamadas["token"].append(valor)
        if valor != "token-valido":
            raise HTTPException(401, "Token inválido.")
        return IdentidadVerificada(sub=SUB, email=EMAIL)

    async def usuario_de_identidad(_session, identidad):
        llamadas["usuario_de_identidad"].append(identidad.sub)
        return USUARIO_NORMAL

    monkeypatch.setattr(security, "verificar_token_google", token)
    monkeypatch.setattr(security, "usuario_de_identidad", usuario_de_identidad)
    return llamadas


def _pedir(authorization="Bearer token-valido"):
    return asyncio.run(security.usuario_verificado(object(), authorization))


def _resolutor(resultado=None, error=None):
    recibido = []

    async def resolutor(session, sub):
        recibido.append(sub)
        if error is not None:
            raise error
        return resultado

    resolutor.recibido = recibido
    return resolutor


def _es_demo_vencida(excepcion):
    return isinstance(excepcion, ErrorNegocio) and excepcion.code == "DEMO_VENCIDA" and excepcion.status_code == 401


# ----------------------------------------------------------------------------- registro

@pytest.mark.parametrize("valor", ["development", "test", "pruebas", "production", None])
def test_registrar_fuera_de_demo(entorno, monkeypatch, valor):
    if valor is None:
        monkeypatch.delenv("APP_ENV")
    else:
        monkeypatch.setenv("APP_ENV", valor)
    with pytest.raises(RuntimeError, match="DEMO-08"):
        security.registrar_resolutor_identidad(_resolutor(_Persona(PERSONA_ID)))
    assert security._resolutor_identidad is None


def test_registrar_con_entorno_desconocido_no_registra(entorno, monkeypatch):
    monkeypatch.setenv("APP_ENV", "inventado")
    with pytest.raises(Exception):
        security.registrar_resolutor_identidad(_resolutor(_Persona(PERSONA_ID)))
    assert security._resolutor_identidad is None


def test_registrar_en_demo_funciona(entorno):
    resolutor = _resolutor(_Persona(PERSONA_ID))
    security.registrar_resolutor_identidad(resolutor)
    assert security._resolutor_identidad is resolutor


def test_un_segundo_registro_falla(entorno):
    primero = _resolutor(_Persona(PERSONA_ID))
    security.registrar_resolutor_identidad(primero)
    for otro in (primero, _resolutor(_Persona("otra-persona-ficticia"))):
        with pytest.raises(RuntimeError, match="DEMO-08"):
            security.registrar_resolutor_identidad(otro)
    assert security._resolutor_identidad is primero


# ----------------------------------------------------------------------------- sin resolutor: igual que antes

@pytest.mark.parametrize("valor", ["demo", "pruebas", "production"])
def test_sin_resolutor_se_comporta_como_antes(entorno, monkeypatch, valor):
    monkeypatch.setenv("APP_ENV", valor)
    usuario = _pedir()
    assert usuario == UsuarioAutenticado(usuario_id=USUARIO_NORMAL, email=EMAIL, sub=SUB)
    assert entorno["usuario_de_identidad"] == [SUB]


# ----------------------------------------------------------------------------- con resolutor

def test_con_resolutor_devuelve_la_persona_y_no_busca_en_users(entorno):
    resolutor = _resolutor(_Persona(PERSONA_ID))
    security.registrar_resolutor_identidad(resolutor)
    usuario = _pedir()
    assert usuario == UsuarioAutenticado(usuario_id=PERSONA_ID, email=EMAIL, sub=SUB)
    assert resolutor.recibido == [SUB], "el resolutor recibe el sub ya verificado, nada más"
    assert entorno["usuario_de_identidad"] == []


def test_con_resolutor_acepta_un_usuario_autenticado(entorno):
    propio = UsuarioAutenticado(usuario_id=PERSONA_ID, email="persona@demo.invalid", sub=SUB)
    security.registrar_resolutor_identidad(_resolutor(propio))
    assert _pedir() == propio


@pytest.mark.parametrize("resultado", [None, _Persona(None), _Persona(""), _Persona(7), object(), "texto"])
def test_resolutor_sin_persona_es_demo_vencida(entorno, resultado):
    security.registrar_resolutor_identidad(_resolutor(resultado))
    with pytest.raises(ErrorNegocio) as error:
        _pedir()
    assert _es_demo_vencida(error.value)
    assert entorno["usuario_de_identidad"] == [], "nunca cae al camino normal"


@pytest.mark.parametrize("fallo", [
    RuntimeError("falla del motor"),
    HTTPException(503, "sin base"),
    ValueError("dato raro"),
])
def test_resolutor_que_lanza_es_demo_vencida(entorno, fallo):
    security.registrar_resolutor_identidad(_resolutor(error=fallo))
    with pytest.raises(ErrorNegocio) as error:
        _pedir()
    assert _es_demo_vencida(error.value)
    assert "falla del motor" not in str(error.value) and error.value.__cause__ is None
    assert entorno["usuario_de_identidad"] == []


def test_demo_vencida_usa_el_catalogo_de_la_demo(entorno):
    import importlib

    errores = importlib.import_module("features.demo.domain.errores")
    security.registrar_resolutor_identidad(_resolutor(None))
    with pytest.raises(ErrorNegocio) as error:
        _pedir()
    assert error.value.detail == errores.DEMO_VENCIDA.mensaje_defecto
    assert error.value.status_code == errores.DEMO_VENCIDA.status_code == 401


# ----------------------------------------------------------------------------- el gancho no se activa solo

def test_resolutor_ignorado_si_el_entorno_no_es_demo(entorno, monkeypatch):
    resolutor = _resolutor(_Persona(PERSONA_ID))
    security.registrar_resolutor_identidad(resolutor)
    monkeypatch.setenv("APP_ENV", "production")
    usuario = _pedir()
    assert usuario.usuario_id == USUARIO_NORMAL
    assert resolutor.recibido == []


@pytest.mark.parametrize("authorization", [None, "", "Basic abc", "Bearer ", "Bearer token-falso"])
def test_sin_token_valido_no_se_llama_al_resolutor(entorno, authorization):
    resolutor = _resolutor(_Persona(PERSONA_ID))
    security.registrar_resolutor_identidad(resolutor)
    with pytest.raises(HTTPException) as error:
        _pedir(authorization)
    assert error.value.status_code == 401
    assert resolutor.recibido == []
    assert entorno["usuario_de_identidad"] == []


def test_la_seccion_no_lee_el_entorno_ni_el_modo_de_cabeceras():
    """El entorno sale solo de EP-01 y la identidad solo del token: la sección no usa `os` ni el modo de cabeceras (se mira el AST, no los textos)."""
    texto = Path(security.__file__).read_text(encoding="utf-8")
    seccion = re.search(r"# --- INICIO DEMO-08 ---\n(.*?)# --- FIN DEMO-08 ---", texto, re.S)
    assert seccion, "falta la sección DEMO-08 en app_core/security.py"
    arbol = ast.parse(seccion.group(1))
    nombres = {n.id for n in ast.walk(arbol) if isinstance(n, ast.Name)}
    nombres |= {n.attr for n in ast.walk(arbol) if isinstance(n, ast.Attribute)}
    for prohibido in ("os", "environ", "getenv", "modo_autenticacion", "MODO_HEADERS", "Header", "headers"):
        assert prohibido not in nombres, prohibido
