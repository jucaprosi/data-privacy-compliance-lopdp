# ¤entorno-pruebas ¤seguridad ¤arbitro
"""EP-01 · Identidad del entorno y guardias de arranque (PRD EVYDENTIA §5.5 y §5.6.2).

Solo valores ficticios: proyectos `proyecto-*-ficticio` y hosts `.invalid` (RFC 2606).
El servidor de metadatos se sustituye por un doble; nada sale a la red.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app_core.entorno import guardias
from app_core.entorno.guardias import (
    ErrorArranqueEntorno, datos_ficticios, entorno_actual, validar_arranque,
)

RAIZ = Path(__file__).resolve().parent.parent
HUELLA = "proyecto-produccion-ficticio"
URL_CON_HUELLA = f"postgresql+psycopg://usuario:clave-ficticia@db.{HUELLA}.ejemplo.invalid/lopdp"
URL_AJENA = "postgresql+psycopg://usuario:clave-ficticia@db.proyecto-pruebas-ficticio.ejemplo.invalid/lopdp"
SIN_METADATOS = lambda: None  # noqa: E731


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("HUELLA_PROYECTO_PRODUCCION", HUELLA)
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "proyecto-pruebas-ficticio")
    monkeypatch.setenv("DATABASE_URL", URL_AJENA)
    monkeypatch.setenv("AUTH_MODE", "oidc")
    return monkeypatch


@pytest.mark.parametrize("valor", ["development", "test", "pruebas", "demo", "production"])
def test_valores_validos(monkeypatch, valor):
    monkeypatch.setenv("APP_ENV", valor)
    assert entorno_actual() == valor


def test_valor_desconocido_es_error(monkeypatch):
    monkeypatch.setenv("APP_ENV", "staging")
    with pytest.raises(ErrorArranqueEntorno):
        entorno_actual()


@pytest.mark.parametrize("entorno", ["pruebas", "demo"])
def test_arranque_correcto_con_proyecto_ajeno(env, entorno):
    env.setenv("APP_ENV", entorno)
    assert validar_arranque(SIN_METADATOS) == entorno
    assert datos_ficticios() is True


@pytest.mark.parametrize("entorno", ["pruebas", "demo"])
def test_falta_huella(env, entorno):
    env.setenv("APP_ENV", entorno)
    env.delenv("HUELLA_PROYECTO_PRODUCCION")
    with pytest.raises(ErrorArranqueEntorno, match="HUELLA_PROYECTO_PRODUCCION"):
        validar_arranque(SIN_METADATOS)


@pytest.mark.parametrize("entorno", ["pruebas", "demo"])
def test_proyecto_coincide_por_variable(env, entorno):
    env.setenv("APP_ENV", entorno)
    env.setenv("GOOGLE_CLOUD_PROJECT", HUELLA)
    with pytest.raises(ErrorArranqueEntorno, match="proyecto de Google Cloud"):
        validar_arranque(SIN_METADATOS)


@pytest.mark.parametrize("entorno", ["pruebas", "demo"])
def test_proyecto_coincide_por_metadatos(env, entorno):
    env.setenv("APP_ENV", entorno)
    env.delenv("GOOGLE_CLOUD_PROJECT")
    with pytest.raises(ErrorArranqueEntorno, match="proyecto de Google Cloud"):
        validar_arranque(lambda: HUELLA)


def test_sin_nube_ni_variable_el_proyecto_es_desconocido(env):
    env.setenv("APP_ENV", "pruebas")
    env.delenv("GOOGLE_CLOUD_PROJECT")
    assert validar_arranque(SIN_METADATOS) == "pruebas"


@pytest.mark.parametrize("entorno", ["pruebas", "demo"])
def test_huella_en_database_url_sin_filtrar_la_url(env, entorno):
    env.setenv("APP_ENV", entorno)
    env.setenv("DATABASE_URL", URL_CON_HUELLA)
    with pytest.raises(ErrorArranqueEntorno, match="DATABASE_URL") as error:
        validar_arranque(SIN_METADATOS)
    mensaje = str(error.value)
    assert URL_CON_HUELLA not in mensaje and "clave-ficticia" not in mensaje and ".invalid" not in mensaje


@pytest.mark.parametrize("entorno", ["pruebas", "demo"])
def test_auth_mode_headers_rechazado(env, entorno):
    env.setenv("APP_ENV", entorno)
    env.setenv("AUTH_MODE", "headers")
    with pytest.raises(ErrorArranqueEntorno, match="AUTH_MODE"):
        validar_arranque(SIN_METADATOS)


@pytest.mark.parametrize("entorno", ["development", "test", "production"])
def test_fuera_de_pruebas_y_demo_no_cambia_el_arranque(monkeypatch, entorno):
    monkeypatch.setenv("APP_ENV", entorno)
    monkeypatch.delenv("HUELLA_PROYECTO_PRODUCCION", raising=False)
    monkeypatch.setenv("DATABASE_URL", URL_CON_HUELLA)
    llamadas = []
    assert validar_arranque(lambda: llamadas.append(1)) == entorno
    assert llamadas == [] and datos_ficticios() is False


@pytest.mark.parametrize("entorno,ficticios", [
    ("development", False), ("test", False), ("pruebas", True), ("demo", True), ("production", False),
])
def test_cuerpo_de_entorno(monkeypatch, entorno, ficticios):
    import main
    monkeypatch.setenv("APP_ENV", entorno)
    monkeypatch.setattr(main, "ENTORNO", entorno)
    respuesta = TestClient(main.app).get("/api/v1/entorno")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"entorno": entorno, "datos_ficticios": ficticios}


@pytest.mark.parametrize("entorno", ["development", "test", "pruebas", "demo"])
def test_cabecera_presente_fuera_de_produccion(monkeypatch, entorno):
    import main
    monkeypatch.setattr(main, "ENTORNO", entorno)
    assert TestClient(main.app).get("/health").headers.get("X-Entorno") == entorno


def test_cabecera_ausente_en_produccion_y_cuerpo_igual(monkeypatch):
    import main
    cliente = TestClient(main.app)
    monkeypatch.setattr(main, "ENTORNO", "development")
    antes = cliente.get("/health")
    monkeypatch.setattr(main, "ENTORNO", "production")
    despues = cliente.get("/health")
    assert "X-Entorno" not in despues.headers
    assert antes.status_code == despues.status_code and antes.json() == despues.json()


def test_metadatos_fuera_de_la_nube_devuelve_none(monkeypatch):
    def sin_red(*_a, **_k):
        raise OSError("sin red")
    monkeypatch.setattr(guardias.urllib.request, "urlopen", sin_red)
    assert guardias._proyecto_desde_metadatos() is None


def test_main_no_arranca_en_pruebas_sin_huella():
    entorno = {k: v for k, v in os.environ.items() if k not in ("HUELLA_PROYECTO_PRODUCCION", "VERCEL", "K_SERVICE")}
    entorno.update(APP_ENV="pruebas", AUTH_MODE="oidc", GOOGLE_CLOUD_PROJECT="proyecto-pruebas-ficticio",
                   DATABASE_URL=URL_AJENA)
    resultado = subprocess.run([sys.executable, "-c", "import main"], cwd=RAIZ, env=entorno,
                               capture_output=True, text=True, timeout=120)
    assert resultado.returncode != 0
    assert "HUELLA_PROYECTO_PRODUCCION" in resultado.stderr
    assert "clave-ficticia" not in resultado.stderr


# --- EP-11: la demo local nunca apunta a producción ----------------------------------------------
# Mutación documentada: quitar la llamada a apunta_a_produccion en validar_arranque hace fallar las
# pruebas 1 y 2, porque la URL simulada lleva el host de producción pero no la huella del proyecto.

from app_core.huellas_produccion import HUELLA_HOST_PRODUCCION  # noqa: E402

URL_PRODUCCION_SIMULADA = (
    f"postgresql+psycopg://usuario:clave-ficticia@{HUELLA_HOST_PRODUCCION}.ejemplo.invalid/lopdp"
)


@pytest.mark.parametrize("entorno", ["demo", "pruebas"])
def test_ep11_no_arranca_con_url_simulada_de_produccion(env, entorno, recwarn):
    env.setenv("APP_ENV", entorno)
    env.setenv("DATABASE_URL", URL_PRODUCCION_SIMULADA)
    with pytest.raises(ErrorArranqueEntorno, match="producción") as error:
        validar_arranque(SIN_METADATOS)
    assert URL_PRODUCCION_SIMULADA not in str(error.value)
    assert not recwarn.list


def test_ep11_demo_con_url_simulada_de_prueba_arranca(env):
    env.setenv("APP_ENV", "demo")
    env.setenv("DATABASE_URL", URL_AJENA)
    assert validar_arranque(SIN_METADATOS) == "demo"
