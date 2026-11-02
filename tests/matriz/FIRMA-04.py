# -*- coding: utf-8 -*-
"""FIRMA-05 · Matriz de aceptación de FIRMA-04: router /api/v1/firma y webhook HMAC (11 casos, F04-01..F04-11).

Se ejecuta por ruta (`pytest tests/matriz/FIRMA-04.py -v`) con HTTP real sobre la app y la base de
TEST_DATABASE_URL (rama Neon de pruebas de la persona, nunca producción): sin dobles de BD. Cada caso
crea organizaciones con UUID únicos, no depende del orden y limpia lo que crea. El secreto del webhook
se genera por ejecución y se inyecta con `monkeypatch.setenv`; no hay ningún secreto en el código.

Contrato real de FIRMA-04: rutas bajo `/api/v1/firma` (`/sesiones`, `/sesiones/{firma_id}`, `/webhook`);
la organización sale de la identidad (`X-Tenant-ID` en modo `headers`); el listado responde
`{"sesiones": [...]}`; una firma inválida o ausente responde 401 con `{"detail": "firma_invalida"}`.

`FILAS` va vacía: estos endpoints resuelven la organización, no un rol (`test_matriz_permisos.py`
exige la lista en cada archivo de esta carpeta).
"""
# ¤¤qa-engineer
# ¤firma-electronica ¤arbitro
import hashlib
import hmac as hmac_stdlib
import json
import os
import secrets
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

FILAS: list[tuple[str, str, str, set[str]]] = []

pytestmark = pytest.mark.asyncio

RUTA = "/api/v1/firma"
SHA = "a" * 64
SHA_FIRMADO = "b" * 64


@pytest_asyncio.fixture
async def entorno(db_engine, monkeypatch):
    """Cliente HTTP sobre la app real, dos organizaciones UUID y el secreto del webhook inyectado."""
    from app_core.db import session as sesion_app
    from main import app

    url = os.environ.get("TEST_DATABASE_URL", "")
    assert url and "ep-late-hall" not in url, "Se requiere la rama de pruebas de la persona, nunca producción"
    secreto = secrets.token_hex(16)
    monkeypatch.setenv("FIRMA_WEBHOOK_SECRET", secreto)
    # Otros módulos dejan overrides de sesión puestos; aquí se recorre la base real, así que se quitan
    # mientras dura el caso y se restauran al salir.
    ausente = object()
    previos = {
        dep: app.dependency_overrides.pop(dep, ausente)
        for dep in (sesion_app.get_session, sesion_app.get_tenant_session)
    }
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    ta, tb = str(uuid4()), str(uuid4())
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
            yield {"cliente": cliente, "a": ta, "b": tb, "secreto": secreto}
    finally:
        for dep, previo in previos.items():
            if previo is not ausente:
                app.dependency_overrides[dep] = previo
        # El engine global se enlaza al bucle del caso: se descarta para el siguiente.
        await sesion_app.engine.dispose()
        async with factory() as s:
            for tenant in (ta, tb):
                await sesion_app.fijar_contexto_rls(s, tenant)
                await s.execute(text("DELETE FROM audit_events WHERE tenant_id = :t"), {"t": tenant})
                await s.execute(
                    text("DELETE FROM firma_sessions WHERE tenant_id = CAST(:t AS uuid)"), {"t": tenant}
                )
                await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": tenant})
            await s.commit()


def _h(tenant: str) -> dict[str, str]:
    return {"X-Tenant-ID": tenant}


def _solicitud(**cambios) -> dict:
    return {
        "documento_id": f"doc-{uuid4().hex[:8]}", "firmante_id": "firmante-1", "formato": "pdf",
        "proveedor": "anf", "sha256_original": SHA, **cambios,
    }


async def _crear(env, tenant: str, **cambios) -> dict:
    r = await env["cliente"].post(f"{RUTA}/sesiones", json=_solicitud(**cambios), headers=_h(tenant))
    assert r.status_code == 201, r.text
    return r.json()


async def _obtener(env, tenant: str, firma_id: str) -> dict:
    r = await env["cliente"].get(f"{RUTA}/sesiones/{firma_id}", headers=_h(tenant))
    assert r.status_code == 200, r.text
    return r.json()


def _aviso(firma_id: str, tenant: str) -> bytes:
    return json.dumps(
        {
            "firma_id": firma_id, "tenant_id": tenant, "sha256_firmado": SHA_FIRMADO,
            "timestamp_tsa": datetime.now(timezone.utc).isoformat(),
            "certificado_json": {"numero_serie": "SERIE-F05"},
        },
        separators=(",", ":"),
    ).encode("utf-8")


def _hmac(cuerpo: bytes, secreto: str) -> str:
    """Oráculo independiente del código bajo prueba: HMAC-SHA256 con la biblioteca estándar."""
    return hmac_stdlib.new(secreto.encode("utf-8"), cuerpo, hashlib.sha256).hexdigest()


async def _enviar_webhook(env, sesion: dict, tenant: str):
    cuerpo = _aviso(sesion["firma_id"], tenant)
    return await env["cliente"].post(
        f"{RUTA}/webhook", content=cuerpo, headers={"X-Signature": f"sha256={_hmac(cuerpo, env['secreto'])}"}
    )


async def test_post_sesiones_crea_ok(entorno):
    """F04-01 · POST /sesiones → 201, el cuerpo trae firma_id (UUID) y la sesión nace en borrador."""
    r = await entorno["cliente"].post(f"{RUTA}/sesiones", json=_solicitud(), headers=_h(entorno["a"]))
    assert r.status_code == 201, r.text
    cuerpo = r.json()
    assert str(UUID(cuerpo["firma_id"])) == cuerpo["firma_id"]
    assert cuerpo["estado"] == "borrador" and cuerpo["sha256_original"] == SHA
    assert cuerpo["sha256_firmado"] is None and cuerpo["timestamp_tsa"] is None


async def test_post_sesiones_campos_invalidos(entorno):
    """F04-02 · Payload incompleto o con valores fuera de contrato → 422, y no se escribe nada."""
    malos = [
        {},
        {"documento_id": "doc-1"},
        {k: v for k, v in _solicitud().items() if k != "sha256_original"},
        _solicitud(sha256_original="abc"),
        _solicitud(formato="docx"),
        _solicitud(proveedor="inventado"),
        _solicitud(documento_id=""),
    ]
    for malo in malos:
        r = await entorno["cliente"].post(f"{RUTA}/sesiones", json=malo, headers=_h(entorno["a"]))
        assert r.status_code == 422, malo
    listado = await entorno["cliente"].get(f"{RUTA}/sesiones", headers=_h(entorno["a"]))
    assert listado.json() == {"sesiones": []}


async def test_get_sesion_ok(entorno):
    """F04-03 · GET /sesiones/{firma_id} → 200, estado borrador y los datos del alta."""
    creada = await _crear(entorno, entorno["a"], documento_id="doc-f03", firmante_id="firmante-9")
    leida = await _obtener(entorno, entorno["a"], creada["firma_id"])
    assert leida["estado"] == "borrador"
    assert (leida["documento_id"], leida["firmante_id"]) == ("doc-f03", "firmante-9")
    assert leida == creada


async def test_get_sesion_otro_tenant_404(entorno):
    """F04-04 · La organización B consulta la sesión de A → 404."""
    creada = await _crear(entorno, entorno["a"])
    r = await entorno["cliente"].get(f"{RUTA}/sesiones/{creada['firma_id']}", headers=_h(entorno["b"]))
    assert r.status_code == 404
    assert (await _obtener(entorno, entorno["a"], creada["firma_id"]))["firma_id"] == creada["firma_id"]


async def test_get_sesion_inexistente_404(entorno):
    """F04-05 · Un UUID aleatorio → 404; un id que no es UUID → 422, nunca 500."""
    r = await entorno["cliente"].get(f"{RUTA}/sesiones/{uuid4()}", headers=_h(entorno["a"]))
    assert r.status_code == 404
    r = await entorno["cliente"].get(f"{RUTA}/sesiones/no-es-uuid", headers=_h(entorno["a"]))
    assert r.status_code == 422


async def test_get_sesiones_lista_vacia(entorno):
    """F04-06 · Una organización sin sesiones → 200 con lista vacía, aunque la otra tenga."""
    await _crear(entorno, entorno["a"])
    r = await entorno["cliente"].get(f"{RUTA}/sesiones", headers=_h(entorno["b"]))
    assert r.status_code == 200 and r.json() == {"sesiones": []}


async def test_get_sesiones_filtro_estado(entorno):
    """F04-07 · 2 firmadas + 1 borrador → ?estado=firmado devuelve 2; ?estado=borrador, 1; inválido, 422."""
    creadas = [await _crear(entorno, entorno["a"]) for _ in range(3)]
    for sesion in creadas[:2]:
        assert (await _enviar_webhook(entorno, sesion, entorno["a"])).status_code == 200
    firmadas = await entorno["cliente"].get(f"{RUTA}/sesiones?estado=firmado", headers=_h(entorno["a"]))
    borradores = await entorno["cliente"].get(f"{RUTA}/sesiones?estado=borrador", headers=_h(entorno["a"]))
    assert {s["firma_id"] for s in firmadas.json()["sesiones"]} == {c["firma_id"] for c in creadas[:2]}
    assert [s["firma_id"] for s in borradores.json()["sesiones"]] == [creadas[2]["firma_id"]]
    invalido = await entorno["cliente"].get(f"{RUTA}/sesiones?estado=inventado", headers=_h(entorno["a"]))
    assert invalido.status_code == 422


async def test_webhook_hmac_valido_200(entorno):
    """F04-08 · Cuerpo + X-Signature: sha256=<correcto> → 200 (y también la firma sin prefijo)."""
    creada = await _crear(entorno, entorno["a"])
    r = await _enviar_webhook(entorno, creada, entorno["a"])
    assert r.status_code == 200, r.text
    assert r.json() == {"firma_id": creada["firma_id"], "estado": "firmado"}
    otra = await _crear(entorno, entorno["a"])
    cuerpo = _aviso(otra["firma_id"], entorno["a"])
    sin_prefijo = await entorno["cliente"].post(
        f"{RUTA}/webhook", content=cuerpo, headers={"X-Signature": _hmac(cuerpo, entorno["secreto"])}
    )
    assert sin_prefijo.status_code == 200, sin_prefijo.text


async def test_webhook_hmac_invalido_401(entorno, monkeypatch):
    """F04-09 · Firma incorrecta (o secreto sin configurar) → 401 {"detail": "firma_invalida"}, sin efecto."""
    creada = await _crear(entorno, entorno["a"])
    cuerpo = _aviso(creada["firma_id"], entorno["a"])
    alterado = cuerpo.replace(SHA_FIRMADO.encode(), ("c" * 64).encode())
    for cabecera in (
        f"sha256={_hmac(cuerpo, 'otro-secreto')}",
        "0" * 64,
        "sha256=",
        _hmac(alterado, entorno["secreto"]),  # firma válida de OTRO cuerpo
    ):
        r = await entorno["cliente"].post(f"{RUTA}/webhook", content=cuerpo, headers={"X-Signature": cabecera})
        assert r.status_code == 401 and r.json() == {"detail": "firma_invalida"}, cabecera
    # Falla cerrada: sin secreto configurado ni la firma «correcta» con clave vacía sirve.
    monkeypatch.delenv("FIRMA_WEBHOOK_SECRET")
    r = await entorno["cliente"].post(f"{RUTA}/webhook", content=cuerpo, headers={"X-Signature": _hmac(cuerpo, "")})
    assert r.status_code == 401 and r.json() == {"detail": "firma_invalida"}
    assert (await _obtener(entorno, entorno["a"], creada["firma_id"]))["estado"] == "borrador"


async def test_webhook_hmac_ausente_401(entorno):
    """F04-10 · Sin cabecera X-Signature → 401, y la sesión no cambia."""
    creada = await _crear(entorno, entorno["a"])
    cuerpo = _aviso(creada["firma_id"], entorno["a"])
    r = await entorno["cliente"].post(f"{RUTA}/webhook", content=cuerpo)
    assert r.status_code == 401 and r.json() == {"detail": "firma_invalida"}
    vacia = await entorno["cliente"].post(f"{RUTA}/webhook", content=cuerpo, headers={"X-Signature": ""})
    assert vacia.status_code == 401
    assert (await _obtener(entorno, entorno["a"], creada["firma_id"]))["estado"] == "borrador"


async def test_webhook_actualiza_estado(entorno):
    """F04-11 · Un webhook válido deja la sesión firmada con hash, sello de tiempo y certificado."""
    creada = await _crear(entorno, entorno["a"])
    assert (await _enviar_webhook(entorno, creada, entorno["a"])).status_code == 200
    firmada = await _obtener(entorno, entorno["a"], creada["firma_id"])
    assert firmada["estado"] == "firmado" and firmada["sha256_firmado"] == SHA_FIRMADO
    assert firmada["timestamp_tsa"] and firmada["certificado_json"] == {"numero_serie": "SERIE-F05"}
    assert firmada["sha256_original"] == SHA
    # Una sesión firmada no se vuelve a firmar (409) y un aviso con el tenant equivocado no la encuentra (404).
    assert (await _enviar_webhook(entorno, creada, entorno["a"])).status_code == 409
    assert (await _enviar_webhook(entorno, creada, entorno["b"])).status_code == 404
