"""Tests de integracion RBAC: administracion de la organizacion, SoD y alcance por area.

Skip automatico si `redis` no esta disponible en el interprete actual.
Permite que el arnes use su propio Python sin instalar dependencias.
"""
import importlib.util

import pytest

_REDIS_AVAILABLE = importlib.util.find_spec("redis") is not None
pytestmark = pytest.mark.skipif(
    not _REDIS_AVAILABLE,
    reason="redis no instalado en este entorno (arnes); usar .venv para tests completos",
)
import os
import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
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
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def org(factory):
    """Tenant + admin_organizacion. Cleanup de todo lo creado en el tenant."""
    ta = f"org-ta-{uuid.uuid4().hex[:8]}"
    admin = f"org-admin-{uuid.uuid4().hex[:8]}"
    domain = f"{ta}.test"

    async with factory() as s:
        await s.execute(text(
            "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
            "VALUES (:id, :n, :r, :ruc)"
        ), {"id": ta, "n": f"Org {ta}", "r": f"Org {ta} SA", "ruc": f"RUC{ta[:20]}"})
        await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:id, :e, 'Admin')"),
                        {"id": admin, "e": f"admin@{domain}"})
        await s.execute(text(
            "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) "
            "VALUES (:id, :u, :t, 'admin_organizacion')"
        ), {"id": f"utr-{uuid.uuid4().hex[:8]}", "u": admin, "t": ta})
        await s.commit()

    yield {"tenant": ta, "admin": admin, "domain": domain}

    async with factory() as s:
        for sql in (
            "DELETE FROM task_audit_log WHERE tenant_id = :t",
            "DELETE FROM task_evidence WHERE tenant_id = :t",
            "DELETE FROM roadmap_tasks WHERE tenant_id = :t",
            "DELETE FROM roadmap_waves WHERE tenant_id = :t",
            "DELETE FROM roadmaps WHERE tenant_id = :t",
            "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
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


async def _new_user(client, org, nombre: str) -> str:
    r = await client.post(
        "/api/v1/organizacion/usuarios",
        json={"email": f"{nombre}@{org['domain']}", "nombre": nombre},
        headers=_h(org["admin"], org["tenant"], "admin_organizacion"),
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _grant(client, org, user_id: str, role: str, area_id: str | None = None):
    body = {"user_id": user_id, "role": role}
    if area_id:
        body["area_id"] = area_id
    return await client.post(
        "/api/v1/organizacion/roles",
        json=body,
        headers=_h(org["admin"], org["tenant"], "admin_organizacion"),
    )


async def _seed_task(factory, tenant: str, area_id: str | None) -> str:
    rm, wv, tk = (f"{p}-{uuid.uuid4().hex[:8]}" for p in ("rm", "wv", "tk"))
    async with factory() as s:
        await s.execute(text("INSERT INTO roadmaps (id, tenant_id, status, variables_json) "
                             "VALUES (:id, :t, 'generated', '{}')"), {"id": rm, "t": tenant})
        await s.execute(text("INSERT INTO roadmap_waves (id, roadmap_id, tenant_id, name) "
                             "VALUES (:id, :r, :t, 'Ola 1')"), {"id": wv, "r": rm, "t": tenant})
        await s.execute(text(
            "INSERT INTO roadmap_tasks (id, wave_id, tenant_id, area_id, control_ref, dimension, "
            "title, priority, status) VALUES (:id, :w, :t, :a, 'P10', 'D02', 'Task', 'alta', 'pendiente')"
        ), {"id": tk, "w": wv, "t": tenant, "a": area_id})
        await s.commit()
    return tk


# ==================== /me/roles y acceso admin ====================

@pytest.mark.asyncio
async def test_me_roles_devuelve_roles_activos(api_client, org):
    r = await api_client.get("/api/v1/organizacion/me/roles", headers=_h(org["admin"], org["tenant"]))
    assert r.status_code == 200, r.text
    assert [x["role"] for x in r.json()["roles"]] == ["admin_organizacion"]


@pytest.mark.asyncio
async def test_no_admin_no_gestiona_roles(api_client, org):
    uid = await _new_user(api_client, org, "impl")
    assert (await _grant(api_client, org, uid, "implementador")).status_code == 201
    r = await api_client.get("/api/v1/organizacion/roles", headers=_h(uid, org["tenant"], "implementador"))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_area_id_en_rol_transversal_422(api_client, org):
    uid = await _new_user(api_client, org, "dpo422")
    r = await _grant(api_client, org, uid, "dpo", area_id="cualquiera")
    assert r.status_code == 422


# ==================== Asignación, SoD y revocación ====================

@pytest.mark.asyncio
async def test_sod_dpo_y_ciclo_de_revocacion(api_client, org):
    uid = await _new_user(api_client, org, "maria")

    r = await _grant(api_client, org, uid, "dpo")
    assert r.status_code == 201, r.text
    dpo_assignment = r.json()["id"]
    assert r.json()["granted_by"] == org["admin"]

    assert (await _grant(api_client, org, uid, "implementador")).status_code == 409
    assert (await _grant(api_client, org, uid, "encargado")).status_code == 409
    assert (await _grant(api_client, org, uid, "dpo")).status_code == 409  # duplicado activo
    assert (await _grant(api_client, org, uid, "admin_organizacion")).status_code == 201

    r = await api_client.delete(
        f"/api/v1/organizacion/roles/{dpo_assignment}",
        headers=_h(org["admin"], org["tenant"], "admin_organizacion"),
    )
    assert r.status_code == 200, r.text
    assert r.json()["revoked_by"] == org["admin"]

    # Sin DPO activo ya puede ser implementador; y entonces no puede volver a ser DPO.
    assert (await _grant(api_client, org, uid, "implementador")).status_code == 201
    assert (await _grant(api_client, org, uid, "dpo")).status_code == 409

    # El rol revocado ya no da acceso.
    r = await api_client.get("/api/v1/organizacion/me/roles", headers=_h(uid, org["tenant"]))
    assert sorted(x["role"] for x in r.json()["roles"]) == ["admin_organizacion", "implementador"]


@pytest.mark.asyncio
async def test_regrant_reactiva_asignacion_revocada(api_client, org):
    uid = await _new_user(api_client, org, "reactiva")
    first = (await _grant(api_client, org, uid, "encargado")).json()["id"]
    await api_client.delete(f"/api/v1/organizacion/roles/{first}",
                            headers=_h(org["admin"], org["tenant"], "admin_organizacion"))
    r = await _grant(api_client, org, uid, "encargado")
    assert r.status_code == 201, r.text
    assert r.json()["id"] == first
    assert r.json()["valid_to"] is None


@pytest.mark.asyncio
async def test_no_se_revoca_ultimo_admin(api_client, org):
    r = await api_client.get("/api/v1/organizacion/me/roles", headers=_h(org["admin"], org["tenant"]))
    assignment = r.json()["roles"][0]["id"]
    r = await api_client.delete(f"/api/v1/organizacion/roles/{assignment}",
                                headers=_h(org["admin"], org["tenant"], "admin_organizacion"))
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_trigger_bd_bloquea_dpo_con_rol_operativo(factory, org):
    """Respaldo en BD: aunque se salte la API, el trigger rechaza la combinación."""
    async with factory() as s:
        await s.execute(text(
            "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, 'implementador')"
        ), {"id": f"utr-{uuid.uuid4().hex[:8]}", "u": org["admin"], "t": org["tenant"]})
        await s.commit()
        with pytest.raises(DBAPIError):
            await s.execute(text(
                "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, 'dpo')"
            ), {"id": f"utr-{uuid.uuid4().hex[:8]}", "u": org["admin"], "t": org["tenant"]})
        await s.rollback()


# ==================== Alcance por área ====================

@pytest.mark.asyncio
async def test_responsable_area_acotado_a_su_area_y_subareas(api_client, factory, org):
    admin_h = _h(org["admin"], org["tenant"], "admin_organizacion")
    finanzas = (await api_client.post("/api/v1/organizacion/areas", json={"nombre": "Finanzas"}, headers=admin_h)).json()["id"]
    tesoreria = (await api_client.post("/api/v1/organizacion/areas",
                                       json={"nombre": "Tesorería", "parent_area_id": finanzas},
                                       headers=admin_h)).json()["id"]
    rrhh = (await api_client.post("/api/v1/organizacion/areas", json={"nombre": "RRHH"}, headers=admin_h)).json()["id"]

    uid = await _new_user(api_client, org, "resp")
    assert (await _grant(api_client, org, uid, "responsable_area", area_id=finanzas)).status_code == 201

    r = await api_client.patch(f"/api/v1/organizacion/areas/{finanzas}",
                               json={"responsable_user_id": uid}, headers=admin_h)
    assert r.status_code == 200 and r.json()["responsable_user_id"] == uid

    tk_sub = await _seed_task(factory, org["tenant"], tesoreria)
    tk_otra = await _seed_task(factory, org["tenant"], rrhh)
    body = {"filename": "e.pdf", "mime_type": "application/pdf", "file_size": 10}
    h = _h(uid, org["tenant"], "responsable_area")

    r = await api_client.post(f"/api/v1/roadmaps/tasks/{tk_sub}/evidence/upload-url", json=body, headers=h)
    assert r.status_code == 200, r.text
    r = await api_client.post(f"/api/v1/roadmaps/tasks/{tk_otra}/evidence/upload-url", json=body, headers=h)
    assert r.status_code == 403
    r = await api_client.post("/api/v1/roadmaps/tasks/no-existe/evidence/upload-url", json=body, headers=h)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_responsable_area_sin_responsable_de_area_409(api_client, org):
    admin_h = _h(org["admin"], org["tenant"], "admin_organizacion")
    area = (await api_client.post("/api/v1/organizacion/areas", json={"nombre": "Legal"}, headers=admin_h)).json()["id"]
    uid = await _new_user(api_client, org, "sinrol")
    r = await api_client.patch(f"/api/v1/organizacion/areas/{area}",
                               json={"responsable_user_id": uid}, headers=admin_h)
    assert r.status_code == 409


# ==================== Cuatro ojos en evidencia ====================

@pytest.mark.asyncio
async def test_quien_sube_evidencia_no_la_valida(api_client, factory, org):
    enc = await _new_user(api_client, org, "enc")
    dpo = await _new_user(api_client, org, "dpo")
    assert (await _grant(api_client, org, enc, "encargado")).status_code == 201
    assert (await _grant(api_client, org, dpo, "dpo")).status_code == 201

    tk = await _seed_task(factory, org["tenant"], None)
    r = await api_client.post(
        f"/api/v1/roadmaps/tasks/{tk}/evidence",
        params={"r2_key": f"{org['tenant']}/{tk}/e.pdf", "mime_type": "application/pdf", "file_size": 10},
        headers=_h(enc, org["tenant"], "encargado"),
    )
    assert r.status_code == 201, r.text
    ev = r.json()["id"]

    url = f"/api/v1/roadmaps/tasks/{tk}/evidence/{ev}"
    body = {"validation_status": "approved", "notes": "ok"}
    r = await api_client.patch(url, json=body, headers=_h(enc, org["tenant"], "encargado"))
    assert r.status_code == 409
    r = await api_client.patch(url, json=body, headers=_h(dpo, org["tenant"], "dpo"))
    assert r.status_code == 200, r.text
    assert r.json()["validated_by"] == dpo
