"""ORG-05: un único camino para dar `responsable_area` y rastro de cada concesión directa.

- Arranque (sin implementador activo): el administrador concede `responsable_area` directo.
- Con implementador activo: la concesión directa de `responsable_area` da 409 y señala RM-10.
- Nadie se concede a sí mismo un rol operativo.
- El resto de roles se siguen concediendo directo.
- Cada concesión y revocación directa deja `role_granted` / `role_revoked` en audit_events.
- El flujo RM-10 sigue concediendo `responsable_area` aunque haya implementador.
"""
import importlib.util

import pytest

_REDIS_AVAILABLE = importlib.util.find_spec("redis") is not None
pytestmark = pytest.mark.skipif(
    not _REDIS_AVAILABLE,
    reason="redis no instalado en este entorno (arnes); usar .venv para tests completos",
)
import json
import os
import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine



def _async_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@pytest_asyncio.fixture
async def factory():
    engine = create_async_engine(_async_url(), pool_pre_ping=True)
    yield async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    await engine.dispose()


@pytest_asyncio.fixture
async def api_client(factory):
    from main import app
    from app_core.db.session import get_session

    async def _test_get_session():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = _test_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.pop(get_session, None)


@pytest_asyncio.fixture
async def org(factory):
    """Tenant mediano + admin_organizacion + un área. Limpieza de todo lo creado."""
    ta = f"org05-{uuid.uuid4().hex[:8]}"
    admin = f"org05-admin-{uuid.uuid4().hex[:8]}"
    area = f"org05-a-{uuid.uuid4().hex[:8]}"
    domain = f"{ta}.test"

    async with factory() as s:
        await s.execute(text(
            "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
            "VALUES (:id, :n, :r, :ruc, 'mediana')"
        ), {"id": ta, "n": f"Org {ta}", "r": f"Org {ta} SA", "ruc": f"RUC{uuid.uuid4().hex[:12]}"})
        await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:id, :e, 'Admin')"),
                        {"id": admin, "e": f"admin@{domain}"})
        await s.execute(text(
            "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) "
            "VALUES (:id, :u, :t, 'admin_organizacion')"
        ), {"id": f"utr-{uuid.uuid4().hex[:8]}", "u": admin, "t": ta})
        await s.execute(text("INSERT INTO areas (id, tenant_id, nombre, codigo) VALUES (:i, :t, 'Finanzas', :c)"),
                        {"i": area, "t": ta, "c": f"COD-{area[-6:]}"})
        await s.commit()

    yield {"tenant": ta, "admin": admin, "area": area, "domain": domain}

    async with factory() as s:
        for sql in (
            "DELETE FROM audit_events WHERE tenant_id = :t",
            "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
            "DELETE FROM area_responsable_requests WHERE tenant_id = :t",
            "UPDATE areas SET parent_area_id = NULL, responsable_user_id = NULL WHERE tenant_id = :t",
            "DELETE FROM areas WHERE tenant_id = :t",
        ):
            await s.execute(text(sql), {"t": ta})
        await s.execute(text("DELETE FROM users WHERE email LIKE :d"), {"d": f"%@{domain}"})
        await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": ta})
        await s.commit()


def _h(user: str, tenant: str, role: str | None = None) -> dict:
    h = {"X-User-ID": user, "X-Tenant-ID": tenant}
    if role:
        h["X-Role"] = role
    return h


def _admin(org) -> dict:
    return _h(org["admin"], org["tenant"], "admin_organizacion")


async def _new_user(client, org, nombre: str) -> str:
    r = await client.post(
        "/api/v1/organizacion/usuarios",
        json={"email": f"{nombre}@{org['domain']}", "nombre": nombre},
        headers=_admin(org),
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _grant(client, org, user_id: str, role: str, area_id: str | None = None, headers=None):
    body = {"user_id": user_id, "role": role}
    if area_id:
        body["area_id"] = area_id
    return await client.post("/api/v1/organizacion/roles", json=body, headers=headers or _admin(org))


async def _eventos(factory, tenant: str, action: str) -> list[dict]:
    async with factory() as s:
        await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant})
        filas = (await s.execute(
            text("SELECT entity_type, entity_id, user_id, payload FROM audit_events "
                 "WHERE tenant_id = :t AND action = :a"),
            {"t": tenant, "a": action},
        )).mappings().all()
    salida = []
    for f in filas:
        payload = f["payload"] if isinstance(f["payload"], dict) else json.loads(f["payload"])
        salida.append({**dict(f), "payload": payload})
    return salida


pytestmark = [pytestmark, pytest.mark.asyncio]


async def test_arranque_permite_responsable_directo(api_client, org):
    uid = await _new_user(api_client, org, "resp-arranque")
    r = await _grant(api_client, org, uid, "responsable_area", org["area"])
    assert r.status_code == 201, r.text


async def test_con_implementador_responsable_directo_409(api_client, org):
    impl = await _new_user(api_client, org, "impl")
    assert (await _grant(api_client, org, impl, "implementador")).status_code == 201
    uid = await _new_user(api_client, org, "resp-tarde")
    r = await _grant(api_client, org, uid, "responsable_area", org["area"])
    assert r.status_code == 409, r.text
    assert "responsable-requests" in r.text
    assert "ya tiene un implementador" in r.json()["detail"]


@pytest.mark.parametrize("rol", ["responsable_area", "coordinador", "implementador"])
async def test_nadie_se_autoconcede_un_rol_operativo(api_client, org, rol):
    area = org["area"] if rol == "responsable_area" else None
    r = await _grant(api_client, org, org["admin"], rol, area)
    assert r.status_code == 409, r.text
    assert "a sí mismo" in r.text


@pytest.mark.parametrize("rol", ["implementador", "dpo", "admin_organizacion"])
async def test_roles_no_restringidos_se_conceden_directo(api_client, org, rol):
    impl = await _new_user(api_client, org, "impl-base")
    if rol != "implementador":
        assert (await _grant(api_client, org, impl, "implementador")).status_code == 201
    uid = await _new_user(api_client, org, f"dest-{rol}")
    r = await _grant(api_client, org, uid, rol)
    assert r.status_code == 201, r.text


async def test_concesion_y_revocacion_dejan_rastro(api_client, factory, org):
    uid = await _new_user(api_client, org, "rastro")
    r = await _grant(api_client, org, uid, "implementador")
    assert r.status_code == 201, r.text
    asignacion = r.json()["id"]

    concedidos = [e for e in await _eventos(factory, org["tenant"], "role_granted") if e["entity_id"] == asignacion]
    assert len(concedidos) == 1
    ev = concedidos[0]
    assert ev["entity_type"] == "user_tenant_role"
    assert ev["user_id"] == org["admin"]
    assert ev["payload"]["target_user_id"] == uid
    assert ev["payload"]["role"] == "implementador"

    r = await api_client.delete(f"/api/v1/organizacion/roles/{asignacion}", headers=_admin(org))
    assert r.status_code == 200, r.text
    revocados = [e for e in await _eventos(factory, org["tenant"], "role_revoked") if e["entity_id"] == asignacion]
    assert len(revocados) == 1
    assert revocados[0]["user_id"] == org["admin"]
    assert revocados[0]["payload"] == {"target_user_id": uid, "role": "implementador", "area_id": None}


async def test_concesion_rechazada_no_deja_rastro(api_client, factory, org):
    r = await _grant(api_client, org, org["admin"], "coordinador")
    assert r.status_code == 409
    assert await _eventos(factory, org["tenant"], "role_granted") == []


async def test_flujo_rm10_concede_responsable_con_implementador(api_client, org):
    coord = await _new_user(api_client, org, "coord")
    impl = await _new_user(api_client, org, "impl-rm10")
    destino = await _new_user(api_client, org, "destino")
    assert (await _grant(api_client, org, coord, "coordinador")).status_code == 201
    assert (await _grant(api_client, org, impl, "implementador")).status_code == 201

    h_coord = _h(coord, org["tenant"], "coordinador")
    h_impl = _h(impl, org["tenant"], "implementador")
    r = await api_client.post(
        "/api/v1/areas/responsable-requests",
        json={"target_user_id": destino, "area_id": org["area"], "motivo": "ORG-05"},
        headers=h_coord,
    )
    assert r.status_code == 201, r.text
    sol = r.json()["id"]
    r = await api_client.post(f"/api/v1/areas/responsable-requests/{sol}/approve", json={"notas": "ok"}, headers=h_impl)
    assert r.status_code == 200, r.text
    r = await api_client.post(f"/api/v1/areas/responsable-requests/{sol}/execute", headers=h_impl)
    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "ejecutada"

    r = await api_client.get("/api/v1/organizacion/roles", headers=_admin(org))
    assert any(a["user_id"] == destino and a["role"] == "responsable_area" for a in r.json())
