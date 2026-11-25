# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa
"""BIB-109: plantillas Markdown del PMV (data/biblioteca/pmv) en el catálogo editorial.

  --verificar           sin escritura ni base de datos (código 0 si las doce son válidas y cargables).
  --cargar --actor ID   carga con la ficha de cada plantilla: exige BIB109_DATABASE_URL, --entorno
                        (local por defecto) y --confirmar-entorno. Código 2, sin conectar, si la URL no
                        corresponde al entorno pedido. Deja cada plantilla En revisión; nunca publica.
                        Lo ejecuta una persona, nunca la IA. No imprime la URL.
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


ENTORNOS = ("local", "pruebas", "produccion", "demo")
HUELLAS_DEMO = ("evydentia-demo-db", "evydentia_demo")  # instancia y base de la demo (DEMO-12 R1)


# ¤adpa
def entorno_de_url(url: str) -> str | None:
    """Entorno que nombra la URL (sin abrir conexión): demo, local, produccion, pruebas o `None` si no se reconoce.

    La demo se reconoce antes que las demás reglas: su base por proxy local no debe pasar por «local».
    """
    from app_core.huellas_produccion import apunta_a_produccion, es_base_local

    minusculas = url.lower()
    if any(h in minusculas for h in HUELLAS_DEMO):
        return "demo"
    if es_base_local(url):
        return "local"
    if apunta_a_produccion(url) or any(h in minusculas for h in ("evydentia-production", "evydentia_prod")):
        return "produccion"
    return "pruebas" if "pruebas" in minusculas else None


# ¤adpa
def motivo_entorno(url: str, entorno: str, confirmado: bool) -> str | None:
    """Motivo para no conectar (código 2), o `None`. La URL nunca se imprime."""
    if not confirmado:
        return "Falta --confirmar-entorno."
    if entorno_de_url(url) != entorno:
        return f"La URL no corresponde al entorno «{entorno}»; no se abrió conexión."
    return None


# ¤adpa
def _imprimir_informe(informe: dict) -> None:
    print(f"{len(informe['plantillas'])} plantillas válidas en data/biblioteca/pmv")
    for p in informe["plantillas"]:
        print(f"  {p['codigo']}  v{p['version']}  {p['sha256']}  {p['nombre']}")
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
    parser.add_argument("--entorno", choices=ENTORNOS, default="local")
    parser.add_argument("--confirmar-entorno", "--confirmar-rama-desarrollo", dest="confirmar_entorno",
                        action="store_true")
    args = parser.parse_args(argv)

    url = os.environ.get("BIB109_DATABASE_URL", "")
    if args.cargar:
        if not url or not args.actor:
            print("Cargar exige BIB109_DATABASE_URL, --actor, --entorno y --confirmar-entorno.")
            return 2
        rechazo = motivo_entorno(url, args.entorno, args.confirmar_entorno)
        if rechazo:
            print(rechazo)
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
