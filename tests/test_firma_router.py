# -*- coding: utf-8 -*-
"""Árbitro FIRMA-04: API HTTP de firma electrónica contra TEST_DATABASE_URL (nunca producción).

Sin mocks de base de datos: cada prueba recorre el router, la compuerta y `firma_sessions` reales.
El aislamiento entre organizaciones se prueba con dos tenants distintos.

Prueba de mutación documentada: en api/routers/firma_electronica.py se sustituyó
`hmac.compare_digest(a, b)` por `a == b` en `_verificar_hmac`. Los resultados HTTP no cambian, pero
`test_webhook_hmac_invalido` (que espía compare_digest) pasó a FAILED; se restauró la función.
"""
# ¤¤qa-engineer
# ¤firma-electronica
import hashlib
import hmac as hmac_stdlib
import json
import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

pytestmark = pytest.mark.asyncio

RUTA = "/api/v1/firma"
SECRETO = "secreto-firma-04-solo-pruebas"
SHA = "a" * 64


@pytest_asyncio.fixture
async def entorno(db_engine, monkeypatch):
    from app_core.db.session import fijar_contexto_rls
    from main import app

    url = os.environ.get("TEST_DATABASE_URL", "")
    assert url and "ep-late-hall-b50bpbk5" not in url, "Se requiere una rama de pruebas, nunca producción"
    monkeypatch.setenv("FIRMA_WEBHOOK_SECRET", SECRETO)

    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    ta, tb = (str(uuid4()) for _ in range(2))
    try:
        async with factory() as s:
            for tenant in (ta, tb):
                await s.execute(
                    text(
                        "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                        "VALUES (:t, :t, :t, :t)"
                    ),
                    {"t": tenant},
                )
            await s.commit()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as cliente:
            yield {"cliente": cliente, "a": ta, "b": tb}
    finally:
        async with factory() as s:
            for tenant in (ta, tb):
                await fijar_contexto_rls(s, tenant)
                await s.execute(text("DELETE FROM audit_events WHERE tenant_id = :t"), {"t": tenant})
                await s.execute(text("DELETE FROM firma_sessions WHERE tenant_id = :t"), {"t": tenant})
                await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": tenant})
            await s.commit()


def _h(tenant: str) -> dict[str, str]:
    return {"X-Tenant-ID": tenant}


def _solicitud(**cambios) -> dict:
    return {
        "documento_id": f"doc-{uuid4().hex[:8]}", "firmante_id": "firmante-1", "formato": "pdf",
        "proveedor": "anf", "sha256_original": SHA,
        **cambios,
    }


async def _crear(entorno, tenant: str, **cambios) -> dict:
    r = await entorno["cliente"].post(f"{RUTA}/sesiones", json=_solicitud(**cambios), headers=_h(tenant))
    assert r.status_code == 201, r.text
    return r.json()


def _aviso(sesion: dict, tenant: str) -> bytes:
    return json.dumps({
        "firma_id": sesion["firma_id"], "tenant_id": tenant,
        "sha256_firmado": "b" * 64, "timestamp_tsa": datetime.now(timezone.utc).isoformat(),
        "certificado_json": {"numero_serie": "SERIE-F04"},
    }, separators=(",", ":")).encode("utf-8")


def _firmar(cuerpo: bytes, secreto: str = SECRETO) -> str:
    return hmac_stdlib.new(secreto.encode(), cuerpo, hashlib.sha256).hexdigest()


async def test_crear_sesion_ok(entorno):
    cuerpo = await _crear(entorno, entorno["a"], proveedor="universign")
    assert cuerpo["firma_id"] and cuerpo["estado"] == "borrador"
    assert cuerpo["proveedor"] == "universign" and cuerpo["formato"] == "pdf"
    # La organización sale del contexto autenticado: queda en A, no es visible desde B.
    r_b = await entorno["cliente"].get(f"{RUTA}/sesiones/{cuerpo['firma_id']}", headers=_h(entorno["b"]))
    assert r_b.status_code == 404


async def test_obtener_sesion_ok(entorno):
    creada = await _crear(entorno, entorno["a"])
    r = await entorno["cliente"].get(f"{RUTA}/sesiones/{creada['firma_id']}", headers=_h(entorno["a"]))
    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "borrador" and r.json()["documento_id"] == creada["documento_id"]


async def test_obtener_sesion_otro_tenant(entorno):
    creada = await _crear(entorno, entorno["a"])
    r = await entorno["cliente"].get(f"{RUTA}/sesiones/{creada['firma_id']}", headers=_h(entorno["b"]))
    assert r.status_code == 404
    listado_b = await entorno["cliente"].get(f"{RUTA}/sesiones", headers=_h(entorno["b"]))
    assert listado_b.json() == {"sesiones": []}


async def test_listar_sesiones_filtro_estado(entorno):
    firmada = await _crear(entorno, entorno["a"])
    pendiente = await _crear(entorno, entorno["a"])
    cuerpo = _aviso(firmada, entorno["a"])
    r = await entorno["cliente"].post(f"{RUTA}/webhook", content=cuerpo, headers={"X-Signature": _firmar(cuerpo)})
    assert r.status_code == 200, r.text

    solo_firmadas = await entorno["cliente"].get(f"{RUTA}/sesiones?estado=firmado", headers=_h(entorno["a"]))
    solo_borradores = await entorno["cliente"].get(f"{RUTA}/sesiones?estado=borrador", headers=_h(entorno["a"]))
    assert [s["firma_id"] for s in solo_firmadas.json()["sesiones"]] == [firmada["firma_id"]]
    assert [s["firma_id"] for s in solo_borradores.json()["sesiones"]] == [pendiente["firma_id"]]


async def test_webhook_hmac_valido(entorno):
    creada = await _crear(entorno, entorno["a"])
    cuerpo = _aviso(creada, entorno["a"])
    r = await entorno["cliente"].post(
        f"{RUTA}/webhook", content=cuerpo, headers={"X-Signature": f"sha256={_firmar(cuerpo)}"}
    )
    assert r.status_code == 200, r.text
    assert r.json() == {"firma_id": creada["firma_id"], "estado": "firmado"}
    firmada = (await entorno["cliente"].get(f"{RUTA}/sesiones/{creada['firma_id']}", headers=_h(entorno["a"]))).json()
    assert firmada["estado"] == "firmado" and firmada["sha256_firmado"] == "b" * 64
    assert firmada["certificado_json"] == {"numero_serie": "SERIE-F04"} and firmada["timestamp_tsa"]


async def test_webhook_hmac_invalido(entorno, monkeypatch):
    from api.routers import firma_electronica as router_firma

    llamadas = []
    real = hmac_stdlib.compare_digest

    def espia(a, b):
        llamadas.append((a, b))
        return real(a, b)

    monkeypatch.setattr(router_firma.hmac, "compare_digest", espia)
    creada = await _crear(entorno, entorno["a"])
    cuerpo = _aviso(creada, entorno["a"])
    r = await entorno["cliente"].post(f"{RUTA}/webhook", content=cuerpo, headers={"X-Signature": _firmar(cuerpo, "otro-secreto")})
    assert r.status_code == 401 and r.json() == {"detail": "firma_invalida"}
    assert len(llamadas) == 1  # la comparación pasó por compare_digest, nunca por ==
    # Sin efecto en la base: la sesión sigue en borrador.
    actual = (await entorno["cliente"].get(f"{RUTA}/sesiones/{creada['firma_id']}", headers=_h(entorno["a"]))).json()
    assert actual["estado"] == "borrador"


async def test_webhook_hmac_ausente(entorno):
    creada = await _crear(entorno, entorno["a"])
    cuerpo = _aviso(creada, entorno["a"])
    r = await entorno["cliente"].post(f"{RUTA}/webhook", content=cuerpo)
    assert r.status_code == 401 and r.json() == {"detail": "firma_invalida"}
    actual = (await entorno["cliente"].get(f"{RUTA}/sesiones/{creada['firma_id']}", headers=_h(entorno["a"]))).json()
    assert actual["estado"] == "borrador"
