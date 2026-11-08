# ¤entorno-pruebas ¤seguridad-tenant
"""Siembra idempotente del entorno de pruebas de EVYDENTIA (EP-03).

Contrato: `PRD_EVYDENTIA_REVENTA_NUBE.md` §5.5 e invariante 53. En pruebas el modo es `oidc`: quienes
prueban entran con su cuenta de Google y la siembra solo les asigna un rol en una organización ficticia.

Uso (PowerShell, desde la raíz del worktree):

    python scripts/sembrar_entorno_pruebas.py --testers herramientas\\testers-entorno-pruebas.txt --bucket <bucket-de-pruebas>

- Guardia: exige `HUELLA_PROYECTO_PRODUCCION` y se niega si esa huella aparece en `MIGRATION_DATABASE_URL`
  o en el bucket de destino; también si la URL es la de la base de producción (SEC-15).
- Salida: solo cuenta lo creado y lo que ya existía. Nunca imprime la URL ni los correos.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import os
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app_core.huellas_produccion import apunta_a_produccion  # noqa: E402
from scripts.datos_sinteticos import clips, evidencias, organizaciones  # noqa: E402

TESTERS_POR_DEFECTO = Path("herramientas") / "testers-entorno-pruebas.txt"


class GuardiaError(RuntimeError):
    """La siembra se niega a correr. El mensaje nunca contiene la URL."""


def validar_destino(url: str | None, bucket: str | None, entorno=None) -> None:
    entorno = os.environ if entorno is None else entorno
    huella = (entorno.get("HUELLA_PROYECTO_PRODUCCION") or "").strip().lower()
    if not huella:
        raise GuardiaError("Falta HUELLA_PROYECTO_PRODUCCION: sin ella no se puede descartar producción.")
    if not url or not url.strip():
        raise GuardiaError("Falta MIGRATION_DATABASE_URL.")
    if huella in url.lower() or apunta_a_produccion(url):
        raise GuardiaError("La base de destino es la de producción. Siembra cancelada.")
    if bucket and huella in bucket.lower():
        raise GuardiaError("El bucket de destino es de producción. Siembra cancelada.")


def ruta_en_repositorio(ruta: Path) -> bool:
    """Verdadero si git rastrea el archivo: entonces sus correos estarían en el repositorio."""
    import subprocess

    try:
        relativa = ruta.resolve().relative_to(RAIZ)
    except ValueError:
        return False
    salida = subprocess.run(
        ["git", "ls-files", "--error-unmatch", relativa.as_posix()],
        cwd=RAIZ, capture_output=True, text=True,
    )
    return salida.returncode == 0


class AlmacenLocal:
    """Destino en una carpeta local (pruebas y ensayo). Compara el hash antes de escribir."""

    def __init__(self, carpeta: Path):
        self.carpeta = Path(carpeta)

    def asegurar(self, objeto) -> bool:
        destino = self.carpeta / objeto.clave
        if destino.exists() and destino.read_bytes() == objeto.datos:
            return False
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(objeto.datos)
        return True


class AlmacenBucket:
    """Bucket de Cloud Storage del proyecto de pruebas. Guarda el sha256 en los metadatos del objeto."""

    def __init__(self, nombre: str):
        from google.cloud import storage  # dependencia opcional: solo para quien siembra la nube

        self._bucket = storage.Client().bucket(nombre)

    def asegurar(self, objeto) -> bool:
        huella = hashlib.sha256(objeto.datos).hexdigest()
        blob = self._bucket.get_blob(objeto.clave)
        if blob is not None and (blob.metadata or {}).get("sha256") == huella:
            return False
        blob = self._bucket.blob(objeto.clave)
        blob.metadata = {"sha256": huella, "sintetico": "ep-03"}
        blob.upload_from_string(objeto.datos, content_type=objeto.tipo)
        return True


def objetos_sinteticos() -> list:
    lista = []
    for org in organizaciones.ORGANIZACIONES:
        lista += evidencias.evidencias_de(org.id, org.nombre_comercial)
        lista += clips.clips_de(org.id)
    return lista


async def sembrar(session, cuentas, almacen) -> dict[str, dict[str, int]]:
    """Corre la siembra completa y devuelve, por clase, cuántos se crearon y cuántos ya existían."""
    resumen: dict[str, Counter] = {}

    def conteo(clase: str, creado: bool) -> None:
        resumen.setdefault(clase, Counter())["creados" if creado else "existentes"] += 1

    await organizaciones.sembrar_organizaciones(session, cuentas, conteo)
    for objeto in objetos_sinteticos():
        conteo("objetos", almacen.asegurar(objeto))
    # === EP-10 ===
    # === fin EP-10 ===
    return {k: {"creados": v["creados"], "existentes": v["existentes"]} for k, v in resumen.items()}


def formatear(resumen: dict[str, dict[str, int]]) -> str:
    return "\n".join(
        f"{clase}: {datos['creados']} creados, {datos['existentes']} ya existían"
        for clase, datos in sorted(resumen.items())
    )


async def _principal(args) -> int:
    url = os.environ.get("MIGRATION_DATABASE_URL")
    validar_destino(url, args.bucket)
    testers = Path(args.testers)
    if ruta_en_repositorio(testers):
        raise GuardiaError("El archivo de quienes prueban está rastreado por git; debe quedar fuera del repositorio.")
    cuentas = organizaciones.leer_cuentas(testers.read_text(encoding="utf-8")) if testers.exists() else []
    almacen = AlmacenBucket(args.bucket) if args.bucket else AlmacenLocal(Path(args.carpeta))
    # Una sola fuente de sesión (INV_LOPDP_SESSION_SINGLE_SOURCE): app_core.db.session lee DATABASE_URL al
    # importarse, así que se fija antes con la base ya validada por la guardia.
    os.environ["DATABASE_URL"] = url
    from app_core.db import session as sesion_bd

    try:
        async with sesion_bd.async_session_factory() as session:
            resumen = await sembrar(session, cuentas, almacen)
    finally:
        await sesion_bd.engine.dispose()
    print(formatear(resumen))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Siembra idempotente del entorno de pruebas (EP-03).")
    parser.add_argument("--testers", default=str(TESTERS_POR_DEFECTO),
                        help="Archivo local con correo,rol,organización por línea.")
    parser.add_argument("--bucket", default=None, help="Bucket de Cloud Storage del proyecto de pruebas.")
    parser.add_argument("--carpeta", default=str(Path("herramientas") / "siembra-local"),
                        help="Carpeta local de destino cuando no se indica bucket.")
    args = parser.parse_args(argv)
    if sys.platform == "win32":  # psycopg asíncrono no corre sobre el bucle Proactor de Windows
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        return asyncio.run(_principal(args))
    except (GuardiaError, ValueError) as error:
        print(f"Siembra detenida: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
