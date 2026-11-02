# ¤arbitro
"""La suite no arranca sobre producción ni en un worktree sin `.env` propio, y nunca imprime la URL."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SECRETO = "clave-que-no-debe-salir"
URL_PRODUCCION = f"postgresql://dueno:{SECRETO}@EP-LATE-HALL-prueba-pooler.neon.test/base"
URL_PRUEBAS = f"postgresql://dueno:{SECRETO}@ep-pruebas.neon.test/base"


def _proyecto(tmp_path: Path) -> Path:
    (tmp_path / "tests").mkdir()
    shutil.copy(RAIZ / "tests" / "conftest.py", tmp_path / "tests" / "conftest.py")
    (tmp_path / "tests" / "test_uno.py").write_text("def test_uno():\n    assert True\n", encoding="utf-8")
    return tmp_path


def _correr(proyecto: Path, **variables) -> subprocess.CompletedProcess:
    entorno = {k: v for k, v in os.environ.items() if "DATABASE_URL" not in k}
    entorno.update(UPSTASH_REDIS_URL="prueba", R2_ACCESS_KEY_ID="prueba", **variables)
    return subprocess.run([sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider"],
                          cwd=proyecto, capture_output=True, text=True, env=entorno)


def test_url_de_produccion_detiene_la_suite_sin_imprimirla(tmp_path):
    res = _correr(_proyecto(tmp_path), TEST_DATABASE_URL=URL_PRODUCCION)
    assert res.returncode == 3
    assert "TEST_DATABASE_URL, DATABASE_URL apunta a produccion" in res.stdout + res.stderr
    assert SECRETO not in res.stdout + res.stderr and "LATE-HALL" not in res.stdout + res.stderr


def test_database_url_de_produccion_sin_url_de_pruebas_tambien_se_detiene(tmp_path):
    res = _correr(_proyecto(tmp_path), DATABASE_URL=URL_PRODUCCION)
    assert res.returncode == 3 and "DATABASE_URL apunta a produccion" in res.stdout + res.stderr


def test_url_de_pruebas_pasa(tmp_path):
    assert _correr(_proyecto(tmp_path), TEST_DATABASE_URL=URL_PRUEBAS).returncode == 0


def test_worktree_sin_env_se_detiene_con_mensaje_claro(tmp_path):
    proyecto = _proyecto(tmp_path)
    (proyecto / ".git").write_text("gitdir: ../.git/worktrees/x\n", encoding="utf-8")
    res = _correr(proyecto, TEST_DATABASE_URL=URL_PRUEBAS)
    assert res.returncode == 3 and "no tiene .env propio" in res.stdout + res.stderr


def test_worktree_con_env_propio_pasa(tmp_path):
    proyecto = _proyecto(tmp_path)
    (proyecto / ".git").write_text("gitdir: ../.git/worktrees/x\n", encoding="utf-8")
    (proyecto / ".env").write_text(f"TEST_DATABASE_URL={URL_PRUEBAS}\n", encoding="utf-8")
    assert _correr(proyecto).returncode == 0


def test_carpeta_principal_sin_env_sigue_funcionando_como_en_ci(tmp_path):
    proyecto = _proyecto(tmp_path)
    (proyecto / ".git").mkdir()
    assert _correr(proyecto, TEST_DATABASE_URL=URL_PRUEBAS).returncode == 0
