# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤seguridad
"""Comando de administración de operadores de la plataforma (ORG-09).

La lista de operadores la define el propietario fuera de la API: este comando la mantiene con
la credencial de migraciones (MIGRATION_DATABASE_URL), porque la aplicación (lopdp_app) solo puede
leer esa tabla y vincular el google_sub. Nunca imprime la URL.

Uso (desde la raíz del proyecto):
    python -m features.plataforma.administrar_operadores listar
    python -m features.plataforma.administrar_operadores alta <correo> "<nombre>"
    python -m features.plataforma.administrar_operadores baja <correo>
    python -m features.plataforma.administrar_operadores vincular

La baja desactiva (activo = FALSE): el registro se conserva para la auditoría.
OPE-01: `alta` y `vincular` crean o recuperan el usuario de cada operador (por el pasillo de organizacion,
sin membresía en ningún tenant) y guardan `usuario_id`. `vincular` se puede repetir sin efecto. Funcionan
igual contra la base de la demo con su `MIGRATION_DATABASE_URL` (R2b); los ejecuta el propietario.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from urllib.parse import urlsplit
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_LISTAR = text(
    "SELECT email, nombre, activo, google_sub IS NOT NULL AS vinculado, usuario_id "
    "FROM operadores_plataforma ORDER BY email"
)
_ALTA = text(
    "UPDATE operadores_plataforma SET activo = TRUE, nombre = :n, updated_at = NOW() "
    "WHERE LOWER(email) = :e RETURNING id"
)
_INSERTAR = text("INSERT INTO operadores_plataforma (id, email, nombre, activo) VALUES (:id, :e, :n, TRUE)")
_BAJA = text(
    "UPDATE operadores_plataforma SET activo = FALSE, updated_at = NOW() WHERE LOWER(email) = :e RETURNING id"
)


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


async def ejecutar(session: AsyncSession, args: argparse.Namespace) -> None:
    """Una orden sobre la sesión dada (la prueba la ejecuta con su propia sesión)."""
    from features.plataforma.services import operador_engine

    if args.accion == "listar":
        filas = (await session.execute(_LISTAR)).mappings().all()
        for f in filas:
            print(f"{f['email']}  activo={f['activo']}  google_vinculado={f['vinculado']}  "
                  f"usuario={'sí' if f['usuario_id'] else 'no'}  {f['nombre'] or ''}")
        print(f"{len(filas)} operador(es).")
    elif args.accion == "alta":
        correo = _correo(args.correo)
        fila = (await session.execute(_ALTA, {"e": correo, "n": args.nombre})).first()
        operador_id = fila[0] if fila is not None else str(uuid4())
        if fila is None:
            await session.execute(_INSERTAR, {"id": operador_id, "e": correo, "n": args.nombre})
        await operador_engine.enlazar_usuario(session, operador_id)
        print(f"Operador activo con su usuario: {correo}")
    elif args.accion == "vincular":
        enlazados = await operador_engine.vincular_operadores(session)
        for f in enlazados:
            print(f"{f['email']}  usuario={'sí' if f['usuario_id'] else 'no'}  ha_entrado={f['ha_entrado']}")
        print(f"{len(enlazados)} operador(es) activo(s).")
    else:
        correo = _correo(args.correo)
        if (await session.execute(_BAJA, {"e": correo})).first() is None:
            raise SystemExit(f"No existe el operador {correo}.")
        print(f"Operador desactivado: {correo}")


def _argumentos(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Administra los operadores de la plataforma.")
    sub = ap.add_subparsers(dest="accion", required=True)
    sub.add_parser("listar")
    sub.add_parser("vincular")
    alta = sub.add_parser("alta")
    alta.add_argument("correo")
    alta.add_argument("nombre")
    baja = sub.add_parser("baja")
    baja.add_argument("correo")
    return ap.parse_args(argv)


async def _principal(args: argparse.Namespace) -> None:
    url = _url()
    print(f"Base de datos: {urlsplit(url).hostname}")
    os.environ["DATABASE_URL"] = url  # una sola fuente de sesión: app_core.db.session la lee al importarse
    from app_core.db import session as sesion_bd

    try:
        async with sesion_bd.async_session_factory() as session, session.begin():
            await ejecutar(session, args)
    finally:
        await sesion_bd.engine.dispose()


def main(argv: list[str] | None = None) -> int:
    if sys.platform == "win32":  # psycopg asíncrono necesita el bucle selector en Windows
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(_principal(_argumentos(argv)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
