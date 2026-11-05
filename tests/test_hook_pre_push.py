# ¤¤qa-engineer
"""El hook pre-push detiene main y un arnés en rojo, y solo avisa de lo que falte en la máquina.

Cada prueba trabaja en un clon temporal con un remoto local y un arnés de mentira: nunca toca este repositorio.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
RAMA = "tarea/juan-carlos/ci-07"
HOOK = (RAIZ / ".githooks" / "pre-push").read_bytes().replace(b"\r\n", b"\n")
INSTALADOR = RAIZ / "scripts" / "instalar_hooks.py"

ARNES_DE_MENTIRA = """import os, sys

def carpeta_postgres():
    return "x"

def preparar_servidor(carpeta):
    if os.environ.get("SIN_POSTGRES"):
        raise FileNotFoundError(carpeta)

if __name__ == "__main__":
    with open(os.environ["ARNES_REGISTRO"], "a", encoding="utf-8") as registro:
        registro.write(" ".join(sys.argv[1:] + os.environ.get("PYTEST_ADDOPTS", "").split()) + "\\n")
    sys.exit(int(os.environ.get("ARNES_SALIDA", "0")))
"""


class Repo:
    def __init__(self, base: Path):
        self.remoto = base / "remoto.git"
        self.clon = base / "clon"
        self.worktree = base / "worktree"
        self.registro = base / "arnes.log"
        entorno = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        identidad = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        self.entorno = {**entorno, **identidad, "LOPDP_PYTHON": sys.executable, "ARNES_REGISTRO": str(self.registro)}

    def git(self, *args: str, cwd: Path | None = None, **extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *args], cwd=cwd or self.worktree, env={**self.entorno, **extra}, capture_output=True, text=True, encoding="utf-8")

    def preparar(self, con_hook: bool = True, crlf: bool = False) -> None:
        subprocess.run(["git", "init", "--bare", "-b", "main", str(self.remoto)], check=True, capture_output=True)
        self.clon.mkdir()
        self.git("init", "-b", "main", cwd=self.clon)
        self.git("remote", "add", "origin", str(self.remoto), cwd=self.clon)
        (self.clon / "verificadores").mkdir()
        (self.clon / "verificadores" / "arnes_local.py").write_text(ARNES_DE_MENTIRA, encoding="utf-8")
        (self.clon / ".gitignore").write_text(".env\n", encoding="utf-8")
        if con_hook:
            (self.clon / ".githooks").mkdir()
            (self.clon / ".githooks" / "pre-push").write_bytes(HOOK.replace(b"\n", b"\r\n") if crlf else HOOK)
        self.git("add", ".", cwd=self.clon)
        self.git("commit", "-m", "base", cwd=self.clon)
        self.git("push", "origin", "main", cwd=self.clon)
        self.git("fetch", "origin", cwd=self.clon)
        self.git("worktree", "add", str(self.worktree), "-b", RAMA, "origin/main", cwd=self.clon)
        (self.worktree / ".env").write_text("TEST_DATABASE_URL=postgresql://x@127.0.0.1:55432/lopdp\n", encoding="utf-8")
        salida = subprocess.run([sys.executable, str(INSTALADOR)], cwd=self.clon, env=self.entorno, capture_output=True, text=True, encoding="utf-8")
        assert salida.returncode == 0, salida.stdout

    def commit(self) -> None:
        (self.worktree / "cambio.txt").write_text("x\n", encoding="utf-8")
        self.git("add", "cambio.txt")
        self.git("commit", "-m", "cambio")

    def en_remoto(self, rama: str) -> bool:
        return self.git("rev-parse", "--verify", "--quiet", f"refs/heads/{rama}", cwd=self.remoto).returncode == 0

    def corridas(self) -> list[str]:
        return self.registro.read_text(encoding="utf-8").splitlines() if self.registro.exists() else []


@pytest.fixture
def repo(tmp_path):
    instancia = Repo(tmp_path)
    instancia.preparar()
    instancia.commit()
    return instancia


def test_el_push_a_main_se_bloquea_sin_correr_el_arnes(repo):
    salida = repo.git("push", "origin", "HEAD:main")
    assert salida.returncode != 0
    assert "BLOQUEADO: push directo a main" in salida.stderr
    assert repo.corridas() == []


def test_el_borrado_de_main_tambien_se_bloquea(repo):
    assert repo.git("push", "origin", ":main").returncode != 0
    assert repo.en_remoto("main")


def test_un_arnes_en_rojo_detiene_el_push(repo):
    salida = repo.git("push", "origin", RAMA, ARNES_SALIDA="1")
    assert salida.returncode != 0
    assert "BLOQUEADO: el arnes local" in salida.stderr
    assert not repo.en_remoto(RAMA)


def test_un_arnes_en_verde_deja_pasar_y_recibe_la_base_main(repo):
    salida = repo.git("push", "origin", RAMA)
    assert salida.returncode == 0, salida.stderr
    assert repo.corridas() == ["--base origin/main --maxfail=1"]
    assert repo.en_remoto(RAMA)


def test_sin_postgres_avisa_y_no_bloquea(repo):
    salida = repo.git("push", "origin", RAMA, SIN_POSTGRES="1")
    assert salida.returncode == 0, salida.stderr
    assert "No hay PostgreSQL local" in salida.stderr
    assert repo.corridas() == []


def test_una_rama_sin_persona_avisa_y_no_bloquea(repo):
    repo.git("switch", "-c", "claude/otra")
    salida = repo.git("push", "origin", "claude/otra")
    assert salida.returncode == 0, salida.stderr
    assert "no nombra a una persona" in salida.stderr
    assert repo.corridas() == []


def test_la_carpeta_principal_no_corre_el_arnes(repo):
    repo.git("switch", "-c", "tarea/juan-carlos/desde-la-principal", "origin/main", cwd=repo.clon)
    salida = repo.git("push", "origin", "tarea/juan-carlos/desde-la-principal:copia", cwd=repo.clon)
    assert salida.returncode == 0, salida.stderr
    assert "carpeta principal" in salida.stderr
    assert repo.corridas() == []


def test_un_env_con_produccion_no_corre_el_arnes(repo):
    (repo.worktree / ".env").write_text("DATABASE_URL=postgresql://x@ep-late-hall.neon.tech/db\n", encoding="utf-8")
    salida = repo.git("push", "origin", RAMA)
    assert salida.returncode == 0, salida.stderr
    assert "apunta a produccion" in salida.stderr
    assert repo.corridas() == []


def test_lo_que_no_es_el_worktree_no_se_verifica(repo):
    repo.git("branch", "otra-rama", "HEAD~1")
    salida = repo.git("push", "origin", "otra-rama")
    assert salida.returncode == 0, salida.stderr
    assert "no es lo que hay en este worktree" in salida.stderr
    assert repo.corridas() == []


def test_el_hook_funciona_con_crlf_como_lo_deja_autocrlf(tmp_path):
    repo = Repo(tmp_path)
    repo.preparar(crlf=True)
    repo.commit()
    assert repo.git("push", "origin", RAMA, ARNES_SALIDA="1").returncode != 0
    assert repo.git("push", "origin", "HEAD:main").returncode != 0
    assert repo.corridas() == ["--base origin/main --maxfail=1"]


def test_una_rama_sin_el_hook_versionado_conserva_el_bloqueo_de_main(tmp_path):
    repo = Repo(tmp_path)
    repo.preparar(con_hook=False)
    repo.commit()
    salida = repo.git("push", "origin", "HEAD:main")
    assert salida.returncode != 0
    assert "BLOQUEADO: push directo a main" in salida.stderr
    assert repo.git("push", "origin", RAMA).returncode == 0


def test_el_instalador_respalda_el_hook_anterior_y_es_idempotente(tmp_path):
    repo = Repo(tmp_path)
    repo.preparar()
    hooks = repo.clon / ".git" / "hooks"
    (hooks / "pre-push").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    for _ in range(2):
        salida = subprocess.run([sys.executable, str(INSTALADOR)], cwd=repo.worktree, env=repo.entorno, capture_output=True)
        assert salida.returncode == 0
    assert (hooks / "pre-push.anterior").read_text(encoding="utf-8") == "#!/bin/sh\nexit 0\n"
    assert b"instalar_hooks.py" in (hooks / "pre-push").read_bytes()
    assert b"\r" not in (hooks / "pre-push").read_bytes()
    assert repo.git("config", "--get", "core.hooksPath").stdout == ""


def test_el_instalador_rechaza_un_hookspath_que_lo_anularia(tmp_path):
    repo = Repo(tmp_path)
    repo.preparar()
    repo.git("config", "core.hooksPath", ".githooks")
    salida = subprocess.run([sys.executable, str(INSTALADOR)], cwd=repo.clon, env=repo.entorno, capture_output=True)
    assert salida.returncode == 1
