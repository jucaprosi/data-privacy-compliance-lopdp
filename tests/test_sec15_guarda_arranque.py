# ¤rbac-tenant ¤arbitro
"""SEC-15 / RET-01 · Guarda de arranque: AUTH_MODE=headers solo arranca fuera de Cloud Run y contra base local.

Contrato: `INV_LOPDP_HEADERS_NEVER_WITH_PRODUCTION`. Predicado:
    AUTH_MODE = headers ∧ (∃ v ∈ {DATABASE_URL, MIGRATION_DATABASE_URL, DATABASE_URL_DIRECT} :
    ¬es_base_local(v)  ∨  corre_en_la_nube())  ⟹  no arranca.

Con `AUTH_MODE=oidc`, la guardia de base local no rige (Cloud Run con `/cloudsql/...` arranca normal).
Solo URL ficticias (RFC 2606 `.invalid` o sockets `/cloudsql/` simulados): ninguna credencial real.
"""
import logging
import os
import subprocess
import sys
from pathlib import Path

import pytest

from app_core import huellas_produccion as huellas
from app_core.huellas_produccion import (
    INSTANCIA_CLOUD_SQL_PRODUCCION, VARIABLES_DE_NUBE, apunta_a_produccion, corre_en_la_nube,
    es_base_local, host_de,
)
from app_core.security import REGLA_ARRANQUE, VARIABLES_DE_BASE, exigir_arranque_seguro

RAIZ = Path(__file__).resolve().parent.parent
URL_REMOTA = "postgresql+psycopg://usuario:clave-ficticia@db.remota.invalid/lopdp"
URL_CLOUDSQL_PROD = f"postgresql+psycopg://lopdp_app:clave-ficticia@/evydentia?host=/cloudsql/{INSTANCIA_CLOUD_SQL_PRODUCCION}"
URL_CLOUDSQL_PRUEBAS = "postgresql+psycopg://lopdp_app:clave-ficticia@/lopdp?host=/cloudsql/evydentia-pruebas:us-central1:evydentia-pruebas"
URL_LOCAL = "postgresql+psycopg://usuario:clave-ficticia@127.0.0.1:5432/lopdp"


@pytest.fixture
def entorno(monkeypatch):
    """Entorno limpio: cabeceras, fuera de Cloud Run y las tres bases en 127.0.0.1 local."""
    for nombre in (*VARIABLES_DE_NUBE, "CLOUD_SQL_INSTANCE", "INSTANCE_CONNECTION_NAME", "CLOUD_SQL_CONNECTION_NAME"):
        monkeypatch.delenv(nombre, raising=False)
    for nombre in VARIABLES_DE_BASE:
        monkeypatch.setenv(nombre, URL_LOCAL)
    monkeypatch.setenv("AUTH_MODE", "headers")
    return monkeypatch


# ----------------------------------------------------------------------------- guarda

def test_las_tres_variables_de_base_estan_vigiladas():
    assert VARIABLES_DE_BASE == ("DATABASE_URL", "MIGRATION_DATABASE_URL", "DATABASE_URL_DIRECT")


@pytest.mark.parametrize("variable", ["DATABASE_URL", "MIGRATION_DATABASE_URL", "DATABASE_URL_DIRECT"])
@pytest.mark.parametrize("url_no_local", [URL_REMOTA, URL_CLOUDSQL_PROD, URL_CLOUDSQL_PRUEBAS])
def test_cabeceras_con_base_no_local_no_arranca(entorno, variable, url_no_local):
    entorno.setenv(variable, url_no_local)
    with pytest.raises(RuntimeError) as error:
        exigir_arranque_seguro()
    mensaje = str(error.value)
    assert REGLA_ARRANQUE in mensaje and variable in mensaje
    assert url_no_local not in mensaje and "clave-ficticia" not in mensaje and "db.remota.invalid" not in mensaje


def test_cabeceras_en_la_nube_no_arranca(entorno):
    entorno.setenv("K_SERVICE", "evydentia-backend")
    with pytest.raises(RuntimeError) as error:
        exigir_arranque_seguro()
    assert REGLA_ARRANQUE in str(error.value) and "K_SERVICE" in str(error.value)


def test_cabeceras_con_host_local_arranca_y_dice_el_host(entorno, caplog):
    with caplog.at_level(logging.WARNING, logger="jubys.arranque"):
        exigir_arranque_seguro()
    linea = caplog.text
    assert "AUTH_MODE=headers" in linea and "127.0.0.1" in linea
    assert "clave-ficticia" not in linea and "usuario" not in linea


@pytest.mark.parametrize("host_local", ["localhost", "127.0.0.1", "[::1]"])
def test_cabeceras_acepta_hosts_locales_permitidos(entorno, host_local):
    url = f"postgresql+psycopg://usuario:clave-ficticia@{host_local}:5432/lopdp"
    for nombre in VARIABLES_DE_BASE:
        entorno.setenv(nombre, url)
    exigir_arranque_seguro()


@pytest.mark.parametrize("modo", ["oidc", "", "HEADERS-no"])
def test_oidc_con_cloudsql_de_produccion_y_en_cloud_run_arranca(entorno, modo):
    """El arranque legítimo de Cloud Run usa oidc + K_SERVICE + /cloudsql/... sin activar la guardia local."""
    entorno.setenv("AUTH_MODE", modo)
    for nombre in VARIABLES_DE_BASE:
        entorno.setenv(nombre, URL_CLOUDSQL_PROD)
    entorno.setenv("K_SERVICE", "evydentia-backend")
    exigir_arranque_seguro()


# ----------------------------------------------------------------------------- main.py

def _importar_main(**variables) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in (*VARIABLES_DE_NUBE, "CLOUD_SQL_INSTANCE")}
    env.update({nombre: URL_LOCAL for nombre in VARIABLES_DE_BASE}, AUTH_MODE="headers", PYTHONIOENCODING="utf-8")
    env.update(variables)
    return subprocess.run([sys.executable, "-c", "import main"], cwd=RAIZ, env=env,
                          capture_output=True, text=True, encoding="utf-8", timeout=180)


@pytest.mark.parametrize("url_no_local", [URL_REMOTA, URL_CLOUDSQL_PROD, URL_CLOUDSQL_PRUEBAS])
def test_importar_main_con_base_no_local_sale_con_error(url_no_local):
    resultado = _importar_main(DATABASE_URL=url_no_local)
    assert resultado.returncode != 0
    assert REGLA_ARRANQUE in resultado.stderr and "DATABASE_URL" in resultado.stderr
    assert "clave-ficticia" not in resultado.stderr + resultado.stdout


def test_importar_main_con_base_local_arranca():
    """Control: el fallo anterior se debe a la guarda, no a otra cosa del entorno."""
    resultado = _importar_main()
    assert resultado.returncode == 0, resultado.stderr[-2000:]


def test_la_guarda_corre_en_main_antes_de_crear_la_aplicacion():
    texto = (RAIZ / "main.py").read_text(encoding="utf-8")
    seccion = texto.split("# === SEC-15 ===")[1].split("# === fin SEC-15 ===")[0]
    assert "exigir_arranque_seguro()" in seccion
    assert texto.index("from app_core.config import config") < texto.index("# === SEC-15 ===") < texto.index("app = FastAPI(")


# ----------------------------------------------------------------------------- huella y nube

@pytest.mark.parametrize(("url", "esperado"), [
    (URL_CLOUDSQL_PROD, True),
    (URL_CLOUDSQL_PRUEBAS, False),
    (URL_LOCAL, False),
    ("sqlite+aiosqlite:////tmp/test.db", False),
    ("", False),
    (None, False),
])
def test_apunta_a_produccion_solo_reconoce_cloudsql_produccion(url, esperado):
    assert apunta_a_produccion(url, {}) is esperado


@pytest.mark.parametrize(("url", "esperado"), [
    (URL_LOCAL, True),
    ("postgresql://usuario:clave@localhost:5432/lopdp", True),
    ("postgresql+asyncpg://usuario:clave@[::1]:5432/lopdp", True),
    (URL_REMOTA, False),
    (URL_CLOUDSQL_PROD, False),
    (URL_CLOUDSQL_PRUEBAS, False),
    ("postgresql://localhost/lopdp?host=/cloudsql/instancia", False),
    ("sqlite+aiosqlite:////tmp/test.db", False),
    ("", False),
    (None, False),
])
def test_es_base_local_aplica_lista_blanca(url, esperado):
    assert es_base_local(url, {}) is esperado


def test_host_de_no_devuelve_credenciales():
    assert host_de(URL_REMOTA) == "db.remota.invalid"
    assert host_de("sqlite+aiosqlite:////tmp/test.db") is None


@pytest.mark.parametrize(("variables", "esperado"), [
    ({}, False),
    ({"K_SERVICE": "lopdp-backend"}, True),
    ({"K_SERVICE": ""}, True),
    ({"CI": "true", "GITHUB_ACTIONS": "true"}, False),
])
def test_corre_en_la_nube(variables, esperado):
    assert corre_en_la_nube(variables) is esperado


def test_corre_en_la_nube_lee_el_entorno_del_proceso(monkeypatch):
    monkeypatch.delenv("K_SERVICE", raising=False)
    assert corre_en_la_nube() is False
    monkeypatch.setenv("K_SERVICE", "lopdp-backend")
    assert corre_en_la_nube() is True


def test_crear_organizacion_dev_usa_la_guardia_del_modulo():
    sys.path.insert(0, str(RAIZ / "scripts"))
    try:
        import crear_organizacion_dev as script
    finally:
        sys.path.remove(str(RAIZ / "scripts"))
    assert script.es_base_local is huellas.es_base_local
    assert script.apunta_a_produccion is huellas.apunta_a_produccion
    with pytest.raises(RuntimeError):
        script.validar_entorno(URL_REMOTA, auth_mode="headers")
    with pytest.raises(RuntimeError):
        script.validar_entorno(URL_CLOUDSQL_PRUEBAS, auth_mode="headers")
    assert script.validar_entorno(URL_LOCAL, auth_mode="headers") == "127.0.0.1"
