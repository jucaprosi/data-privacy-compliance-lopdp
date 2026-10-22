# ¤seguridad
"""Comando de administración de operadores de la plataforma (ORG-09).

La lista de operadores la define el propietario fuera de la API: este comando la mantiene con
la credencial de migraciones (MIGRATION_DATABASE_URL), porque la aplicación (lopdp_app) solo puede
leer esa tabla y vincular el google_sub. Nunca imprime la URL.

Uso (desde la raíz del proyecto):
    python -m features.plataforma.administrar_operadores listar
    python -m features.plataforma.administrar_operadores alta <correo> "<nombre>"
    python -m features.plataforma.administrar_operadores baja <correo>

La baja desactiva (activo = FALSE): el registro se conserva para la auditoría.
"""
from __future__ import annotations

import argparse
import os
import sys
from urllib.parse import urlsplit
from uuid import uuid4

from sqlalchemy import create_engine, text


def _url() -> str:
    url = os.environ.get("MIGRATION_DATABASE_URL", "").strip().strip('"')
    if not url:
        raise SystemExit("MIGRATION_DATABASE_URL no está definida.")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _correo(valor: str) -> str:
    correo = valor.strip().lower()
    if "@" not in correo or correo.startswith("@") or correo.endswith("@"):
        raise SystemExit(f"Correo no válido: {valor!r}")
    return correo


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Administra los operadores de la plataforma.")
    sub = ap.add_subparsers(dest="accion", required=True)
    sub.add_parser("listar")
    alta = sub.add_parser("alta")
    alta.add_argument("correo")
    alta.add_argument("nombre")
    baja = sub.add_parser("baja")
    baja.add_argument("correo")
    args = ap.parse_args(argv)

    url = _url()
    print(f"Base de datos: {urlsplit(url).hostname}")
    engine = create_engine(url)
    try:
        with engine.begin() as c:
            if args.accion == "listar":
                filas = c.execute(text(
                    "SELECT email, nombre, activo, google_sub IS NOT NULL AS vinculado "
                    "FROM operadores_plataforma ORDER BY email"
                )).mappings().all()
                for f in filas:
                    print(f"{f['email']}  activo={f['activo']}  google_vinculado={f['vinculado']}  {f['nombre'] or ''}")
                print(f"{len(filas)} operador(es).")
            elif args.accion == "alta":
                correo = _correo(args.correo)
                fila = c.execute(text(
                    "UPDATE operadores_plataforma SET activo = TRUE, nombre = :n, updated_at = NOW() "
                    "WHERE LOWER(email) = :e RETURNING id"
                ), {"e": correo, "n": args.nombre}).first()
                if fila is None:
                    c.execute(text(
                        "INSERT INTO operadores_plataforma (id, email, nombre, activo) VALUES (:id, :e, :n, TRUE)"
                    ), {"id": str(uuid4()), "e": correo, "n": args.nombre})
                print(f"Operador activo: {correo}")
            else:
                correo = _correo(args.correo)
                fila = c.execute(text(
                    "UPDATE operadores_plataforma SET activo = FALSE, updated_at = NOW() "
                    "WHERE LOWER(email) = :e RETURNING id"
                ), {"e": correo}).first()
                if fila is None:
                    raise SystemExit(f"No existe el operador {correo}.")
                print(f"Operador desactivado: {correo}")
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(main())
