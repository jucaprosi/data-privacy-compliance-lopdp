# ¤arbitro
# ¤¤qa-engineer
"""Cada trabajador de xdist clona su base de una plantilla migrada; sin -n la suite usa TEST_DATABASE_URL como siempre.

Estas pruebas no necesitan xdist ni servidor: el CI aún corre en serie y contra Neon, donde no se puede clonar.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import psycopg
import pytest
from sqlalchemy.engine import make_url

import conftest

RAIZ = Path(__file__).resolve().parent.parent
SECRETO = "clave-que-no-debe-salir"
URL = f"postgresql://dueno:{SECRETO}@127.0.0.1:55432/lopdp"
SIN_SERVIDOR = f"postgresql://dueno:{SECRETO}@servidor-inexistente.test:1/base"


class _Conexion:
    """Registra las sentencias en texto y falla las primeras CREATE DATABASE que se le indiquen."""

    def __init__(self, fallos: int = 0):
        self.sentencias, self.parametros, self.fallos = [], [], fallos

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, sentencia, parametros=None):
        texto = sentencia if isinstance(sentencia, str) else sentencia.as_string(None)
        self.sentencias.append(texto)
        self.parametros.append(parametros)
        if texto.startswith("CREATE DATABASE") and self.fallos:
            self.fallos -= 1
            raise psycopg.errors.ObjectInUse("la plantilla tiene sesiones abiertas")


def _trabajador(trabajador="gw3", corrida="abcdef0123456789"):
    return SimpleNamespace(workerinput={"workerid": trabajador, "testrunuid": corrida})


@pytest.fixture
def entorno_de_trabajador(monkeypatch):
    conexion = _Conexion()
    monkeypatch.setattr(conftest.psycopg, "connect", lambda *a, **k: conexion)
    for nombre in conftest.VARIABLES_DE_BASE:
        monkeypatch.setenv(nombre, URL)
    monkeypatch.setenv("PYTEST_ADDOPTS", "-n auto")
    return conexion


def test_los_trabajadores_ordenan_igual_los_parametros_y_conservan_la_definicion():
    def lista(*ids):
        return [SimpleNamespace(nodeid=i) for i in ids]

    uno = lista("a.py::zeta", "a.py::beta[y]", "a.py::beta[x]", "b.py::alfa")
    otro = lista("a.py::zeta", "a.py::beta[x]", "a.py::beta[y]", "b.py::alfa")
    conftest._ordenar_parametros(uno)
    conftest._ordenar_parametros(otro)
    assert [i.nodeid for i in uno] == [i.nodeid for i in otro]
    assert [i.nodeid for i in uno] == ["a.py::zeta", "a.py::beta[x]", "a.py::beta[y]", "b.py::alfa"]


def test_cada_archivo_empieza_solo_con_los_overrides_que_instalo(monkeypatch):
    uno, otro = object(), object()
    assert conftest._overrides_nuevos({"a": uno}, {"a": uno, "b": otro}) == {"b": otro}
    assert conftest._overrides_nuevos({"a": uno}, {"a": otro}) == {"a": otro}

    overrides = {"ajeno": uno}
    monkeypatch.setitem(sys.modules, "main", SimpleNamespace(app=SimpleNamespace(dependency_overrides=overrides)))
    monkeypatch.setitem(conftest._OVERRIDES_POR_ARCHIVO, "tests/test_a.py", {"propio": otro})
    conftest._restablecer_overrides("tests/test_a.py")
    assert overrides == {"propio": otro}
    conftest._restablecer_overrides("tests/test_sin_overrides.py")
    assert overrides == {}


def test_el_nombre_del_clon_distingue_trabajador_y_corrida():
    uno = conftest._nombre_de_clon("lopdp", "gw0", "abcdef0123456789")
    assert uno == "lopdp_gw0_abcdef01"
    assert uno != conftest._nombre_de_clon("lopdp", "gw1", "abcdef0123456789")
    assert uno != conftest._nombre_de_clon("lopdp", "gw0", "00000000ffff")


def test_cierra_las_conexiones_a_la_plantilla_antes_de_clonar():
    conexion = _Conexion()
    conftest._clonar_plantilla(conexion, "lopdp", "lopdp_gw0_abc")
    assert "pg_terminate_backend" in conexion.sentencias[0]
    assert conexion.parametros[0] == ("lopdp",)
    assert conexion.sentencias[1] == 'CREATE DATABASE "lopdp_gw0_abc" TEMPLATE "lopdp"'


def test_si_la_plantilla_sigue_ocupada_vuelve_a_cerrar_y_reintenta(monkeypatch):
    monkeypatch.setattr(conftest.time, "sleep", lambda _: None)
    conexion = _Conexion(fallos=2)
    conftest._clonar_plantilla(conexion, "lopdp", "clon")
    assert sum("pg_terminate_backend" in s for s in conexion.sentencias) == 3
    assert sum(s.startswith("CREATE DATABASE") for s in conexion.sentencias) == 3


def test_si_la_plantilla_nunca_se_libera_el_error_no_se_oculta(monkeypatch):
    monkeypatch.setattr(conftest.time, "sleep", lambda _: None)
    with pytest.raises(psycopg.errors.ObjectInUse):
        conftest._clonar_plantilla(_Conexion(fallos=conftest.INTENTOS_DE_CLONADO), "lopdp", "clon")


def test_el_trabajador_apunta_las_tres_variables_a_su_clon(entorno_de_trabajador):
    config = _trabajador()
    conftest._preparar_trabajador(config)
    for nombre in conftest.VARIABLES_DE_BASE:
        assert make_url(os.environ[nombre]).database == "lopdp_gw3_abcdef01"
        assert make_url(os.environ[nombre]).password == SECRETO
    assert config._base_de_trabajador[1] == "lopdp_gw3_abcdef01"


def test_una_url_de_migracion_distinta_no_se_redirige(entorno_de_trabajador, monkeypatch):
    monkeypatch.setenv("MIGRATION_DATABASE_URL", "postgresql://otra@127.0.0.1/otra")
    conftest._preparar_trabajador(_trabajador())
    assert os.environ["MIGRATION_DATABASE_URL"] == "postgresql://otra@127.0.0.1/otra"


def test_los_pytest_hijos_no_heredan_el_paralelo(entorno_de_trabajador):
    conftest._preparar_trabajador(_trabajador())
    assert "PYTEST_ADDOPTS" not in os.environ


def test_el_trabajador_sin_base_no_conecta(entorno_de_trabajador, monkeypatch):
    monkeypatch.delenv("TEST_DATABASE_URL")
    conftest._preparar_trabajador(_trabajador())
    assert entorno_de_trabajador.sentencias == []


def test_el_clon_se_borra_aunque_queden_conexiones(entorno_de_trabajador):
    conftest._borrar_base_de_trabajador(make_url(URL), "lopdp_gw3_abc")
    assert entorno_de_trabajador.sentencias == ['DROP DATABASE IF EXISTS "lopdp_gw3_abc" WITH (FORCE)']


@pytest.mark.parametrize("procesos, url, esperado", [
    (4, "postgresql://u@ep-pruebas.neon.tech/base", True),
    (4, URL, False),
    (None, "postgresql://u@ep-pruebas.neon.tech/base", False),
    (0, "postgresql://u@ep-pruebas.neon.tech/base", False),
])
def test_el_paralelo_no_se_admite_sobre_neon(monkeypatch, procesos, url, esperado):
    monkeypatch.setenv("TEST_DATABASE_URL", url)
    config = SimpleNamespace(getoption=lambda nombre, defecto=None: procesos)
    assert conftest._paralelo_sobre_neon(config) is esperado


def test_sin_trabajadores_la_suite_usa_la_url_tal_cual_y_no_conecta(tmp_path):
    (tmp_path / "tests").mkdir()
    shutil.copy(RAIZ / "tests" / "conftest.py", tmp_path / "tests" / "conftest.py")
    (tmp_path / "tests" / "test_uno.py").write_text(
        "import os\n"
        "def test_uno(pytestconfig):\n"
        f"    assert os.environ['TEST_DATABASE_URL'] == {SIN_SERVIDOR!r}\n"
        f"    assert os.environ['DATABASE_URL'] == {SIN_SERVIDOR!r}\n"
        "    assert not hasattr(pytestconfig, '_base_de_trabajador')\n",
        encoding="utf-8",
    )
    entorno = {k: v for k, v in os.environ.items() if "DATABASE_URL" not in k and k != "PYTEST_ADDOPTS"}
    entorno.update(UPSTASH_REDIS_URL="prueba", R2_ACCESS_KEY_ID="prueba", TEST_DATABASE_URL=SIN_SERVIDOR)
    res = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider"],
                         cwd=tmp_path, capture_output=True, text=True, env=entorno)
    assert res.returncode == 0, res.stdout + res.stderr
    assert SECRETO not in res.stdout + res.stderr


def test_cada_proceso_usa_la_base_que_le_corresponde():
    base = make_url(os.environ["TEST_DATABASE_URL"]).database if os.environ.get("TEST_DATABASE_URL") else ""
    trabajador = os.environ.get("PYTEST_XDIST_WORKER")
    assert (f"_{trabajador}_" in base) if trabajador else ("_gw" not in (base or ""))
