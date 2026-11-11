# ¤rbac-tenant
# ¤arbitro
"""Árbitro de ORG-18: sedes de la organización y clientes cuando actúa como encargada.

Valida (contrato: governance/especificaciones/ORG-18.md):
1. Solo una sede principal vigente (409 SEDE_PRINCIPAL_DUPLICADA); retirarla libera el lugar.
2. Los clientes solo existen si `rol_datos` es encargado o ambos (409 NO_ES_ENCARGADA).
3. El contrato se referencia por huella existente en Evidencias (422 CONTRATO_NO_ENCONTRADO).
4. Una organización no ve ni toca lo de otra (HTTP y RLS como lopdp_app); el dpo lee y no escribe.
5. La auditoría y las respuestas de error no llevan datos de contacto.

Las pruebas de integración necesitan TEST_DATABASE_URL (PostgreSQL 16 local, 127.0.0.1) y se omiten sin
ella. Datos ficticios: correos con el dominio reservado .invalid.

Mutación documentada: en `sedes_engine._exigir_principal_libre`, hacer que no lance el error (y quitar el
índice único parcial) deja marcar dos sedes principales y `test_sede_principal_unica` falla.
"""
from __future__ import annotations

import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app_core.db.session import get_session
from features.organizacion.organizacion_service import ClienteEntrada, SedeEntrada
from app_core.pasillo import evidencias as pasillo_evidencias
from main import app

RUTA = "/api/v1/organizacion"
HUELLA = "a" * 64
SEDE = {"nombre": "Matriz ficticia", "direccion": "Calle Ficticia 123", "ciudad": "Ciudad", "provincia": "Provincia"}
CLIENTE = {"razon_social": "Cliente Ficticio S.A.", "ruc": "1790000000001"}


# ---------------------------------------------------------------- validación pura (sin BD)

def test_sede_y_cliente_no_admiten_organizacion_ni_campos_ajenos():
    SedeEntrada.model_validate(SEDE)
    for campo in ("tenant_id", "creado_por", "retirada_en"):
        with pytest.raises(ValidationError):
            SedeEntrada.model_validate({**SEDE, campo: "x"})
    with pytest.raises(ValidationError):
        ClienteEntrada.model_validate({**CLIENTE, "tenant_id": "t"})


@pytest.mark.parametrize("ruc", ["123", "17900000000012", "17900000000a1", ""])
def test_ruc_del_cliente_debe_tener_trece_digitos(ruc):
    with pytest.raises(ValidationError):
        ClienteEntrada.model_validate({**CLIENTE, "ruc": ruc})


# ------------------------------------------------------------------------------- integración

def _async_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Sin TEST_DATABASE_URL: la parte de BD de ORG-18 queda no verificada")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@pytest_asyncio.fixture
async def factory():
    engine = create_async_engine(_async_url(), pool_pre_ping=True)
    yield async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    await engine.dispose()


@pytest_asyncio.fixture
async def dos_organizaciones(factory):
    """A (encargada; admin, coordinador, dpo) y B (responsable; su admin)."""
    async def _sesion_de_prueba():
        async with factory() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    guardado = dict(app.dependency_overrides)
    app.dependency_overrides[get_session] = _sesion_de_prueba

    sufijo = uuid.uuid4().hex[:8]
    ta, tb = f"t18a-{sufijo}", f"t18b-{sufijo}"
    u = {n: f"u18{n}-{sufijo}" for n in ("admin", "coord", "dpo", "badmin")}
    roles = (
        (u["admin"], ta, "admin_organizacion"), (u["coord"], ta, "coordinador"), (u["dpo"], ta, "dpo"),
        (u["badmin"], tb, "admin_organizacion"),
    )
    async with factory() as s:
        for tid, rol_datos in ((ta, "encargado"), (tb, "responsable")):
            await s.execute(
                text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, rol_datos) "
                     "VALUES (:id, :nom, :razon, :ruc, :rol)"),
                {"id": tid, "nom": f"Org {tid}", "razon": f"Org Ficticia {tid} S.A.", "ruc": f"RUC{tid[:10]}", "rol": rol_datos},
            )
        for uid in u.values():
            await s.execute(
                text("INSERT INTO users (id, email, nombre) VALUES (:id, :email, :nombre)"),
                {"id": uid, "email": f"{uid}@organizacion.invalid", "nombre": f"Usuario ficticio {uid}"},
            )
        for uid, tid, rol in roles:
            await s.execute(
                text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, :r)"),
                {"id": f"r18-{uuid.uuid4().hex[:8]}", "u": uid, "t": tid, "r": rol},
            )
        await s.commit()

    yield {"ta": ta, "tb": tb, **u}

    ids = {"a": ta, "b": tb}
    async with factory() as s:
        await s.execute(text("DELETE FROM clientes_encargo WHERE tenant_id IN (:a, :b)"), ids)
        await s.execute(text("DELETE FROM sedes WHERE tenant_id IN (:a, :b)"), ids)
        await s.execute(text("DELETE FROM audit_events WHERE tenant_id IN (:a, :b)"), ids)
        await s.execute(text("DELETE FROM user_tenant_roles WHERE tenant_id IN (:a, :b)"), ids)
        await s.execute(text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": list(u.values())})
        await s.execute(text("DELETE FROM tenants WHERE id IN (:a, :b)"), ids)
        await s.commit()

    app.dependency_overrides.clear()
    app.dependency_overrides.update(guardado)


def _cab(tenant: str, usuario: str, rol: str) -> dict[str, str]:
    return {"X-Tenant-ID": tenant, "X-User-ID": usuario, "X-Role": rol}


def _cli() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _codigo(respuesta) -> str | None:
    cuerpo = respuesta.json()
    return cuerpo.get("code") or (cuerpo.get("detail") or {}).get("code") if isinstance(cuerpo, dict) else None


@pytest.mark.asyncio
async def test_sede_principal_unica(dos_organizaciones):
    o = dos_organizaciones
    cab = _cab(o["ta"], o["admin"], "admin_organizacion")
    async with _cli() as c:
        primera = await c.post(f"{RUTA}/sedes", json={**SEDE, "es_principal": True}, headers=cab)
        assert primera.status_code == 201
        otra = await c.post(f"{RUTA}/sedes", json={**SEDE, "nombre": "Sucursal", "es_principal": True}, headers=cab)
        assert otra.status_code == 409 and _codigo(otra) == "SEDE_PRINCIPAL_DUPLICADA"
        secundaria = (await c.post(f"{RUTA}/sedes", json={**SEDE, "nombre": "Sucursal"}, headers=cab)).json()["id"]
        marcada = await c.put(f"{RUTA}/sedes/{secundaria}", json={**SEDE, "nombre": "Sucursal", "es_principal": True}, headers=cab)
        assert marcada.status_code == 409
        # Retirar la principal libera el lugar.
        assert (await c.post(f"{RUTA}/sedes/{primera.json()['id']}/retirar", headers=cab)).status_code == 200
        assert (await c.put(f"{RUTA}/sedes/{secundaria}", json={**SEDE, "nombre": "Sucursal", "es_principal": True}, headers=cab)).status_code == 200
        lista = (await c.get(f"{RUTA}/sedes", headers=cab)).json()
        assert [s["es_principal"] for s in lista if s["retirada_en"] is None] == [True]


@pytest.mark.asyncio
async def test_clientes_solo_encargada(dos_organizaciones):
    o = dos_organizaciones
    async with _cli() as c:
        cab_b = _cab(o["tb"], o["badmin"], "admin_organizacion")
        for respuesta in (await c.post(f"{RUTA}/clientes", json=CLIENTE, headers=cab_b), await c.get(f"{RUTA}/clientes", headers=cab_b)):
            assert respuesta.status_code == 409 and _codigo(respuesta) == "NO_ES_ENCARGADA"
        cab_a = _cab(o["ta"], o["admin"], "admin_organizacion")
        creado = await c.post(f"{RUTA}/clientes", json=CLIENTE, headers=cab_a)
        assert creado.status_code == 201
        assert (await c.post(f"{RUTA}/clientes", json=CLIENTE, headers=cab_a)).status_code == 409
        assert [x["razon_social"] for x in (await c.get(f"{RUTA}/clientes", headers=cab_a)).json()] == ["Cliente Ficticio S.A."]
        assert (await c.post(f"{RUTA}/clientes/{creado.json()['id']}/retirar", headers=cab_a)).status_code == 200
        assert (await c.post(f"{RUTA}/clientes", json=CLIENTE, headers=cab_a)).status_code == 201


@pytest.mark.asyncio
async def test_contrato_debe_existir_en_evidencias(dos_organizaciones, monkeypatch):
    o = dos_organizaciones
    cab = _cab(o["ta"], o["admin"], "admin_organizacion")
    monkeypatch.setattr(pasillo_evidencias, "huella_registrada", lambda tenant, sha: HUELLA if sha == HUELLA else None)
    async with _cli() as c:
        malo = await c.post(f"{RUTA}/clientes", json={**CLIENTE, "contrato_sha256": "b" * 64}, headers=cab)
        assert malo.status_code == 422 and _codigo(malo) == "CONTRATO_NO_ENCONTRADO"
        bueno = await c.post(f"{RUTA}/clientes", json={**CLIENTE, "contrato_sha256": HUELLA, "vigente_hasta": "2030-01-31"}, headers=cab)
        assert bueno.status_code == 201
        fila = (await c.get(f"{RUTA}/clientes", headers=cab)).json()[0]
        assert fila["contrato_sha256"] == HUELLA and fila["vigente_hasta"] == "2030-01-31"


@pytest.mark.asyncio
async def test_dpo_lee_pero_no_escribe_y_otra_organizacion_no_ve(dos_organizaciones):
    o = dos_organizaciones
    cab = _cab(o["ta"], o["admin"], "admin_organizacion")
    cab_dpo = _cab(o["ta"], o["dpo"], "dpo")
    async with _cli() as c:
        sede = (await c.post(f"{RUTA}/sedes", json=SEDE, headers=cab)).json()["id"]
        assert [s["id"] for s in (await c.get(f"{RUTA}/sedes", headers=cab_dpo)).json()] == [sede]
        assert (await c.post(f"{RUTA}/sedes", json=SEDE, headers=cab_dpo)).status_code == 403
        assert (await c.post(f"{RUTA}/clientes", json=CLIENTE, headers=cab_dpo)).status_code == 403
        cab_b = _cab(o["tb"], o["badmin"], "admin_organizacion")
        assert (await c.get(f"{RUTA}/sedes", headers=cab_b)).json() == []
        assert (await c.put(f"{RUTA}/sedes/{sede}", json=SEDE, headers=cab_b)).status_code == 404
        assert (await c.post(f"{RUTA}/sedes/{sede}/retirar", headers=cab_b)).status_code == 404


@pytest.mark.asyncio
async def test_auditoria_sin_datos_de_contacto(dos_organizaciones, factory):
    o = dos_organizaciones
    cab = _cab(o["ta"], o["admin"], "admin_organizacion")
    contacto = "dpo@contacto-ficticio.invalid"
    async with _cli() as c:
        r = await c.post(f"{RUTA}/sedes", json={**SEDE, "contacto_spdp": contacto, "contacto_titulares": contacto}, headers=cab)
        assert r.status_code == 201
    async with factory() as s:
        eventos = (await s.execute(
            text("SELECT CAST(payload AS text) FROM audit_events WHERE tenant_id = :t"), {"t": o["ta"]},
        )).scalars().all()
    assert eventos and all(contacto not in (e or "") for e in eventos)


@pytest.mark.asyncio
async def test_rls_sedes(dos_organizaciones, factory):
    o = dos_organizaciones
    async with factory() as s:
        for tabla, permiso, esperado in (
            ("sedes", "SELECT", True), ("sedes", "INSERT", True), ("sedes", "UPDATE", True), ("sedes", "DELETE", False),
            ("clientes_encargo", "UPDATE", True), ("clientes_encargo", "DELETE", False),
        ):
            r = (await s.execute(text("SELECT has_table_privilege('lopdp_app', :t, :p)"), {"t": tabla, "p": permiso})).scalar()
            assert r is esperado, (tabla, permiso)
        forzadas = (await s.execute(text(
            "SELECT count(*) FROM pg_class WHERE relname IN ('sedes', 'clientes_encargo') "
            "AND relrowsecurity AND relforcerowsecurity"
        ))).scalar()
        assert forzadas == 2
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": o["ta"]})
        await s.execute(
            text("INSERT INTO sedes (id, tenant_id, nombre, direccion, ciudad, provincia, creado_por) "
                 "VALUES (:id, :t, 'De A', 'Calle', 'Ciudad', 'Provincia', 'u')"),
            {"id": str(uuid.uuid4()), "t": o["ta"]},
        )
        await s.execute(
            text("INSERT INTO clientes_encargo (id, tenant_id, razon_social, ruc, creado_por) VALUES (:id, :t, 'De A', '1790000000001', 'u')"),
            {"id": str(uuid.uuid4()), "t": o["ta"]},
        )
        with pytest.raises(Exception):  # WITH CHECK: no se escribe en otra organización
            async with s.begin_nested():
                await s.execute(
                    text("INSERT INTO sedes (id, tenant_id, nombre, direccion, ciudad, provincia, creado_por) "
                         "VALUES (:id, :t, 'Ajena', 'Calle', 'Ciudad', 'Provincia', 'u')"),
                    {"id": str(uuid.uuid4()), "t": o["tb"]},
                )
        await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": o["tb"]})
        assert (await s.execute(text("SELECT count(*) FROM sedes"))).scalar() == 0
        assert (await s.execute(text("SELECT count(*) FROM clientes_encargo"))).scalar() == 0
        await s.rollback()
