# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤arbitro
"""La suite toma su configuración del proceso, acepta solo bases locales y nunca imprime la URL ni secretos."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SECRETO = "clave-que-no-debe-salir"
HOST_REMOTO = "base.ejemplo.test"
URL_REMOTA = f"postgresql://usuaria_secreta:{SECRETO}@{HOST_REMOTO}:5432/lopdp"
URL_LOCAL = "postgresql://usuaria_local:clave@127.0.0.1:5432/lopdp"


def _proyecto(tmp_path: Path) -> Path:
    (tmp_path / "tests").mkdir(parents=True)
    shutil.copy(RAIZ / "tests" / "conftest.py", tmp_path / "tests" / "conftest.py")
    (tmp_path / "tests" / "test_uno.py").write_text("def test_uno():\n    assert True\n", encoding="utf-8")
    return tmp_path


def _correr(proyecto: Path, **variables: str) -> subprocess.CompletedProcess:
    claves_base = {"TEST_DATABASE_URL", "DATABASE_URL", "MIGRATION_DATABASE_URL", "PYTEST_ADDOPTS"}
    entorno = {k: v for k, v in os.environ.items() if k not in claves_base}
    entorno.update(variables)
    return subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider"],
        cwd=proyecto,
        capture_output=True,
        text=True,
        env=entorno,
    )


def test_base_no_local_detiene_la_suite_sin_imprimir_la_url(tmp_path):
    res = _correr(_proyecto(tmp_path), TEST_DATABASE_URL=URL_REMOTA)
    salida = res.stdout + res.stderr
    assert res.returncode == 3
    assert "TEST_DATABASE_URL" in salida
    assert HOST_REMOTO not in salida
    assert "usuaria_secreta" not in salida
    assert SECRETO not in salida


def test_base_local_pasa(tmp_path):
    res = _correr(_proyecto(tmp_path), TEST_DATABASE_URL=URL_LOCAL)
    assert res.returncode == 0


def test_arranca_en_carpeta_y_en_worktree(tmp_path):
    principal = _proyecto(tmp_path / "principal")
    (principal / ".git").mkdir()
    assert _correr(principal, TEST_DATABASE_URL=URL_LOCAL).returncode == 0

    worktree = _proyecto(tmp_path / "worktree")
    (worktree / ".git").write_text("gitdir: ../.git/worktrees/x\n", encoding="utf-8")
    assert _correr(worktree, TEST_DATABASE_URL=URL_LOCAL).returncode == 0
