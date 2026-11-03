# ¤ci-cd
# ¤¤qa-engineer
"""El conteo de consultas por prueba, con SQLite en memoria: sin red y sin Neon."""
import importlib.util
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

import plugin_contar_consultas as plugin

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("contar_consultas_pruebas", RAIZ / "scripts" / "contar_consultas_pruebas.py")
ccp = importlib.util.module_from_spec(_spec)
sys.modules["contar_consultas_pruebas"] = ccp
_spec.loader.exec_module(ccp)

SECRETO = "dato-personal-que-no-debe-guardarse"


@pytest.fixture
def contador():
    instancia = plugin.Contador()
    instancia.instalar()
    yield instancia
    instancia.retirar()


def _consultar(veces: int) -> None:
    motor = create_engine("sqlite://")
    with motor.connect() as conexion:
        for _ in range(veces):
            conexion.execute(text("SELECT :valor"), {"valor": SECRETO})
    motor.dispose()


def _fila(contador, nodeid):
    return next(fila for fila in contador.filas() if fila["nodeid"] == nodeid)


def test_cuenta_sentencias_conexion_y_checkout(contador):
    contador.actual = ("a", "call")
    _consultar(3)
    fila = _fila(contador, "a")
    assert (fila["consultas"], fila["conexiones"], fila["checkouts"]) == (3, 1, 1)
    assert fila["rollback"] == 1  # salir del bloque sin commit


def test_dos_pruebas_no_se_mezclan(contador):
    contador.actual = ("a", "call")
    _consultar(2)
    contador.actual = ("b", "call")
    _consultar(5)
    assert (_fila(contador, "a")["consultas"], _fila(contador, "b")["consultas"]) == (2, 5)


def test_separa_las_consultas_de_fixtures(contador):
    contador.actual = ("a", "setup")
    _consultar(2)
    contador.actual = ("a", "call")
    _consultar(1)
    contador.actual = ("a", "teardown")
    _consultar(4)
    fila = _fila(contador, "a")
    assert (fila["consultas"], fila["consultas_en_fixtures"]) == (7, 6)


def test_lo_que_ocurre_fuera_de_una_prueba_no_se_atribuye(contador):
    contador.actual = None
    _consultar(2)
    assert contador.filas() == []


def test_retirar_deja_de_contar():
    instancia = plugin.Contador()
    instancia.instalar()
    instancia.retirar()
    instancia.actual = ("a", "call")
    _consultar(1)
    assert instancia.filas() == []


def test_el_plugin_real_escribe_un_json_sin_texto_de_sentencias(tmp_path):
    (tmp_path / "test_x.py").write_text(textwrap.dedent(f"""
        from sqlalchemy import create_engine, text

        def _consultar(veces):
            with create_engine("sqlite://").connect() as conexion:
                for _ in range(veces):
                    conexion.execute(text("SELECT :valor"), {{"valor": "{SECRETO}"}})

        def test_dos():
            _consultar(2)

        def test_ninguna():
            pass

        def test_tres():
            _consultar(3)
    """), encoding="utf-8")
    salida = tmp_path / "salida.json"
    fuera = ("PYTEST_ADDOPTS", "PYTEST_XDIST_WORKER", "TEST_DATABASE_URL", "DATABASE_URL")
    entorno = {clave: valor for clave, valor in os.environ.items() if clave not in fuera}
    entorno["PYTHONPATH"] = str(RAIZ / "tests")
    proceso = subprocess.run(
        [sys.executable, "-m", "pytest", "test_x.py", "-p", "plugin_contar_consultas", "--consultas-json", str(salida),
         "-p", "no:cacheprovider", "--rootdir", str(tmp_path), "-c", os.devnull],
        cwd=tmp_path, env=entorno, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )
    assert proceso.returncode == 0, proceso.stdout + proceso.stderr
    crudo = salida.read_text(encoding="utf-8")
    assert SECRETO not in crudo and "SELECT" not in crudo
    assert {fila["nodeid"]: fila["consultas"] for fila in json.loads(crudo)} == {
        "test_x.py::test_dos": 2, "test_x.py::test_ninguna": 0, "test_x.py::test_tres": 3,
    }


def test_los_archivos_salen_de_la_medicion():
    texto = "| Archivo | Pruebas |\n| :--- | ---: |\n| `test_a` | 20 |\n| `test_b_c` | 33 |\n\nvan `test_d` aparte\n"
    assert ccp.archivos_de_la_medicion(texto) == ["tests/test_a.py", "tests/test_b_c.py"]


def test_la_tabla_agrega_por_archivo():
    def fila(nodeid, consultas, fixtures):
        ceros = dict.fromkeys(("conexiones", "checkouts", "begin", "commit", "rollback"), 1)
        return {"nodeid": nodeid, "segundos": 1.0, "consultas": consultas, "consultas_en_fixtures": fixtures, **ceros}

    a, = ccp.por_archivo([fila("tests/a.py::x", 10, 5), fila("tests/a.py::y", 20, 15), fila("tests/a.py::z", 60, 25)])
    assert (a["archivo"], a["pruebas"], a["consultas"], a["mediana"], a["maximo"]) == ("tests/a.py", 3, 90, 20, 60)
    assert a["pct_fixtures"] == 50
    assert a["viajes"] == 90 + 3 * 4  # sin contar el saludo de cada conexión, que se suma aparte
    assert a["conexiones"] == 3


def test_la_latencia_implicita_es_la_diferencia_entre_los_viajes():
    assert ccp.latencia_implicita_ms(segundos_lejos=30.0, segundos_cerca=10.0, viajes=1000) == 20.0
    assert ccp.latencia_implicita_ms(10.0, 10.0, 0) is None


@pytest.mark.parametrize("url", ["postgresql://u@ep-algo.us-east-2.aws.neon.tech/x", "postgresql://u@ep-late-hall-1/x"])
def test_el_script_rechaza_neon(url):
    with pytest.raises(SystemExit):
        ccp.exigir_base_local(url)


def test_el_script_acepta_la_base_local():
    ccp.exigir_base_local("postgresql://lopdp@127.0.0.1:55432/lopdp")
