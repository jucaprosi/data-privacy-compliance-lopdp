# -*- coding: utf-8 -*-
# ¤adpa ¤seguridad
"""BIB-117: conceder, revocar y listar capacidades editoriales de la Biblioteca en una rama de prueba.

Lo ejecuta una persona, nunca la IA, con la credencial del DUEÑO de la base de su rama de prueba:

  python scripts/capacidades_biblioteca.py --listar --confirmar-rama-desarrollo
  python scripts/capacidades_biblioteca.py --conceder --usuario U --capacidad editor --otorgante O --motivo "…" --confirmar-rama-desarrollo
  python scripts/capacidades_biblioteca.py --revocar  --usuario U --capacidad editor --otorgante O --motivo "…" --confirmar-rama-desarrollo

Guardas, todas antes de abrir conexión (código 2):
  - BIB_CAPACIDADES_DATABASE_URL obligatoria;
  - --confirmar-rama-desarrollo;
  - nunca producción (huella de app_core/huellas_produccion.py y la instancia de Cloud SQL de producción)
    ni la rama test compartida (lista de hosts de BIB-109, leída de scripts/cargar_plantillas_pmv.py).
No imprime la URL. No hay opción de baja: revocar es un UPDATE.
"""
from __future__ import annotations

import argparse
import ast
import asyncio
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
VARIABLE_URL = "BIB_CAPACIDADES_DATABASE_URL"
# Instancia y base de producción de Google Cloud (EVYDENTIA): una URL que las nombre nunca se usa.
HUELLAS_CLOUD_SQL_PRODUCCION = ("evydentia-production", "evydentia_prod")


# ¤adpa
def hosts_de_bib109() -> tuple[str, ...]:
    """HOSTS_PROHIBIDOS de BIB-109, leída del script sin importarlo (no se copia la lista)."""
    arbol = ast.parse((RAIZ / "scripts" / "cargar_plantillas_pmv.py").read_text(encoding="utf-8"))
    for nodo in arbol.body:
        if isinstance(nodo, ast.Assign) and any(getattr(t, "id", None) == "HOSTS_PROHIBIDOS" for t in nodo.targets):
            return tuple(ast.literal_eval(nodo.value))
    raise RuntimeError("No se encontró HOSTS_PROHIBIDOS en scripts/cargar_plantillas_pmv.py")


# ¤adpa
def motivo_de_rechazo(url: str, confirmado: bool) -> str | None:
    """Motivo para no conectar, o `None`. No abre conexión ni muestra la URL."""
    from app_core.huellas_produccion import apunta_a_produccion

    if not url.strip():
        return f"Falta {VARIABLE_URL} (la base de tu rama de prueba, con la credencial del dueño)."
    if not confirmado:
        return "Falta --confirmar-rama-desarrollo."
    minusculas = url.lower()
    if apunta_a_produccion(url) or any(h in minusculas for h in HUELLAS_CLOUD_SQL_PRODUCCION):
        return "La URL apunta a producción; no se abrió conexión."
    if any(h in minusculas for h in hosts_de_bib109()):
        return "La URL apunta a producción o a la rama test compartida; no se abrió conexión."
    return None


# ¤adpa
async def _ejecutar(url: str, args: argparse.Namespace) -> int:
    os.environ["DATABASE_URL"] = url
    from app_core.db.session import async_session_factory, engine
    from app_core.errors import ErrorNegocio
    from features.biblioteca import biblioteca_service as bib

    try:
        async with async_session_factory() as sesion, sesion.begin():
            if args.listar:
                for c in await bib.listar_capacidades(sesion):
                    estado = "revocada" if c.revocada_en else "vigente"
                    print(f"{c.usuario_id}\t{c.capacidad}\t{estado}\tconcedida_por={c.concedida_por}")
                return 0
            accion = bib.conceder_capacidad if args.conceder else bib.revocar_capacidad
            resultado = await accion(sesion, args.usuario, args.capacidad, args.otorgante, args.motivo)
            print(f"{resultado}: {args.usuario} {args.capacidad}")
            return 0
    except ErrorNegocio as error:
        print(f"Sin cambios: {error}")
        return 1
    finally:
        await engine.dispose()


# ¤adpa
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    modo = parser.add_mutually_exclusive_group(required=True)
    modo.add_argument("--listar", action="store_true")
    modo.add_argument("--conceder", action="store_true")
    modo.add_argument("--revocar", action="store_true")
    parser.add_argument("--usuario")
    parser.add_argument("--capacidad")
    parser.add_argument("--otorgante")
    parser.add_argument("--motivo")
    parser.add_argument("--confirmar-rama-desarrollo", action="store_true")
    args = parser.parse_args(argv)

    if not args.listar and not (args.usuario and args.capacidad and args.otorgante):
        print("--conceder y --revocar exigen --usuario, --capacidad, --otorgante y --motivo.")
        return 2
    rechazo = motivo_de_rechazo(os.environ.get(VARIABLE_URL, ""), args.confirmar_rama_desarrollo)
    if rechazo:
        print(rechazo)
        return 2
    return asyncio.run(_ejecutar(os.environ[VARIABLE_URL], args))


if __name__ == "__main__":
    sys.exit(main())
