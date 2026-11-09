# ¤demo ¤seguridad-tenant
"""Siembra idempotente de la plantilla «Cooperativa Demo» (DEMO-03, PRD EVYDENTIA §5.6.1.4).

Lee `data/demo/cooperativa_demo.json` y asegura, sin duplicar:
  - el tenant plantilla con `es_demo = true`;
  - sus unidades, por `organizacion_service.crear_area_estructura`;
  - cinco personas ficticias `.invalid`, cada una con un solo rol, por `organizacion_service.grant_role`.
    El DPO no tiene rol operativo: segregación de funciones (trigger `fn_utr_dpo_sod`);
  - `ia_tope_organizacion.tope = 5` (decisión del propietario, PRD §5.6.7; tabla de SEC-13a).

Reutiliza los aseguradores de personas, áreas y roles de EP-03 (`scripts/datos_sinteticos`). Como
allí, `tenants`, `users` e `ia_tope_organizacion` se escriben con inserciones condicionadas, porque
sus salas no exponen un alta idempotente. Los datos de ciclo del JSON (diagnóstico, hallazgos y
tareas, Biblioteca y evidencias) quedan declarados y no se siembran hasta que cada sala exponga su alta.

    $env:APP_ENV = "demo"
    python scripts/demo/sembrar_plantilla.py

Se niega a correr fuera de `APP_ENV=demo` y contra la base de producción. No imprime ni la URL ni los
correos. Salida: 0 bien; 2 rechazado.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

PLANTILLA = RAIZ / "data" / "demo" / "cooperativa_demo.json"
# Id de la plantilla. Lo fija este script hasta que el contrato de features/demo/domain lo publique.
TENANT_PLANTILLA_ID = "demo-plantilla-cooperativa"


class SiembraRechazada(RuntimeError):
    pass


def cargar_plantilla(ruta: Path = PLANTILLA) -> dict:
    return json.loads(ruta.read_text(encoding="utf-8"))


def validar_destino(url: str | None) -> None:
    from app_core.entorno.guardias import ErrorArranqueEntorno, entorno_actual
    from app_core.huellas_produccion import apunta_a_produccion

    try:
        entorno = entorno_actual()
    except ErrorArranqueEntorno as error:
        raise SiembraRechazada(str(error)) from None
    if entorno != "demo":
        raise SiembraRechazada(f"la plantilla solo se siembra con APP_ENV=demo (está en {entorno}).")
    if not url:
        raise SiembraRechazada("falta MIGRATION_DATABASE_URL.")
    if apunta_a_produccion(url):
        raise SiembraRechazada("la base es la de producción.")
    huella = os.environ.get("HUELLA_PROYECTO_PRODUCCION", "").strip().lower()
    if huella and huella in url.lower():
        raise SiembraRechazada("la base contiene la huella del proyecto de producción.")


async def _asegurar_tenant(session, t: dict, conteo) -> None:
    from sqlalchemy import text

    fila = await session.execute(
        text(
            "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, sector, tamano, activo, es_demo) "
            "VALUES (:id, :n, :r, :ruc, :sec, :tam, TRUE, TRUE) ON CONFLICT (id) DO NOTHING RETURNING id"
        ),
        {"id": t["id"], "n": t["nombre_comercial"], "r": t["razon_social"], "ruc": t["ruc"],
         "sec": t["sector"], "tam": t["tamano"]},
    )
    conteo("organizacion", fila.first() is not None)


async def _asegurar_tope(session, tenant_id: str, tope: int, conteo) -> None:
    from sqlalchemy import text

    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant_id})
    actual = (await session.execute(
        text("SELECT tope FROM ia_tope_organizacion WHERE tenant_id = :t"), {"t": tenant_id})).first()
    if actual is not None and actual[0] == tope:
        conteo("tope_ia", False)
        return
    await session.execute(
        text("INSERT INTO ia_tope_organizacion (tenant_id, tope) VALUES (:t, :tope) "
             "ON CONFLICT (tenant_id) DO UPDATE SET tope = EXCLUDED.tope"),
        {"t": tenant_id, "tope": tope},
    )
    conteo("tope_ia", True)


async def sembrar(session, plantilla: dict | None = None) -> dict[str, dict[str, int]]:
    """Siembra la plantilla y devuelve, por clase, cuántos se crearon y cuántos ya existían."""
    from features.organizacion import organizacion_service as org_srv
    from scripts.datos_sinteticos import organizaciones as ep03

    plantilla = plantilla or cargar_plantilla()
    resumen: dict[str, Counter] = {}

    def conteo(clase: str, creado: bool) -> None:
        clase = {"personas": "personas", "areas": "unidades", "roles": "roles"}.get(clase, clase)
        resumen.setdefault(clase, Counter())["creados" if creado else "existentes"] += 1

    tenant = plantilla["tenant"]
    if tenant["id"] != TENANT_PLANTILLA_ID:
        raise SiembraRechazada("el id del JSON no coincide con TENANT_PLANTILLA_ID.")
    tid = TENANT_PLANTILLA_ID
    await _asegurar_tenant(session, tenant, conteo)
    personas = plantilla["personas"]
    uids = {}
    for p in personas:
        uids[p["correo"]] = await ep03._asegurar_usuario(session, p["correo"], p["nombre"], conteo)
    admin_uid = uids[next(p["correo"] for p in personas if p["rol"] == "admin_organizacion")]
    await ep03._asegurar_rol(session, tid, admin_uid, "admin_organizacion", None, admin_uid, conteo)

    areas: dict[str, str] = {}
    for u in plantilla["unidades"]:
        areas[u["codigo"]] = await ep03._asegurar_area(
            session, tid, u["codigo"], u["nombre"], org_srv.NivelArea(u["nivel"]),
            areas.get(u["padre"]) if u["padre"] else None, admin_uid, conteo)

    for p in personas:
        if p["rol"] == "admin_organizacion":
            continue
        area = areas[p["unidad"]] if p.get("unidad") else None
        await ep03._asegurar_rol(session, tid, uids[p["correo"]], p["rol"], area, admin_uid, conteo)

    await _asegurar_tope(session, tid, int(plantilla["ia_tope_organizacion"]["tope"]), conteo)
    await session.commit()
    return {k: {"creados": v["creados"], "existentes": v["existentes"]} for k, v in resumen.items()}


def formatear(resumen: dict) -> str:
    lineas = []
    for clase, datos in sorted(resumen.items()):
        lineas.append(f"{clase}: {datos['creados']} creados, {datos['existentes']} ya existían")
    return "\n".join(lineas)


async def _principal() -> int:
    url = os.environ.get("MIGRATION_DATABASE_URL")
    validar_destino(url)
    os.environ["DATABASE_URL"] = url  # una sola fuente de sesión: app_core.db.session la lee al importarse
    from app_core.db import session as sesion_bd

    try:
        async with sesion_bd.async_session_factory() as session:
            resumen = await sembrar(session)
    finally:
        await sesion_bd.engine.dispose()
    print(formatear(resumen))
    return 0


def main() -> int:
    try:
        validar_destino(os.environ.get("MIGRATION_DATABASE_URL"))
    except SiembraRechazada as error:
        print(f"Siembra rechazada: {error}", file=sys.stderr)
        return 2
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    return asyncio.run(_principal())


if __name__ == "__main__":
    raise SystemExit(main())
