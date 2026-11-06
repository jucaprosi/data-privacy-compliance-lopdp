# ¤rbac-tenant ¤arbitro
"""SEC-15 · Guarda de arranque: el modo de cabeceras nunca arranca contra producción ni en la nube.

Contrato: `INV_LOPDP_HEADERS_NEVER_WITH_PRODUCTION`. Predicado:
    AUTH_MODE = headers ∧ (∃ v ∈ {DATABASE_URL, MIGRATION_DATABASE_URL, DATABASE_URL_DIRECT} :
    host(v) ∋ huella  ∨  VERCEL ∨ K_SERVICE)  ⟹  no arranca.

Solo URL ficticias con la huella del host (dominio `.invalid`, RFC 2606): ninguna credencial real.
Nada se conecta a una base.

Mutación documentada: quitar "MIGRATION_DATABASE_URL" de `VARIABLES_DE_BASE` en
`app_core/security.py` hace fallar `test_cabeceras_con_produccion_no_arranca[MIGRATION_DATABASE_URL]`.
"""
import logging
import os
import subprocess
import sys
from pathlib import Path

import pytest

from app_core import huellas_produccion as huellas
from app_core.huellas_produccion import (
    HUELLA_HOST_PRODUCCION, apunta_a_produccion, corre_en_la_nube, host_de,
)
from app_core.security import REGLA_ARRANQUE, VARIABLES_DE_BASE, exigir_arranque_seguro

RAIZ = Path(__file__).resolve().parent.parent
URL_PRODUCCION = f"postgresql+psycopg://usuario:clave-ficticia@{HUELLA_HOST_PRODUCCION}-pooler.c-0.ejemplo.invalid/lopdp"
URL_PRUEBAS = "postgresql+psycopg://usuario:clave-ficticia@ep-rama-de-pruebas-pooler.c-0.ejemplo.invalid/lopdp"


@pytest.fixture
def entorno(monkeypatch):
    """Entorno limpio: cabeceras, sin nube y las tres bases en el host de pruebas."""
    for nombre in ("VERCEL", "K_SERVICE"):
        monkeypatch.delenv(nombre, raising=False)
    for nombre in VARIABLES_DE_BASE:
        monkeypatch.setenv(nombre, URL_PRUEBAS)
    monkeypatch.setenv("AUTH_MODE", "headers")
    return monkeypatch


# ----------------------------------------------------------------------------- guarda

def test_las_tres_variables_de_base_estan_vigiladas():
    assert VARIABLES_DE_BASE == ("DATABASE_URL", "MIGRATION_DATABASE_URL", "DATABASE_URL_DIRECT")


@pytest.mark.parametrize("variable", ["DATABASE_URL", "MIGRATION_DATABASE_URL", "DATABASE_URL_DIRECT"])
def test_cabeceras_con_produccion_no_arranca(entorno, variable):
    entorno.setenv(variable, URL_PRODUCCION)
    with pytest.raises(RuntimeError) as error:
        exigir_arranque_seguro()
    mensaje = str(error.value)
    assert REGLA_ARRANQUE in mensaje and variable in mensaje
    assert URL_PRODUCCION not in mensaje and "clave-ficticia" not in mensaje and HUELLA_HOST_PRODUCCION not in mensaje


@pytest.mark.parametrize("variable", ["VERCEL", "K_SERVICE"])
def test_cabeceras_en_la_nube_no_arranca(entorno, variable):
    entorno.setenv(variable, "1")
    with pytest.raises(RuntimeError) as error:
        exigir_arranque_seguro()
    assert REGLA_ARRANQUE in str(error.value) and variable in str(error.value)


def test_cabeceras_con_host_de_pruebas_arranca_y_dice_el_host(entorno, caplog):
    with caplog.at_level(logging.WARNING, logger="jubys.arranque"):
        exigir_arranque_seguro()
    linea = caplog.text
    assert "AUTH_MODE=headers" in linea and "ep-rama-de-pruebas-pooler.c-0.ejemplo.invalid" in linea
    assert "clave-ficticia" not in linea and "usuario" not in linea


@pytest.mark.parametrize("modo", ["oidc", "", "HEADERS-no"])
def test_oidc_con_produccion_y_en_la_nube_arranca(entorno, modo):
    """Es el caso legítimo de Vercel: oidc con la base de producción."""
    entorno.setenv("AUTH_MODE", modo)
    for nombre in VARIABLES_DE_BASE:
        entorno.setenv(nombre, URL_PRODUCCION)
    entorno.setenv("VERCEL", "1")
    exigir_arranque_seguro()


# ----------------------------------------------------------------------------- main.py

def _importar_main(**variables) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in ("VERCEL", "K_SERVICE")}
    env.update({nombre: URL_PRUEBAS for nombre in VARIABLES_DE_BASE}, AUTH_MODE="headers", PYTHONIOENCODING="utf-8")
    env.update(variables)
    return subprocess.run([sys.executable, "-c", "import main"], cwd=RAIZ, env=env,
                          capture_output=True, text=True, encoding="utf-8", timeout=180)


def test_importar_main_con_produccion_sale_con_error():
    resultado = _importar_main(DATABASE_URL=URL_PRODUCCION)
    assert resultado.returncode != 0
    assert REGLA_ARRANQUE in resultado.stderr and "DATABASE_URL" in resultado.stderr
    assert "clave-ficticia" not in resultado.stderr + resultado.stdout


def test_importar_main_con_base_de_pruebas_arranca():
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
    (URL_PRODUCCION, True),
    (f"postgresql://u:p@{HUELLA_HOST_PRODUCCION}.c-0.ejemplo.invalid:5432/lopdp", True),
    (f"postgresql://U:P@{HUELLA_HOST_PRODUCCION.upper()}.EJEMPLO.INVALID/lopdp", True),
    (URL_PRUEBAS, False),
    # Solo el host cuenta: la huella en la contraseña o en el nombre de la base no es producción.
    (f"postgresql://u:{HUELLA_HOST_PRODUCCION}@ep-rama-de-pruebas.ejemplo.invalid/{HUELLA_HOST_PRODUCCION}", False),
    # Falla cerrado: sin host legible, la huella en el texto cuenta como producción.
    (f"{HUELLA_HOST_PRODUCCION}/lopdp", True),
    ("sqlite+aiosqlite:////tmp/test.db", False),
    ("", False),
    (None, False),
])
def test_apunta_a_produccion_compara_el_host(url, esperado):
    assert apunta_a_produccion(url) is esperado


def test_host_de_no_devuelve_credenciales():
    assert host_de(URL_PRUEBAS) == "ep-rama-de-pruebas-pooler.c-0.ejemplo.invalid"
    assert host_de("sqlite+aiosqlite:////tmp/test.db") is None


@pytest.mark.parametrize(("variables", "esperado"), [
    ({}, False),
    ({"VERCEL": "1"}, True),
    ({"VERCEL": ""}, True),
    ({"K_SERVICE": "lopdp-backend"}, True),
    ({"VERCEL_ENV": "preview", "CI": "true", "GITHUB_ACTIONS": "true"}, False),
])
def test_corre_en_la_nube(variables, esperado):
    assert corre_en_la_nube(variables) is esperado


def test_corre_en_la_nube_lee_el_entorno_del_proceso(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("K_SERVICE", raising=False)
    assert corre_en_la_nube() is False
    monkeypatch.setenv("K_SERVICE", "lopdp-backend")
    assert corre_en_la_nube() is True


def test_la_huella_vive_en_un_solo_modulo():
    """Ninguno de los archivos de SEC-15 escribe la huella salvo `app_core/huellas_produccion.py`."""
    for relativa in ("app_core/security.py", "main.py", "scripts/crear_organizacion_dev.py"):
        assert HUELLA_HOST_PRODUCCION not in (RAIZ / relativa).read_text(encoding="utf-8"), relativa


def test_crear_organizacion_dev_usa_la_huella_del_modulo():
    sys.path.insert(0, str(RAIZ / "scripts"))
    try:
        import crear_organizacion_dev as script
    finally:
        sys.path.remove(str(RAIZ / "scripts"))
    assert script.HOST_PRODUCCION is huellas.HUELLA_HOST_PRODUCCION
    assert script.apunta_a_produccion is huellas.apunta_a_produccion
    with pytest.raises(RuntimeError):
        script.validar_entorno(URL_PRODUCCION, auth_mode="headers")
    assert script.validar_entorno(URL_PRUEBAS, auth_mode="headers") == "ep-rama-de-pruebas-pooler.c-0.ejemplo.invalid"
