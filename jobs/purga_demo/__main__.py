# -*- coding: utf-8 -*-
# ¤demo
"""Punto de entrada del Cloud Run Job: `python -m jobs.purga_demo`. Sale con 1 si se niega o falla."""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from .almacen import AlmacenGCS, ErrorAlmacen
from .guardias import PurgaRechazada, exigir_demo
from .purga import ErrorPurga, purgar


def main() -> int:
    url = os.environ.get("PURGA_DATABASE_URL", "")
    try:
        exigir_demo(url)
        motor = create_engine(make_url(url).set(drivername="postgresql+psycopg"), pool_pre_ping=True)
        informe = purgar(motor, AlmacenGCS.desde_entorno(), datetime.now(timezone.utc))
    except (PurgaRechazada, ErrorPurga, ErrorAlmacen) as error:
        print(f"[purga-demo] ERROR: {error}", file=sys.stderr)
        return 1
    print(f"[purga-demo] tenants={len(informe.tenants)} objetos={informe.objetos} filas={informe.filas} "
          f"sesiones_caducadas={informe.sesiones_caducadas}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
