"""La suite se detiene con un solo mensaje cuando el interprete no tiene los requisitos del proyecto."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _proyecto(tmp_path: Path, requisitos: str) -> Path:
    (tmp_path / "tests").mkdir()
    (tmp_path / "scripts").mkdir()
    shutil.copy(RAIZ / "tests" / "conftest.py", tmp_path / "tests" / "conftest.py")
    shutil.copy(RAIZ / "scripts" / "verificar_entorno.py", tmp_path / "scripts" / "verificar_entorno.py")
    (tmp_path / "requirements.txt").write_text(requisitos, encoding="utf-8")
    (tmp_path / "tests" / "test_uno.py").write_text("def test_uno():\n    assert True\n", encoding="utf-8")
    return tmp_path


# Se limpia PYTEST_ADDOPTS y cualquier variable de base del entorno heredado para probar la guardia de
# paquetes en aislamiento puro de proceso (sin archivos de entorno locales).
ENTORNO_AISLADO: dict[str, str] = {}


def _pytest(proyecto: Path) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if "DATABASE_URL" not in k and k != "PYTEST_ADDOPTS"}
    env.update(ENTORNO_AISLADO)
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                          cwd=proyecto, capture_output=True, text=True, env=env)


def test_un_interprete_incompleto_detiene_la_suite_con_un_solo_mensaje(tmp_path):
    res = _pytest(_proyecto(tmp_path, "pytest>=7\npaquete-inexistente-zzz>=1\n"))
    salida = res.stdout + res.stderr
    assert res.returncode == 3
    assert salida.count("paquete-inexistente-zzz") == 1
    assert "passed" not in salida and "failed" not in salida


def test_un_interprete_completo_ejecuta_la_suite(tmp_path):
    res = _pytest(_proyecto(tmp_path, "pytest>=7\n"))
    assert res.returncode == 0, res.stdout + res.stderr
    assert "1 passed" in res.stdout
