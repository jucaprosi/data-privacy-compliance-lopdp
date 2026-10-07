"""Tests de integración del router de roadmaps con httpx ASGITransport + RBAC."""
import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def _async_url() -> str:
    url = os.environ["TEST_DATABASE_URL"]
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@pytest_asyncio.fixture
async def api_client():
    """Cliente httpx async con app + dependency override de get_session."""
    from main import app
    from app_core.db.session import get_session

    engine = create_async_engine(_async_url(), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

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
    await engine.dispose()


@pytest_asyncio.fixture
async def api_seed():
    """Crea tenant + user + rol (implementador) para tests de API."""
    engine = create_async_engine(_async_url())
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    ta = f"api-ta-{uuid.uuid4().hex[:8]}"
    user = f"api-user-{uuid.uuid4().hex[:8]}"

    async with factory() as session:
        await session.execute(text(
            "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
            "VALUES (:id, :n, :r, :ruc)"
        ), {"id": ta, "n": f"API Test {ta}", "r": f"API {ta} SA", "ruc": f"RUC{ta[:20]}"})
        await session.execute(text(
            "INSERT INTO users (id, email, nombre) VALUES (:id, :e, :n)"
        ), {"id": user, "e": f"{user}@test.local", "n": f"User {user}"})
        await session.execute(text(
            "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) "
            "VALUES (:id, :uid, :tid, 'implementador')"
        ), {"id": f"role-{uuid.uuid4().hex[:8]}", "uid": user, "tid": ta})
        await session.commit()

    yield {"tenant": ta, "user": user, "role": "implementador"}

    async with factory() as session:
        try:
            await session.execute(text("DELETE FROM task_audit_log WHERE tenant_id = :t"), {"t": ta})
            await session.execute(text("DELETE FROM task_evidence WHERE tenant_id = :t"), {"t": ta})
            await session.execute(text(
                "DELETE FROM task_dependencies WHERE task_id IN "
                "(SELECT id FROM roadmap_tasks WHERE tenant_id = :t)"
            ), {"t": ta})
            await session.execute(text("DELETE FROM roadmap_tasks WHERE tenant_id = :t"), {"t": ta})
            await session.execute(text("DELETE FROM roadmap_waves WHERE tenant_id = :t"), {"t": ta})
            await session.execute(text("DELETE FROM roadmaps WHERE tenant_id = :t"), {"t": ta})
            await session.execute(text("DELETE FROM user_tenant_roles WHERE tenant_id = :t"), {"t": ta})
            await session.execute(text("DELETE FROM users WHERE id = :u"), {"u": user})
            await session.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": ta})
            await session.commit()
        except Exception:
            await session.rollback()

    await engine.dispose()


def _h(user: str, tenant: str, role: str) -> dict:
    return {"X-User-ID": user, "X-Tenant-ID": tenant, "X-Role": role}


def _payload(seed):
    return {
        "tenant_id": seed["tenant"],
        "user_id": seed["user"],
        "variables": {
            "plazo_meses": 6, "presupuesto": 1000.0, "moneda": "USD",
            "equipo": ["DPO"], "dpo": "Maria", "idioma": "ES",
        },
    }


# ==================== POST /roadmaps/generate ====================

@pytest.mark.asyncio
async def test_generate_implementador_ok(api_client, api_seed):
    r = await api_client.post(
        "/api/v1/roadmaps/generate",
        json=_payload(api_seed),
        headers=_h(api_seed["user"], api_seed["tenant"], "implementador"),
    )
    assert r.status_code == 202, r.text
    assert "job_id" in r.json()


@pytest.mark.asyncio
async def test_generate_dpo_rechazado(api_client, api_seed):
    r = await api_client.post(
        "/api/v1/roadmaps/generate",
        json=_payload(api_seed),
        headers=_h(api_seed["user"], api_seed["tenant"], "dpo"),
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_generate_sin_membresia(api_client, api_seed):
    r = await api_client.post(
        "/api/v1/roadmaps/generate",
        json=_payload(api_seed),
        headers=_h("user-desconocido", api_seed["tenant"], "implementador"),
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_generate_rol_invalido(api_client, api_seed):
    r = await api_client.post(
        "/api/v1/roadmaps/generate",
        json=_payload(api_seed),
        headers=_h(api_seed["user"], api_seed["tenant"], "rol-inexistente"),
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_generate_sin_headers(api_client, api_seed):
    r = await api_client.post("/api/v1/roadmaps/generate", json=_payload(api_seed))
    assert r.status_code == 422


# ==================== GET /roadmaps/{id} ====================

@pytest.mark.asyncio
async def test_get_roadmap_inexistente_404(api_client, api_seed):
    r = await api_client.get(
        "/api/v1/roadmaps/no-existe",
        headers=_h(api_seed["user"], api_seed["tenant"], "implementador"),
    )
    assert r.status_code == 404


# ==================== GET /roadmaps/{id}/kpis ====================

@pytest.mark.asyncio
async def test_get_kpis_inexistente_ceros(api_client, api_seed):
    r = await api_client.get(
        "/api/v1/roadmaps/no-existe/kpis",
        headers=_h(api_seed["user"], api_seed["tenant"], "implementador"),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total_tareas"] == 0
    assert body["progreso_porcentaje"] == 0.0


# ==================== PATCH /roadmaps/tasks/{id} ====================

@pytest.mark.asyncio
async def test_patch_task_implementador_ok(api_client, api_seed):
    rm_id = f"rm-{uuid.uuid4().hex[:8]}"
    wv_id = f"wv-{uuid.uuid4().hex[:8]}"
    tk_id = f"tk-{uuid.uuid4().hex[:8]}"

    engine = create_async_engine(_async_url())
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as s:
        await s.execute(text(
            "INSERT INTO roadmaps (id, tenant_id, status, variables_json) "
            "VALUES (:id, :t, 'generated', '{}')"
        ), {"id": rm_id, "t": api_seed["tenant"]})
        await s.execute(text(
            "INSERT INTO roadmap_waves (id, roadmap_id, tenant_id, name) "
            "VALUES (:id, :r, :t, 'Ola 1')"
        ), {"id": wv_id, "r": rm_id, "t": api_seed["tenant"]})
        await s.execute(text(
            "INSERT INTO roadmap_tasks (id, wave_id, tenant_id, control_ref, dimension, "
            "title, priority, status) "
            "VALUES (:id, :w, :t, 'P10', 'D02', 'Task', 'critica', 'pendiente')"
        ), {"id": tk_id, "w": wv_id, "t": api_seed["tenant"]})
        await s.commit()
    await engine.dispose()

    r = await api_client.patch(
        f"/api/v1/roadmaps/tasks/{tk_id}",
        json={"status": "completada"},
        headers=_h(api_seed["user"], api_seed["tenant"], "implementador"),
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "completada"


@pytest.mark.asyncio
async def test_patch_task_dpo_rechazado(api_client, api_seed):
    r = await api_client.patch(
        "/api/v1/roadmaps/tasks/cualquiera",
        json={"status": "completada"},
        headers=_h(api_seed["user"], api_seed["tenant"], "dpo"),
    )
    assert r.status_code == 403


# ==================== POST /roadmaps/tasks/{id}/evidence/upload-url ====================

@pytest.mark.asyncio
async def test_evidence_upload_url_responsable_ok(api_client, api_seed):
    engine = create_async_engine(_async_url())
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as s:
        await s.execute(text(
            "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) "
            "VALUES (:id, :u, :t, 'responsable_area')"
        ), {"id": f"role-{uuid.uuid4().hex[:8]}", "u": api_seed["user"], "t": api_seed["tenant"]})
        await s.commit()
    await engine.dispose()

    r = await api_client.post(
        "/api/v1/roadmaps/tasks/any-task/evidence/upload-url",
        json={"filename": "evidencia.pdf", "mime_type": "application/pdf", "file_size": 1024},
        headers=_h(api_seed["user"], api_seed["tenant"], "responsable_area"),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "url" in body and "key" in body


@pytest.mark.asyncio
async def test_evidence_upload_url_dpo_rechazado(api_client, api_seed):
    r = await api_client.post(
        "/api/v1/roadmaps/tasks/any-task/evidence/upload-url",
        json={"filename": "evidencia.pdf", "mime_type": "application/pdf", "file_size": 1024},
        headers=_h(api_seed["user"], api_seed["tenant"], "dpo"),
    )
    assert r.status_code == 403
