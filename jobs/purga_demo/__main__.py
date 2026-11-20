# -*- coding: utf-8 -*-
# ¤demo
"""Punto de entrada del Cloud Run Job: `python -m jobs.purga_demo`. Sale con 1 si se niega o falla.

Con `--comprobar` no borra nada: solo las comprobaciones de solo lectura del paso 5 del brief del
propietario (DEMO-05c R10), que imprimen números y nombres de tablas, nunca correos ni la URL.
"""
from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, make_url
from sqlalchemy.exc import SQLAlchemyError

from .almacen import Almacen, AlmacenGCS, ErrorAlmacen
from .guardias import PurgaRechazada, exigir_demo, faltan_politicas, tablas_sin_rls
from .purga import Destino, ErrorPurga, purgar


@contextmanager
def _lectura(destino: Destino):
    """Conexión para las guardias: la propia si es una `Connection`; si no, una nueva que no confirma."""
    if isinstance(destino, Connection):
        yield destino
    else:
        with destino.connect() as con:
            yield con


def ejecutar(destino: Destino, almacen: Almacen, ahora: datetime) -> int:
    """Guardia de políticas (DEMO-05c R9) y purga. Con una `Connection` no confirma nada."""
    try:
        with _lectura(destino) as con:
            faltan = faltan_politicas(con)
            sin_rls = tablas_sin_rls(con)
    except SQLAlchemyError as error:
        print(f"[purga-demo] ERROR: no se pudo comprobar las políticas de purga ({type(error).__name__}).",
              file=sys.stderr)
        return 1
    if sin_rls:
        print(f"[purga-demo] tablas sin RLS (las protegen los permisos y el filtro del código): {', '.join(sin_rls)}")
    if faltan:
        print(f"[purga-demo] ERROR: faltan políticas de purga en: {', '.join(faltan)}; ejecuta politicas_purga.sql",
              file=sys.stderr)
        return 1
    try:
        informe = purgar(destino, almacen, ahora)
    except (ErrorPurga, ErrorAlmacen) as error:
        print(f"[purga-demo] ERROR: {error}", file=sys.stderr)
        return 1
    print(f"[purga-demo] tenants={len(informe.tenants)} objetos={informe.objetos} filas={informe.filas} "
          f"sesiones_caducadas={informe.sesiones_caducadas}")
    return 0


_SQL_PERSONAS_FICTICIAS = "SELECT count(*) FROM users u WHERE public.es_persona_ficticia(u.id)"


def comprobar(destino: Destino) -> int:
    """R10: la guardia da vacío y `es_persona_ficticia` reconoce al menos a una persona ficticia. Sin borrar."""
    try:
        with _lectura(destino) as con:
            faltan = faltan_politicas(con)
            sin_rls = tablas_sin_rls(con)
            personas = 0 if faltan else con.execute(text(_SQL_PERSONAS_FICTICIAS)).scalar_one()
    except SQLAlchemyError as error:
        print(f"[purga-demo] ERROR: la comprobación falló ({type(error).__name__}).", file=sys.stderr)
        return 1
    print(f"[purga-demo] comprobacion faltan={len(faltan)} tablas_sin_rls={len(sin_rls)} "
          f"personas_ficticias={personas}")
    if faltan:
        print(f"[purga-demo] ERROR: faltan políticas de purga en: {', '.join(faltan)}; ejecuta politicas_purga.sql",
              file=sys.stderr)
        return 1
    if personas < 1:
        print("[purga-demo] ERROR: es_persona_ficticia no reconoce a ninguna persona ficticia; avisa al CTO.",
              file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    solo_comprobar = "--comprobar" in (sys.argv[1:] if argv is None else argv)
    url = os.environ.get("PURGA_DATABASE_URL", "")
    try:
        exigir_demo(url)
        motor = create_engine(make_url(url).set(drivername="postgresql+psycopg"), pool_pre_ping=True)
        if solo_comprobar:
            return comprobar(motor)
        almacen = AlmacenGCS.desde_entorno()
    except (PurgaRechazada, ErrorPurga, ErrorAlmacen) as error:
        print(f"[purga-demo] ERROR: {error}", file=sys.stderr)
        return 1
    return ejecutar(motor, almacen, datetime.now(timezone.utc))


if __name__ == "__main__":
    sys.exit(main())
