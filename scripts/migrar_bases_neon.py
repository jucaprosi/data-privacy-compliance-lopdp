# -*- coding: utf-8 -*-
# ¤¤qa-engineer
"""Lleva a la cabeza de Alembic las bases de pruebas de Neon, solo desde main y después de fusionar.

Hacia main, el CI de Neon solo compara la revisión de la base con la cabeza del repositorio
(verificar_revision_alembic.py) y no migra. Cuando entra a main una migración, cada base por persona se queda una
fusión por detrás y el siguiente PR de esa persona falla sin culpa de su trabajo. Este script cierra ese hueco: migra
siempre hacia código ya fusionado, nunca hacia la cabeza de un PR, así que ninguna base queda por delante de otros PR.

Cada base se activa con su secreto NEON_MIGRACION_URL_<BASE>, la cadena directa del rol dueño. Sin secretos no hace
nada. Una base que ya está por delante de main, o que no tiene revisión de Alembic, no se toca. Nunca imprime una
cadena de conexión. Salida: 0 todo al día o sin trabajo, 1 si alguna migración falló, 2 si no corre sobre main.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
if str(AQUI) not in sys.path:
    sys.path.insert(0, str(AQUI))

from alembic.config import Config  # noqa: E402
from alembic.script import ScriptDirectory  # noqa: E402

from verificar_revision_alembic import cabezas_del_repositorio, revision_de_la_base  # noqa: E402

RAIZ = AQUI.parent

# Rama de Neon (test-<nombre>) y el secreto que la activa.
BASES = (
    ("main", "NEON_MIGRACION_URL_MAIN"),
    ("juan-carlos", "NEON_MIGRACION_URL_JUAN_CARLOS"),
    ("aleczandra", "NEON_MIGRACION_URL_ALECZANDRA"),
    ("jose", "NEON_MIGRACION_URL_JOSE"),
)
AL_DIA, MIGRADA, OMITIDA, FALLO = "AL DÍA", "MIGRADA", "OMITIDA", "FALLO"
_CONEXION = re.compile(r"[a-z][a-z0-9+.-]*://\S+", re.IGNORECASE)


# ¤revision-alembic
def sin_conexiones(texto: str) -> str:
    """Un error de alembic o de la base puede traer la cadena de conexión: nunca sale tal cual."""
    return _CONEXION.sub("***", texto)


def revisiones_conocidas(raiz: Path = RAIZ) -> set[str]:
    """Todas las revisiones del repositorio, no solo las cabezas: una base en una revisión antigua está atrasada."""
    config = Config(str(raiz / "alembic.ini"))
    config.set_main_option("script_location", str(raiz / "alembic"))
    return {revision.revision for revision in ScriptDirectory.from_config(config).walk_revisions()}


def alembic_upgrade(url: str) -> tuple[int, str]:
    entorno = {**os.environ, "MIGRATION_DATABASE_URL": url}
    entorno.pop("DATABASE_URL", None)
    resultado = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=RAIZ, env=entorno, capture_output=True, text=True, encoding="utf-8",
    )
    return resultado.returncode, resultado.stderr or resultado.stdout


def _revisiones(conjunto: set[str]) -> str:
    return ", ".join(sorted(conjunto)) or "(sin revisión)"


# ¤revision-alembic
def migrar_base(url: str, repositorio: set[str], conocidas: set[str], leer=revision_de_la_base,
                migrar=alembic_upgrade) -> tuple[str, str]:
    try:
        antes = leer(url)
    except Exception as error:  # el texto de un error de conexión puede incluir el host
        return FALLO, f"no se pudo leer la base ({type(error).__name__})"
    if antes == repositorio:
        return AL_DIA, _revisiones(antes)
    if not antes:
        return OMITIDA, "la base no tiene revisión de Alembic; no se crea desde cero aquí"
    ajenas = sorted(antes - conocidas)
    if ajenas:
        return OMITIDA, f"la base está en {ajenas}, que main no conoce (va por delante); no se toca"
    codigo, texto = migrar(url)
    if codigo != 0:
        ultima = next((linea for linea in reversed(sin_conexiones(texto).splitlines()) if linea.strip()), "sin detalle")
        return FALLO, f"alembic upgrade terminó con {codigo}: {ultima[:200]}"
    try:
        despues = leer(url)
    except Exception as error:
        return FALLO, f"migró, pero no se pudo releer la base ({type(error).__name__})"
    if despues != repositorio:
        return FALLO, f"tras migrar quedó en {sorted(despues)} y no en {sorted(repositorio)}"
    return MIGRADA, f"{_revisiones(antes)} a {_revisiones(repositorio)}"


def main(entorno=None, leer=revision_de_la_base, migrar=alembic_upgrade) -> int:
    entorno = os.environ if entorno is None else entorno
    if entorno.get("GITHUB_ACTIONS") and entorno.get("GITHUB_REF") != "refs/heads/main":
        print("[MIGRAR] Solo corre sobre main: se migra hacia código ya fusionado, nunca hacia un PR.")
        return 2
    configuradas = [(nombre, entorno[secreto]) for nombre, secreto in BASES if entorno.get(secreto)]
    if not configuradas:
        print("[MIGRAR] No hay secretos NEON_MIGRACION_URL_*: no hay nada que migrar.")
        return 0
    repositorio = cabezas_del_repositorio()
    conocidas = revisiones_conocidas()
    print(f"[MIGRAR] alembic heads: {_revisiones(repositorio)}")
    fallos = 0
    for nombre, url in configuradas:
        estado, detalle = migrar_base(url, repositorio, conocidas, leer, migrar)
        print(f"[MIGRAR] test-{nombre}: {estado}: {sin_conexiones(detalle)}")
        if estado == OMITIDA and entorno.get("GITHUB_ACTIONS"):
            print(f"::warning title=Base de Neon sin migrar::test-{nombre}: {sin_conexiones(detalle)}")
        fallos += estado == FALLO
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
