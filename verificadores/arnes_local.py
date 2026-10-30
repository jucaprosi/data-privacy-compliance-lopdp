# ¤¤qa-engineer
"""Arnés rápido: la suite completa contra PostgreSQL local, en un solo comando y sin Neon.

Levanta el servidor local si hace falta, crea la base, migra e invoca arnes_cero_regresiones.py sin omitir ninguna
prueba. No sustituye a la corrida contra Neon del CI: no ejercita el pooler ni la latencia real.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PUERTO = 55432
BASE = "lopdp"
ROL = "lopdp_beta_owner"
URL_LOCAL = f"postgresql://{ROL}@127.0.0.1:{PUERTO}/{BASE}"
AJUSTES_SERVIDOR = f"-p {PUERTO} -c listen_addresses=127.0.0.1 -c fsync=off -c synchronous_commit=off -c full_page_writes=off"


# ¤postgres-local
def carpeta_postgres() -> Path:
    definida = os.environ.get("LOPDP_PG_DIR")
    if definida:
        return Path(definida)
    return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Programs" / "PostgreSQL16"


def binario(carpeta: Path, nombre: str) -> str:
    return str(carpeta / "pgsql" / "bin" / f"{nombre}.exe" if os.name == "nt" else carpeta / "pgsql" / "bin" / nombre)


def entorno_de_pruebas(base: dict[str, str]) -> dict[str, str]:
    return {**base, "TEST_DATABASE_URL": URL_LOCAL, "MIGRATION_DATABASE_URL": URL_LOCAL, "ARNES_BASE": "postgresql_local"}


def _psql(carpeta: Path, sentencia: str) -> str:
    salida = subprocess.run(
        [binario(carpeta, "psql"), "-h", "127.0.0.1", "-p", str(PUERTO), "-U", ROL, "-d", "postgres", "-Atc", sentencia],
        capture_output=True, text=True, check=True,
    )
    return salida.stdout.strip()


def preparar_servidor(carpeta: Path) -> None:
    activo = subprocess.run([binario(carpeta, "pg_isready"), "-h", "127.0.0.1", "-p", str(PUERTO)], capture_output=True)
    if activo.returncode != 0:
        # Sin salida heredada: el servidor queda vivo y conservaría abierta la tubería de quien lo arranca.
        subprocess.run(
            [binario(carpeta, "pg_ctl"), "-D", str(carpeta / "datos"), "-w", "-l", str(carpeta / "servidor.log"),
             "-o", AJUSTES_SERVIDOR, "start"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
        )
    if _psql(carpeta, f"SELECT 1 FROM pg_database WHERE datname = '{BASE}'") != "1":
        _psql(carpeta, f"CREATE DATABASE {BASE}")


def preparar_frontend() -> None:
    """tests/test_banco_preguntas.py compila con frontend/node_modules, que un worktree nuevo no trae."""
    if not (RAIZ / "frontend" / "node_modules").exists():
        subprocess.run([shutil.which("npm") or "npm", "ci", "--no-audit", "--no-fund"], cwd=RAIZ / "frontend", check=True)


def main() -> int:
    carpeta = carpeta_postgres()
    if not Path(binario(carpeta, "pg_ctl")).exists():
        print(f"[ARNES LOCAL] No está PostgreSQL 16 en {carpeta}. Instálelo como indica verificadores/README.md.")
        return 2
    preparar_servidor(carpeta)
    preparar_frontend()
    entorno = entorno_de_pruebas(dict(os.environ))
    migracion = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=RAIZ, env=entorno)
    if migracion.returncode != 0:
        return migracion.returncode
    return subprocess.run([sys.executable, str(RAIZ / "verificadores" / "arnes_cero_regresiones.py")], cwd=RAIZ, env=entorno).returncode


if __name__ == "__main__":
    sys.exit(main())
