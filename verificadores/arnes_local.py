# ¤¤qa-engineer
"""Arnés rápido: la suite contra PostgreSQL local, en un solo comando y sin Neon.

Levanta el servidor local si hace falta, crea la base, migra e invoca arnes_cero_regresiones.py con
Pytest en paralelo: cada worktree tiene su base en el servidor común, y esa base migrada es la plantilla
de la que clona la suya cada trabajador. Cada arranque borra los clones huérfanos de este worktree, y
`--limpiar` borra su base antes de retirarlo; las bases de otros worktrees no se tocan. Sin
argumentos corre todas las pruebas; con `--base REV` corre solo el alcance del cambio frente a REV
(salas tocadas, sus dependientes y el núcleo) y el certificado declara ese alcance. No sustituye a la
corrida contra Neon del CI: no ejercita el pooler ni la latencia real.
"""
import argparse
import hashlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PUERTO = 55432
LARGO_MAXIMO_DE_BASE = 48  # PostgreSQL admite 63 y conftest añade "_gw<n>_<corrida>" a cada clon.


# ¤postgres-local
# Justificación: el servidor local es uno solo. Con una base común, dos worktrees se pisaban datos y migraciones, y cada
#   corrida en paralelo cerraba las conexiones de la otra. El hash separa carpetas de igual nombre en rutas distintas.
def nombre_de_base(raiz: Path) -> str:
    ruta = str(raiz.resolve()).replace("\\", "/").lower()
    resumen = hashlib.sha256(ruta.encode("utf-8")).hexdigest()[:8]
    carpeta = re.sub(r"[^a-z0-9]+", "_", raiz.name.lower()).strip("_")
    return f"lopdp_{carpeta[:LARGO_MAXIMO_DE_BASE - 15]}_{resumen}".replace("__", "_")


def es_base_de_este_worktree(nombre: str, base: str) -> bool:
    return nombre == base or nombre.startswith(f"{base}_gw")


BASE = nombre_de_base(RAIZ)
ROL = "lopdp_beta_owner"
URL_LOCAL = f"postgresql://{ROL}@127.0.0.1:{PUERTO}/{BASE}"
# Cada archivo queda entero en un trabajador; cada trabajador clona su base en tests/conftest.py.
OPCIONES_PARALELO = "-n auto --dist loadfile"
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
    opciones = f"{base.get('PYTEST_ADDOPTS', '')} {OPCIONES_PARALELO}".strip()
    return {**base, "TEST_DATABASE_URL": URL_LOCAL, "MIGRATION_DATABASE_URL": URL_LOCAL, "ARNES_BASE": "postgresql_local",
            "PYTEST_ADDOPTS": opciones}


# ¤adpa
def entorno_con_alcance(entorno: dict[str, str], seleccion) -> dict[str, str]:
    """El arnés por salas pasa la lista al runner; el certificado declara el alcance en cualquier modo."""
    entorno = {**entorno, "ARNES_ALCANCE": seleccion.etiqueta}
    if seleccion.modo == "salas":
        entorno["ARNES_PRUEBAS"] = " ".join(seleccion.pruebas)
    return entorno


def _cargar_selector():
    ruta = RAIZ / "scripts" / "seleccionar_pruebas.py"
    spec = importlib.util.spec_from_file_location("seleccionar_pruebas", ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["seleccionar_pruebas"] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def _psql(carpeta: Path, sentencia: str) -> str:
    salida = subprocess.run(
        [binario(carpeta, "psql"), "-h", "127.0.0.1", "-p", str(PUERTO), "-U", ROL, "-d", "postgres", "-Atc", sentencia],
        capture_output=True, text=True, check=True,
    )
    return salida.stdout.strip()


def bases_de_este_worktree(carpeta: Path) -> list[str]:
    nombres = _psql(carpeta, "SELECT datname FROM pg_database").split()
    return [nombre for nombre in nombres if es_base_de_este_worktree(nombre, BASE)]


def borrar_clones_huerfanos(carpeta: Path) -> None:
    """Un trabajador que muere a la fuerza no borra su clon. Solo se tocan los clones de este worktree."""
    for nombre in bases_de_este_worktree(carpeta):
        if nombre != BASE:
            _psql(carpeta, f'DROP DATABASE IF EXISTS "{nombre}" WITH (FORCE)')


def limpiar(carpeta: Path) -> int:
    """Antes de retirar el worktree: borra su base y sus clones; las de otros worktrees no se tocan."""
    iniciar_servidor(carpeta)
    borrar_clones_huerfanos(carpeta)
    _psql(carpeta, f'DROP DATABASE IF EXISTS "{BASE}" WITH (FORCE)')
    print(f"[ARNES LOCAL] Base {BASE} y sus clones borrados.")
    return 0


def iniciar_servidor(carpeta: Path) -> None:
    activo =subprocess.run([binario(carpeta, "pg_isready"), "-h", "127.0.0.1", "-p", str(PUERTO)], capture_output=True)
    if activo.returncode != 0:
        # Sin salida heredada: el servidor queda vivo y conservaría abierta la tubería de quien lo arranca.
        subprocess.run(
            [binario(carpeta, "pg_ctl"), "-D", str(carpeta / "datos"), "-w", "-l", str(carpeta / "servidor.log"),
             "-o", AJUSTES_SERVIDOR, "start"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
        )


def preparar_servidor(carpeta: Path) -> None:
    iniciar_servidor(carpeta)
    borrar_clones_huerfanos(carpeta)
    if _psql(carpeta, f"SELECT 1 FROM pg_database WHERE datname = '{BASE}'") != "1":
        _psql(carpeta, f"CREATE DATABASE {BASE}")


def preparar_xdist() -> None:
    """requirements.txt no lo incluye mientras el CI corra en serie: se instala solo donde se usa."""
    if importlib.util.find_spec("xdist") is None:
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest-xdist"], check=True)


def preparar_frontend() -> None:
    """tests/test_banco_preguntas.py compila con frontend/node_modules, que un worktree nuevo no trae."""
    if not (RAIZ / "frontend" / "node_modules").exists():
        subprocess.run([shutil.which("npm") or "npm", "ci", "--no-audit", "--no-fund"], cwd=RAIZ / "frontend", check=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", metavar="REV", help="corre solo el alcance de los cambios frente a REV (p. ej. origin/main)")
    ap.add_argument("--limpiar", action="store_true", help="borra la base de este worktree y sus clones, y termina")
    args = ap.parse_args(argv)

    carpeta = carpeta_postgres()
    if not Path(binario(carpeta, "pg_ctl")).exists():
        print(f"[ARNES LOCAL] No está PostgreSQL 16 en {carpeta}. Instálelo como indica verificadores/README.md.")
        return 2
    if args.limpiar:
        return limpiar(carpeta)
    entorno = entorno_de_pruebas(dict(os.environ))
    if args.base:
        selector = _cargar_selector()
        seleccion = selector.seleccionar(selector.archivos_cambiados_localmente(args.base, RAIZ), RAIZ)
        print(f"[ARNES LOCAL] Alcance: {seleccion.etiqueta}"
              + (f" ({len(seleccion.pruebas)} archivos de prueba)" if seleccion.modo == "salas" else ""))
        for motivo in seleccion.motivos:
            print(f"  - {motivo}")
        entorno = entorno_con_alcance(entorno, seleccion)
    preparar_servidor(carpeta)
    preparar_xdist()
    if "ARNES_PRUEBAS" not in entorno or "test_banco_preguntas" in entorno["ARNES_PRUEBAS"]:
        preparar_frontend()
    migracion = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=RAIZ, env=entorno)
    if migracion.returncode != 0:
        return migracion.returncode
    return subprocess.run([sys.executable, str(RAIZ / "verificadores" / "arnes_cero_regresiones.py")], cwd=RAIZ, env=entorno).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
