# -*- coding: utf-8 -*-
# ¤adpa
"""BIB-109: plantillas Markdown del PMV (data/biblioteca/pmv) en el catálogo editorial.

  --verificar           sin escritura ni base de datos (código 0 si las doce son válidas y cargables).
  --cargar --actor ID   carga en una rama de desarrollo: exige BIB109_DATABASE_URL y
                        --confirmar-rama-desarrollo. Deja cada plantilla En revisión; nunca publica.
                        Nunca producción ni la rama test compartida. No imprime la URL.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
HOSTS_PROHIBIDOS = ("ep-late-hall-b50bpbk5", "ep-soft-darkness-b5z454vp")


# ¤adpa
def _imprimir_informe(informe: dict) -> None:
    print(f"{len(informe['plantillas'])} plantillas válidas en data/biblioteca/pmv")
    for p in informe["plantillas"]:
        print(f"  {p['codigo']}  v{p['version']}  validacion_legal={p['validacion_legal']}  {p['sha256']}  {p['nombre']}")
    for error in informe["errores"]:
        print(f"ERROR: {error}")


# ¤adpa
async def _cargar(url: str, actor: str) -> dict:
    # Única fuente de sesión del proyecto: app_core.db.session, apuntada a la rama de desarrollo.
    os.environ["DATABASE_URL"] = url
    from sqlalchemy import text
    from app_core.db.session import async_session_factory, engine
    from features.biblioteca import biblioteca_service as bib

    try:
        async with async_session_factory() as sesion, sesion.begin():
            # Privilegios mínimos de la aplicación: RLS y disparadores editoriales se aplican igual que en la API.
            await sesion.execute(text("SET LOCAL ROLE lopdp_app"))
            return await bib.cargar_plantillas_pmv(sesion, actor, RAIZ)
    finally:
        await engine.dispose()


# ¤adpa
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    modo = parser.add_mutually_exclusive_group(required=True)
    modo.add_argument("--verificar", action="store_true")
    modo.add_argument("--cargar", action="store_true")
    parser.add_argument("--actor", help="Id de usuario con capacidad editorial 'editor'")
    parser.add_argument("--confirmar-rama-desarrollo", action="store_true")
    args = parser.parse_args(argv)

    url = os.environ.get("BIB109_DATABASE_URL", "")
    if args.cargar:
        if not url or not args.confirmar_rama_desarrollo or not args.actor:
            print("Cargar exige BIB109_DATABASE_URL (rama de desarrollo), --actor y --confirmar-rama-desarrollo.")
            return 2
        if any(host in url.lower() for host in HOSTS_PROHIBIDOS):
            print("Producción o rama test compartida prohibidas; no se abrió conexión.")
            return 2

    from features.biblioteca import biblioteca_service as bib
    informe = bib.verificar_plantillas_pmv(RAIZ)
    _imprimir_informe(informe)
    if informe["errores"]:
        return 1
    if args.verificar:
        print("Verificación sin escritura: OK")
        return 0

    from api.errores import ErrorNegocio
    try:
        resultado = asyncio.run(_cargar(url, args.actor))
    except ErrorNegocio as error:
        print(f"Carga revertida: {error}")
        return 1
    print(json.dumps(resultado, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
