# ¤seguridad ¤seguridad-tenant ¤arbitro
"""SEC-23: toda ruta de la API bajo /api/v1 exige autenticación, salvo una lista blanca justificada.

Árbitro estructural: recorre las rutas de la app y exige que su árbol de dependencias pase por una de
las compuertas que verifican token y membresía (`obtener_tenant_id_actual`, `get_context` o
`get_usuario_autenticado`). Árbitro dinámico (modo oidc, sin base de datos): el asistente de
implementación responde 401 sin token (m1), 403 sin membresía en la organización de la cabecera (m2)
y 200 a un miembro.
"""
from __future__ import annotations

import inspect
import re
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from api.dependencies import obtener_tenant_id_actual
from api.rbac import get_context, get_usuario_autenticado
from app_core import security
from main import app

COMPUERTAS = {obtener_tenant_id_actual, get_context, get_usuario_autenticado, security.get_current_tenant}
# Una dependencia propia de un router también autentica si su código llama a una función que verifica
# el token (p. ej. `_contexto_rat` llama a `get_usuario_autenticado` en su cuerpo).
VERIFICADORAS = re.compile(
    r"\b(usuario_verificado|verificar_token_google|autenticar_en_tenant|get_usuario_autenticado|"
    r"obtener_tenant_id_actual|get_current_tenant|get_context)\s*\("
)

# Lista blanca explícita y corta: (método, ruta) -> justificación.
LISTA_BLANCA: dict[tuple[str, str], str] = {
    ("GET", "/api/v1/health"): "Sonda de vida del balanceador y del arnés; no lee datos ni llama al modelo.",
    ("GET", "/api/v1/entorno"): "Indica al frontend el entorno (demo, pruebas) antes de iniciar sesión; sin datos de organización.",
}

# Rutas abiertas que ya estaban en main al cerrar SEC-23 (2026-11-13). No son de esta ficha: quedan
# congeladas aquí hasta que Seguridad decida, una por una, si pasan a la lista blanca o a una compuerta.
# Una ruta nueva sin autenticación no entra aquí: hace fallar la prueba.
PENDIENTES_SEGURIDAD: frozenset[tuple[str, str]] = frozenset({
    ("GET", "/api/v1/aceptar/{token}"),
    ("POST", "/api/v1/aceptar/{token}"),
    ("GET", "/api/v1/diagnostico/dimensiones"),
    ("POST", "/api/v1/firma/webhook"),
    ("GET", "/api/v1/niif18/doctrina"),
    ("POST", "/api/v1/niif18/exportar/excel"),
    ("POST", "/api/v1/niif18/exportar/informe"),
    ("POST", "/api/v1/niif18/exportar/pdf"),
    ("POST", "/api/v1/niif18/informe"),
    ("POST", "/api/v1/niif18/mpm"),
    ("POST", "/api/v1/niif18/procesar-balance"),
    ("POST", "/api/v1/niif18/recalcular-subtotales"),
    ("POST", "/api/v1/riesgos/mtge/evaluar"),
})

PROPIA, AJENA = "org-propia-sec23", "org-ajena-sec23"
RUTAS_ASISTENTE = [("GET", "/api/v1/ai_copilot/estado"), ("POST", "/api/v1/ai_copilot/consulta")]


def _verifica_en_su_cuerpo(funcion) -> bool:
    try:
        return bool(VERIFICADORAS.search(inspect.getsource(funcion)))
    except (OSError, TypeError):
        return False


def _exige_autenticacion(dependant) -> bool:
    for d in dependant.dependencies:
        if d.call in COMPUERTAS or _verifica_en_su_cuerpo(d.call) or _exige_autenticacion(d):
            return True
    return False


def _contextos_api():
    """Rutas efectivas de la app (APIRoute directa o dentro de un router incluido) bajo /api/v1."""
    for r in app.routes:
        contextos = r.effective_route_contexts() if hasattr(r, "effective_route_contexts") else [r]
        for ctx in contextos:
            if hasattr(ctx, "dependant") and getattr(ctx, "path", "").startswith("/api/v1"):
                yield ctx


def _rutas_api() -> set[tuple[str, str, bool]]:
    rutas = set()
    for ctx in _contextos_api():
        protegida = _exige_autenticacion(ctx.dependant)
        for m in set(ctx.methods or ()) - {"HEAD", "OPTIONS"}:
            rutas.add((m, ctx.path, protegida))
    assert len(rutas) > 20, "El recorrido no encontró las rutas de la API: revise cómo se registran los routers"
    return rutas


def test_toda_ruta_api_exige_autenticacion_salvo_lista_blanca():
    abiertas = {(m, p) for m, p, protegida in _rutas_api() if not protegida}
    sin_justificar = abiertas - set(LISTA_BLANCA) - PENDIENTES_SEGURIDAD
    assert not sin_justificar, f"Rutas de /api/v1 sin autenticación ni entrada en la lista blanca: {sorted(sin_justificar)}"


def test_lista_blanca_sin_entradas_obsoletas_ni_vacias():
    registradas = {(m, p) for m, p, _ in _rutas_api()}
    for clave, motivo in LISTA_BLANCA.items():
        assert clave in registradas, f"Entrada obsoleta en la lista blanca: {clave}"
        assert motivo.strip(), f"Entrada sin justificación: {clave}"
    abiertas = {(m, p) for m, p, protegida in _rutas_api() if not protegida}
    cerradas = PENDIENTES_SEGURIDAD - abiertas
    assert not cerradas, f"Ya exigen autenticación; quítelas de PENDIENTES_SEGURIDAD: {sorted(cerradas)}"


def test_el_asistente_esta_tras_la_compuerta():
    protegidas = {(m, p) for m, p, protegida in _rutas_api() if protegida}
    for ruta in RUTAS_ASISTENTE:
        assert ruta in protegidas, f"{ruta} no exige autenticación"


class _SesionFalsa:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def commit(self):
        return None


@pytest.fixture
def cliente(monkeypatch):
    """App real en modo oidc; la sesión de base de datos y los roles se simulan."""
    monkeypatch.setenv("AUTH_MODE", "oidc")
    monkeypatch.setattr(sys.modules["app_core.db.session"], "async_session_factory", _SesionFalsa)

    async def roles(_sesion, tenant_id, _usuario):
        return {"implementador"} if tenant_id == PROPIA else set()

    monkeypatch.setattr(security, "roles_activos", roles)
    return TestClient(app)


def _con_usuario_verificado(monkeypatch):
    monkeypatch.setattr(security, "usuario_verificado",
                        AsyncMock(return_value=SimpleNamespace(usuario_id="usuario-sec23")))


def _pedir(cliente, metodo, ruta, cabeceras):
    cuerpo = {"pregunta": "¿Qué exige el artículo 37?"} if metodo == "POST" else None
    return cliente.request(metodo, ruta, headers=cabeceras, json=cuerpo)


@pytest.mark.parametrize("metodo,ruta", RUTAS_ASISTENTE)
def test_m1_sin_token_responde_401(cliente, metodo, ruta):
    r = _pedir(cliente, metodo, ruta, {"X-Tenant-ID": PROPIA})
    assert r.status_code == 401, r.text


@pytest.mark.parametrize("metodo,ruta", RUTAS_ASISTENTE)
def test_m2_sin_membresia_en_la_organizacion_responde_403(cliente, monkeypatch, metodo, ruta):
    _con_usuario_verificado(monkeypatch)
    r = _pedir(cliente, metodo, ruta, {"Authorization": "Bearer token-sec23", "X-Tenant-ID": AJENA})
    assert r.status_code == 403, r.text


def test_miembro_de_la_organizacion_consulta_el_estado(cliente, monkeypatch):
    _con_usuario_verificado(monkeypatch)
    r = cliente.get("/api/v1/ai_copilot/estado",
                    headers={"Authorization": "Bearer token-sec23", "X-Tenant-ID": PROPIA})
    assert r.status_code == 200, r.text
    assert "corpus_version" in r.json()
