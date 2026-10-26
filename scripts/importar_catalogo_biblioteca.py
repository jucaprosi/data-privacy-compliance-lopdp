# -*- coding: utf-8 -*-
# ¤adpa
"""BIB-108: inventario inicial de Biblioteca desde el kit v1.

  --verificar            sin escritura ni base de datos (código 0 si todo cuadra).
  --escribir-manifiesto  regenera data/biblioteca/manifiesto_inicial.json desde el kit.
  --importar --actor ID  importa en una rama de desarrollo: exige BIB108_DATABASE_URL y
                         --confirmar-rama-desarrollo. Nunca producción. No imprime la URL.
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
HOST_PRODUCCION = "ep-late-hall-b50bpbk5"


# ¤adpa
def _imprimir_informe(informe: dict) -> None:
    print(f"Clave {informe['clave']}: {informe['entradas']} entradas = {informe['con_archivo']} con archivo + "
          f"{informe['salida_por_mapear']} por mapear + {informe['planificada']} planificadas")
    for archivo in informe["archivos"]:
        print(f"  {archivo['codigo']:<8} {archivo['tipo']} {archivo['tamano']:>7} B  {archivo['sha256']}  apertura={archivo['apertura']}")
    for error in informe["errores"]:
        print(f"ERROR: {error}")


# ¤adpa
async def _importar(url: str, actor: str, clave: str) -> dict:
    # Única fuente de sesión del proyecto: app_core.db.session, apuntada a la rama de desarrollo.
    os.environ["DATABASE_URL"] = url
    from sqlalchemy import text
    from app_core.db.session import async_session_factory, engine
    from features.biblioteca import biblioteca_service as bib

    try:
        async with async_session_factory() as sesion, sesion.begin():
            # Privilegios mínimos de la aplicación: RLS y disparadores editoriales se aplican igual que en la API.
            await sesion.execute(text("SET LOCAL ROLE lopdp_app"))
            return await bib.importar(sesion, actor, bib.cargar_manifiesto(RAIZ), RAIZ, clave)
    finally:
        await engine.dispose()


# ¤adpa
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    modo = parser.add_mutually_exclusive_group(required=True)
    modo.add_argument("--verificar", action="store_true")
    modo.add_argument("--escribir-manifiesto", action="store_true")
    modo.add_argument("--importar", action="store_true")
    parser.add_argument("--actor", help="Id de usuario con capacidad editorial 'editor'")
    parser.add_argument("--clave", help="Clave de importación (por defecto la del kit v1)")
    parser.add_argument("--confirmar-rama-desarrollo", action="store_true")
    args = parser.parse_args(argv)

    from features.biblioteca import biblioteca_service as bib
    if args.escribir_manifiesto:
        destino = RAIZ / "data/biblioteca/manifiesto_inicial.json"
        destino.write_text(json.dumps(bib.construir_manifiesto(RAIZ), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Manifiesto escrito en {destino.relative_to(RAIZ)}")
        return 0

    url = os.environ.get("BIB108_DATABASE_URL", "")
    if args.importar:
        if not url or not args.confirmar_rama_desarrollo or not args.actor:
            print("Importar exige BIB108_DATABASE_URL (rama de desarrollo), --actor y --confirmar-rama-desarrollo.")
            return 2
        if HOST_PRODUCCION in url.lower():
            print("Host de producción prohibido; no se abrió conexión.")
            return 2

    informe = bib.verificar_manifiesto(bib.cargar_manifiesto(RAIZ), RAIZ)
    _imprimir_informe(informe)
    if informe["errores"]:
        return 1
    if args.verificar:
        print("Verificación sin escritura: OK")
        return 0

    from api.errores import ErrorNegocio
    try:
        resultado = asyncio.run(_importar(url, args.actor, args.clave or bib.CLAVE_INICIAL))
    except ErrorNegocio as error:
        print(f"Importación revertida: {error}")
        return 1
    print(json.dumps(resultado, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
