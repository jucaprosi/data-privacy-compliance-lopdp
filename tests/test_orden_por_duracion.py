# ¤arbitro
# ¤¤qa-engineer
"""El orden por duración: de más lenta a más rápida, solo si hay archivo, y que xdist de verdad lo respete."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import conftest
import orden_por_duracion as orden

RAIZ = Path(__file__).resolve().parent.parent


def _items(*nodeids: str) -> list:
    return [SimpleNamespace(nodeid=nodeid) for nodeid in nodeids]


def _nodeids(items: list) -> list[str]:
    return [item.nodeid for item in items]


def test_el_archivo_mas_lento_va_primero_y_conserva_su_orden_interno():
    items = _items("tests/a.py::uno", "tests/a.py::dos", "tests/b.py::uno", "tests/c.py::uno")
    orden.ordenar(items, {"tests/a.py": 1.0, "tests/b.py": 9.0, "tests/c.py": 5.0})
    assert _nodeids(items) == ["tests/b.py::uno", "tests/c.py::uno", "tests/a.py::uno", "tests/a.py::dos"]


def test_un_archivo_sin_duracion_va_al_final_en_su_orden():
    items = _items("tests/nuevo_1.py::x", "tests/a.py::x", "tests/nuevo_2.py::x")
    orden.ordenar(items, {"tests/a.py": 1.0})
    assert _nodeids(items) == ["tests/a.py::x", "tests/nuevo_1.py::x", "tests/nuevo_2.py::x"]


def test_sin_archivo_de_duraciones_se_conserva_el_orden_de_pytest(tmp_path):
    items = _items("tests/b.py::x", "tests/a.py::x")
    orden.ordenar(items, orden.cargar(tmp_path / "no_existe.json"))
    assert _nodeids(items) == ["tests/b.py::x", "tests/a.py::x"]


def test_dos_trabajadores_obtienen_la_misma_lista():
    nodeids = ("tests/a.py::x[1]", "tests/a.py::x[2]", "tests/b.py::y", "tests/c.py::z")
    uno, otro = _items(*nodeids), _items(*nodeids)
    duraciones = {"tests/c.py": 3.0, "tests/a.py": 3.0}
    orden.ordenar(uno, duraciones)
    orden.ordenar(otro, dict(reversed(list(duraciones.items()))))
    assert _nodeids(uno) == _nodeids(otro)


def test_las_duraciones_suman_las_tres_fases_de_cada_archivo():
    salida = """
============ slowest durations ============
2.50s call     tests/test_a.py::uno
1.25s setup    tests/test_a.py::uno
0.25s teardown tests/test_a.py::dos[x y]
9.00s call     tests/test_b.py::uno
tests/test_c.py::uno PASSED
"""
    assert orden.duraciones_de_la_salida(salida) == {"tests/test_b.py": 9.0, "tests/test_a.py": 4.0}


def test_una_salida_sin_tabla_no_sobrescribe_las_duraciones(tmp_path, monkeypatch):
    destino, salida = tmp_path / "duraciones.json", tmp_path / "salida.txt"
    destino.write_text('{"tests/a.py": 1.0}', encoding="utf-8")
    salida.write_text("1 passed", encoding="utf-8")
    monkeypatch.setattr(orden, "ARCHIVO_DE_DURACIONES", destino)
    assert orden.main([str(salida)]) == 1
    assert destino.read_text(encoding="utf-8") == '{"tests/a.py": 1.0}'


@pytest.mark.parametrize(("hay_archivo", "reordena_xdist"), [(True, False), (False, True)])
def test_xdist_solo_deja_de_reordenar_si_hay_duraciones(tmp_path, monkeypatch, hay_archivo, reordena_xdist):
    ruta = tmp_path / "duraciones.json"
    if hay_archivo:
        ruta.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(conftest, "_DURACIONES", ruta)
    config = SimpleNamespace(option=SimpleNamespace(loadscopereorder=True))
    conftest._respetar_orden_por_duracion(config)
    assert config.option.loadscopereorder is reordena_xdist


def test_loadfile_ejecuta_en_el_orden_del_archivo_y_no_por_numero_de_pruebas(tmp_path):
    """Por omisión xdist reordena los archivos por número de pruebas y anularía el gancho sin avisar."""
    pytest.importorskip("xdist")
    pruebas = tmp_path / "tests"
    pruebas.mkdir()
    for nombre in ("conftest.py", "orden_por_duracion.py"):
        shutil.copy(RAIZ / "tests" / nombre, pruebas / nombre)
    for archivo, cuantas in (("test_a", 2), ("test_m", 3), ("test_z", 1)):
        cuerpo = "".join(f"def test_{i}():\n    pass\n" for i in range(cuantas))
        (pruebas / f"{archivo}.py").write_text(cuerpo, encoding="utf-8")
    duraciones = {"tests/test_z.py": 9.0, "tests/test_a.py": 5.0, "tests/test_m.py": 1.0}
    (pruebas / "duraciones.json").write_text(json.dumps(duraciones), encoding="utf-8")
    fuera = ("TEST_DATABASE_URL", "DATABASE_URL", "MIGRATION_DATABASE_URL", "PYTEST_ADDOPTS", "PYTEST_XDIST_WORKER")
    entorno = {clave: valor for clave, valor in os.environ.items() if clave not in fuera}
    entorno["PYTHONPATH"] = str(RAIZ)
    salida = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-n", "1", "--dist", "loadfile", "-v", "-p", "no:cacheprovider",
         "--rootdir", str(tmp_path), "-o", "pythonpath=."],
        cwd=tmp_path, env=entorno, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )
    assert salida.returncode == 0, salida.stdout + salida.stderr
    corridas = [linea for linea in salida.stdout.splitlines() if " PASSED " in linea and "tests/test_" in linea]
    archivos = list(dict.fromkeys(linea.split("tests/")[1].split("::")[0] for linea in corridas))
    assert archivos == ["test_z.py", "test_a.py", "test_m.py"]
