# ¤¤qa-engineer
"""Comprueba que la base de pruebas esté en la cabeza de Alembic del repositorio. Solo lee: nunca migra.

Sin esto, una migración sin aplicar se descubre tarde, como decenas de pruebas fallidas por una columna ausente.
Imprime las dos revisiones y jamás la URL. Salida: 0 coinciden, 1 no coinciden, 2 no se pudo comprobar.
"""
import os
import sys
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine

RAIZ = Path(__file__).resolve().parent.parent


# ¤revision-alembic
def cabezas_del_repositorio(raiz: Path = RAIZ) -> set[str]:
    config = Config(str(raiz / "alembic.ini"))
    config.set_main_option("script_location", str(raiz / "alembic"))
    return set(ScriptDirectory.from_config(config).get_heads())


def revision_de_la_base(url: str) -> set[str]:
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    motor = create_engine(url)
    try:
        with motor.connect() as conexion:
            return set(MigrationContext.configure(conexion).get_current_heads())
    finally:
        motor.dispose()


def diagnostico(base: set[str], repositorio: set[str]) -> str | None:
    if base == repositorio:
        return None
    ajenas = sorted(base - repositorio)
    if not base:
        return "la base no tiene revisión de Alembic"
    if ajenas:
        return (f"la base está en {ajenas}, que no es la cabeza de esta rama: o falta la migración en la rama, "
                "o la base va por delante con otra tarea")
    return "la base no está en la cabeza del repositorio"


def main() -> int:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        print("[REVISIÓN] Falta TEST_DATABASE_URL.")
        return 2
    repositorio = cabezas_del_repositorio()
    try:
        base = revision_de_la_base(url)
    except Exception as error:
        # El texto de un error de conexión puede incluir el host: solo se imprime el tipo.
        print(f"[REVISIÓN] No se pudo leer la base: {type(error).__name__}.")
        return 2
    print(f"[REVISIÓN] alembic current: {', '.join(sorted(base)) or '(sin revisión)'}")
    print(f"[REVISIÓN] alembic heads:   {', '.join(sorted(repositorio))}")
    problema = diagnostico(base, repositorio)
    if problema:
        print(f"[REVISIÓN] No coinciden: {problema}. Este paso no migra; aplíquela a mano y anótela en "
              "governance/operaciones/REGISTRO_MIGRACIONES_MANUALES.md.")
        return 1
    print("[REVISIÓN] La base coincide con el repositorio.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
