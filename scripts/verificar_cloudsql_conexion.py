# ¤¤qa-engineer
"""GCP-04 · Verificación notarial de la conexión a Cloud SQL. Solo lee: nunca migra ni escribe.

`¤cloud-run-perf` `¤seguridad-tenant` `¤ci-cd` — INV_LOPDP_CLOUD_SQL_AUTOPROXY

Comprueba, con la URL de `CLOUDSQL_DATABASE_URL` (o `DATABASE_URL`):
  1. el servidor es PostgreSQL 16;
  2. el rol de la sesión no es superusuario ni tiene BYPASSRLS (debe ser `lopdp_app`);
  3. la conexión va cifrada (SSL), salvo `--sin-ssl` para el contenedor local o el socket del proxy;
  4. toda tabla con políticas tiene ROW LEVEL SECURITY activa y forzada.

`--rol lopdp_app` hace `SET ROLE` tras conectar con el rol dueño (así lo hacen las pruebas).
Jamás imprime la URL. Salida: 0 todo correcto, 1 alguna comprobación falla, 2 no se pudo comprobar.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field

ROL_APLICACION = "lopdp_app"
VERSION_MAYOR = 16


@dataclass
class Estado:
    version_num: int
    rol: str
    superusuario: bool
    bypassrls: bool
    ssl: bool
    tablas_sin_rls: list[str] = field(default_factory=list)


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


def leer_estado(url: str, rol: str | None = None) -> Estado:
    from sqlalchemy import create_engine, text

    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    motor = create_engine(url)
    try:
        with motor.connect() as conexion:
            if rol:
                if not re.fullmatch(r"[a-z_][a-z0-9_]*", rol):
                    raise ValueError("nombre de rol no válido")
                # Equivale a SET ROLE, con el nombre como parámetro enlazado.
                conexion.execute(text("SELECT set_config('role', :rol, false)"), {"rol": rol})
            version, actual, superusuario, bypass, ssl = conexion.execute(text(_CONSULTA_ROL)).one()
            tablas = [fila[0] for fila in conexion.execute(text(_CONSULTA_TABLAS))]
            return Estado(version, actual, bool(superusuario), bool(bypass), bool(ssl), tablas)
    finally:
        motor.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rol", help="SET ROLE tras conectar (p. ej. lopdp_app)")
    parser.add_argument("--sin-ssl", action="store_true", help="no exigir SSL (contenedor local o socket del proxy)")
    args = parser.parse_args(argv)

    url = os.environ.get("CLOUDSQL_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        print("No se pudo comprobar: falta CLOUDSQL_DATABASE_URL o DATABASE_URL.", file=sys.stderr)
        return 2
    try:
        estado = leer_estado(url, args.rol)
    except Exception as exc:  # noqa: BLE001 — se informa la clase, nunca el mensaje (podría llevar la URL)
        print(f"No se pudo comprobar: error de conexión ({type(exc).__name__}).", file=sys.stderr)
        return 2
    fallos = evaluar(estado, exigir_ssl=not args.sin_ssl)
    print(f"PostgreSQL {estado.version_num // 10000} · rol {estado.rol} · ssl={estado.ssl}")
    for fallo in fallos:
        print(f"FALLA: {fallo}")
    if not fallos:
        print("CLOUD SQL OK: rol sin BYPASSRLS y RLS forzada en todas las tablas con políticas.")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
