# ¤¤qa-engineer
"""GCP-04 · Verificación notarial de la conexión a Cloud SQL. Solo lee: nunca migra ni escribe.

`¤cloud-run-perf` `¤seguridad-tenant` `¤ci-cd` — INV_LOPDP_CLOUD_SQL_AUTOPROXY

Comprueba, con la URL de `CLOUDSQL_DATABASE_URL` (solo esa variable, sin respaldo):
  1. el servidor es PostgreSQL 16;
  2. el rol de la sesión no es superusuario ni tiene BYPASSRLS (debe ser `lopdp_app`);
  3. la conexión va cifrada (SSL), salvo `--sin-ssl` para el contenedor local o el socket del proxy;
  4. toda tabla con políticas tiene ROW LEVEL SECURITY activa y forzada;
  5. el conjunto de `alembic current` es igual al de `alembic heads` del repositorio: una cabeza por sala (CI-18, CI-28).

La URL es la del rol dueño (`evydentia_app`): con ella se lee la revisión de Alembic, y `--rol lopdp_app`
hace `SET ROLE` después, para las comprobaciones de privilegios y RLS. Un solo comando.
Jamás imprime la URL. Salida: 0 todo correcto, 1 la base está atrasada o alguna comprobación falla,
2 falta la variable, la configuración o la conexión.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

ROL_APLICACION = "lopdp_app"
VERSION_MAYOR = 16
VARIABLE_URL = "CLOUDSQL_DATABASE_URL"
RAIZ = Path(__file__).resolve().parent.parent


@dataclass
class Estado:
    version_num: int
    rol: str
    superusuario: bool
    bypassrls: bool
    ssl: bool
    tablas_sin_rls: list[str] = field(default_factory=list)
    revision: set[str] = field(default_factory=set)


def evaluar(estado: Estado, exigir_ssl: bool = True) -> list[str]:
    """Lista de fallos (vacía si todo está bien). Función pura: no toca la base."""
    fallos = []
    if estado.version_num // 10000 != VERSION_MAYOR:
        fallos.append(f"el servidor no es PostgreSQL {VERSION_MAYOR} (server_version_num={estado.version_num})")
    if estado.superusuario:
        fallos.append(f"el rol {estado.rol} es superusuario")
    if estado.bypassrls:
        fallos.append(f"el rol {estado.rol} tiene BYPASSRLS")
    if estado.rol != ROL_APLICACION:
        fallos.append(f"la sesión usa el rol {estado.rol}, no {ROL_APLICACION}")
    if exigir_ssl and not estado.ssl:
        fallos.append("la conexión no va cifrada (SSL)")
    if estado.tablas_sin_rls:
        fallos.append("tablas con políticas sin RLS activa y forzada: " + ", ".join(sorted(estado.tablas_sin_rls)))
    return fallos


_CONSULTA_ROL = """
SELECT current_setting('server_version_num')::int, current_user, r.rolsuper, r.rolbypassrls,
       COALESCE((SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()), false)
FROM pg_roles r WHERE r.rolname = current_user
"""

_CONSULTA_TABLAS = """
SELECT n.nspname || '.' || c.relname
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind IN ('r', 'p')
  AND EXISTS (SELECT 1 FROM pg_policy p WHERE p.polrelid = c.oid)
  AND NOT (c.relrowsecurity AND c.relforcerowsecurity)
"""


def _conjunto(revisiones: Iterable[str] | str | None) -> set[str]:
    if revisiones is None:
        return set()
    if isinstance(revisiones, str):
        return {revisiones}
    return {r for r in revisiones if r}


# ¤revision-alembic
def motivo_revision(revision_en_base: Iterable[str] | str | None, cabezas: Iterable[str]) -> str | None:
    """Comprobación 5: por qué la base no está en la cabeza (None si lo está). Función pura."""
    base, repositorio = _conjunto(revision_en_base), _conjunto(cabezas)
    if len(repositorio) != 1:
        return f"el repositorio tiene {len(repositorio)} cabezas sin fusionar: {', '.join(sorted(repositorio))}"
    if not base:
        return "la base no tiene revisión de Alembic (falta alembic_version)"
    if base != repositorio:
        return (f"la base está en {', '.join(sorted(base))} y la cabeza es {', '.join(sorted(repositorio))}: "
                "está atrasada o va por otra rama")
    return None


# ¤revision-alembic
def motivo_revision_por_conjuntos(revision_en_base: Iterable[str] | str | None, cabezas: Iterable[str]) -> str | None:
    """Comprobación 5 con una cabeza por sala (CI-28): el conjunto de la base es igual al del repositorio.

    No supone una sola cabeza: cada sala tiene la suya. Función pura.
    """
    base, repositorio = _conjunto(revision_en_base), _conjunto(cabezas)
    if not repositorio:
        return "el repositorio no tiene ninguna cabeza de Alembic"
    if not base:
        return "la base no tiene revisión de Alembic (falta alembic_version)"
    sin_aplicar, ajenas = repositorio - base, base - repositorio
    if sin_aplicar:
        return (f"la base está atrasada: le faltan por aplicar las cabezas {', '.join(sorted(sin_aplicar))} "
                "(corra alembic upgrade heads)")
    if ajenas:
        return f"la base está en {', '.join(sorted(ajenas))}, que no es cabeza del repositorio: va por otra rama"
    return None


def comprobar_revision(revision_en_base: Iterable[str] | str | None, cabezas: Iterable[str]) -> int:
    """0 si la base está en la única cabeza del repositorio; 1 si no."""
    return 0 if motivo_revision(revision_en_base, cabezas) is None else 1


def cabezas_del_repositorio(raiz: Path = RAIZ) -> set[str]:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config(str(raiz / "alembic.ini"))
    config.set_main_option("script_location", str(raiz / "alembic"))
    return set(ScriptDirectory.from_config(config).get_heads())


def _leer_revision(conexion) -> set[str]:
    from alembic.runtime.migration import MigrationContext

    return set(MigrationContext.configure(conexion).get_current_heads())


def leer_estado(url: str, rol: str | None = None) -> Estado:
    from sqlalchemy import create_engine, text

    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    motor = create_engine(url)
    try:
        with motor.connect() as conexion:
            # CI-18 (opción b): la revisión se lee con el rol de la conexión (el dueño), ANTES de SET ROLE;
            # a lopdp_app no se le concede lectura de alembic_version.
            revision = _leer_revision(conexion)
            if rol:
                if not re.fullmatch(r"[a-z_][a-z0-9_]*", rol):
                    raise ValueError("nombre de rol no válido")
                # Equivale a SET ROLE, con el nombre como parámetro enlazado.
                conexion.execute(text("SELECT set_config('role', :rol, false)"), {"rol": rol})
            version, actual, superusuario, bypass, ssl = conexion.execute(text(_CONSULTA_ROL)).one()
            tablas = [fila[0] for fila in conexion.execute(text(_CONSULTA_TABLAS))]
            return Estado(version, actual, bool(superusuario), bool(bypass), bool(ssl), tablas, revision)
    finally:
        motor.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rol", help="SET ROLE tras conectar (p. ej. lopdp_app)")
    parser.add_argument("--sin-ssl", action="store_true", help="no exigir SSL (contenedor local o socket del proxy)")
    args = parser.parse_args(argv)

    url = os.environ.get(VARIABLE_URL)
    if not url:
        print(f"No se pudo comprobar: falta {VARIABLE_URL} (no se usa DATABASE_URL).", file=sys.stderr)
        return 2
    try:
        cabezas = cabezas_del_repositorio()
    except Exception as exc:  # noqa: BLE001
        print(f"No se pudo comprobar: configuración de Alembic ({type(exc).__name__}).", file=sys.stderr)
        return 2
    try:
        estado = leer_estado(url, args.rol)
    except Exception as exc:  # noqa: BLE001 — se informa la clase, nunca el mensaje (podría llevar la URL)
        print(f"No se pudo comprobar: error de conexión ({type(exc).__name__}).", file=sys.stderr)
        return 2
    fallos = evaluar(estado, exigir_ssl=not args.sin_ssl)
    motivo = motivo_revision_por_conjuntos(estado.revision, cabezas)
    if motivo:
        fallos.append(motivo)
    print(f"PostgreSQL {estado.version_num // 10000} · rol {estado.rol} · ssl={estado.ssl}")
    print(f"alembic current: {', '.join(sorted(estado.revision)) or '(sin revisión)'} · alembic heads: {', '.join(sorted(cabezas))}")
    for fallo in fallos:
        print(f"FALLA: {fallo}")
    if not fallos:
        print("CLOUD SQL OK: rol sin BYPASSRLS, RLS forzada en todas las tablas con políticas y base en todas las cabezas de Alembic.")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
