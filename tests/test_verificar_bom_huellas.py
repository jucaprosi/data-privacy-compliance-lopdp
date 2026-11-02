# ¤arbitro
# ¤¤qa-engineer
"""El lint de BOM y huellas vive en un script: un BOM y una huella abierta fallan, y las exclusiones se conservan."""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "scripts" / "verificar_bom_huellas.py"
_spec = importlib.util.spec_from_file_location("verificar_bom_huellas", SCRIPT)
vbh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vbh)

BOM = b"\xef\xbb\xbf"
HUELLA = chr(166)


def _escribir(raiz: Path, relativa: str, contenido: bytes) -> str:
    ruta = raiz / relativa
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(contenido)
    return str(ruta)


def test_un_arbol_limpio_pasa(tmp_path):
    _escribir(tmp_path, "a.py", b"x = 1\n")
    _escribir(tmp_path, "b.md", b"# Titulo\n")
    assert vbh.encontrar_fallos(str(tmp_path)) == []


@pytest.mark.parametrize("nombre", ["a.py", "docs/b.md"])
def test_un_bom_falla(tmp_path, nombre):
    ruta = _escribir(tmp_path, nombre, BOM + b"x = 1\n")
    assert vbh.encontrar_fallos(str(tmp_path)) == [ruta]


def test_una_huella_abierta_falla_con_su_linea(tmp_path):
    ruta = _escribir(tmp_path, "a.py", f"x = 1\n# {HUELLA}pendiente\n".encode("utf-8"))
    assert vbh.encontrar_fallos(str(tmp_path)) == [f"{ruta}:L2"]


def test_la_huella_solo_cuenta_en_python_y_el_bom_solo_en_py_y_md(tmp_path):
    _escribir(tmp_path, "a.md", f"{HUELLA}nota\n".encode("utf-8"))
    _escribir(tmp_path, "a.txt", BOM + b"x\n")
    assert vbh.encontrar_fallos(str(tmp_path)) == []


@pytest.mark.parametrize("carpeta", [".git", ".github/workflows", "frontend/node_modules/x", ".pytest_cache", "a/__pycache__",
                                     "verificadores", "tests/verificadores_extra"])
def test_las_exclusiones_se_conservan_tambien_por_subcadena(tmp_path, carpeta):
    _escribir(tmp_path, f"{carpeta}/a.py", BOM + f"# {HUELLA}\n".encode("utf-8"))
    assert vbh.encontrar_fallos(str(tmp_path)) == []


def test_la_ruta_de_la_raiz_no_cuenta_para_las_exclusiones(tmp_path):
    raiz = tmp_path / "verificadores"
    ruta = _escribir(raiz, "a.py", BOM + b"x = 1\n")
    assert vbh.encontrar_fallos(str(raiz)) == [ruta]


def test_un_archivo_que_no_es_utf8_no_se_cuenta(tmp_path):
    _escribir(tmp_path, "a.py", b"\xff\xfe\n")
    assert vbh.encontrar_fallos(str(tmp_path)) == []


def test_el_cli_devuelve_1_con_un_fallo_y_0_sin_el(tmp_path):
    entorno = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    _escribir(tmp_path, "a.py", b"x = 1\n")
    assert subprocess.run([sys.executable, str(SCRIPT)], cwd=tmp_path, env=entorno, capture_output=True).returncode == 0
    _escribir(tmp_path, "b.py", BOM + b"x = 1\n")
    fallo = subprocess.run([sys.executable, str(SCRIPT)], cwd=tmp_path, env=entorno, capture_output=True, encoding="utf-8")
    assert fallo.returncode == 1 and "b.py" in fallo.stderr


def test_el_script_no_se_delata_a_si_mismo():
    assert not vbh.tiene_bom(str(SCRIPT)) and vbh.huellas_abiertas(str(SCRIPT)) == []


def test_ningun_trabajo_repite_el_lint_en_linea():
    flujo = (RAIZ / ".github" / "workflows" / "zero-regression-pipeline.yml").read_text(encoding="utf-8")
    assert flujo.count("run: python scripts/verificar_bom_huellas.py") == 2
    assert "os.walk" not in flujo and "chr(166)" not in flujo


def test_cada_trabajo_que_instala_usa_cache_y_npm_ci():
    flujo = (RAIZ / ".github" / "workflows" / "zero-regression-pipeline.yml").read_text(encoding="utf-8")
    assert "npm install" not in flujo
    assert flujo.count("run: npm ci") == 4
    assert flujo.count("cache: pip") == 3 and flujo.count("cache: npm") == 4
    assert flujo.count("cache-dependency-path: frontend/package-lock.json") == 4
