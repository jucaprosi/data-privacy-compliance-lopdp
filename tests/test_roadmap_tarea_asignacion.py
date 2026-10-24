"""Tests de integración y árbitro para RM-08: Distribuir tareas a los responsables.
`¤roadmap` `¤rbac-tenant`

Endpoint: POST /roadmaps/tasks/{id}/assign
Valida:
1. Rol autorizado: 'coordinador' (403 si otro rol).
2. Tarea de otro tenant -> 404 Not Found.
3. Tarea inexistente -> 404 Not Found.
4. responsable_id no existe en el tenant o está inactivo -> 404 Not Found.
5. El usuario no posee el rol 'responsable_area' activo en el tenant -> 404 Not Found.
6. El responsable no pertenece al mismo área que la tarea -> 422 Unprocessable Entity (ErrorNegocio RESPONSABLE_AREA_MISMATCH).
7. Asignación exitosa cuando coincide el área:
   - Retorna la tarea actualizada con el owner asignado.
   - Registra el evento de auditoría 'task_assigned' en task_audit_log (disparador para NOTIF-01).
"""
import os
import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from main import app
from app_core.db.session import get_session

pytestmark = pytest.mark.asyncio


def _async_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@pytest_asyncio.fixture
async def api_client():
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
async def seed_data():
    """Genera:
    - 2 tenants (tenant_a, tenant_b)
    - Áreas en tenant_a (area_legal, area_ti)
    - Usuarios en tenant_a:
      * coord_a (rol 'coordinador')
      * resp_legal (rol 'responsable_area' en area_legal)
      * resp_ti (rol 'responsable_area' en area_ti)
      * no_resp (rol 'implementador', sin responsable_area)
    - Tarea en tenant_a (task_legal, asignada a area_legal)
    - Tarea en tenant_b (task_tenant_b)
    """
    engine = create_async_engine(_async_url())
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    ta = f"ta-rm08-{uuid.uuid4().hex[:8]}"
    tb = f"tb-rm08-{uuid.uuid4().hex[:8]}"

    u_coord = f"u-coord-{uuid.uuid4().hex[:8]}"
    u_resp_legal = f"u-rleg-{uuid.uuid4().hex[:8]}"
    u_resp_ti = f"u-rti-{uuid.uuid4().hex[:8]}"
    u_no_resp = f"u-noresp-{uuid.uuid4().hex[:8]}"

    area_legal = f"area-leg-{uuid.uuid4().hex[:8]}"
    area_ti = f"area-ti-{uuid.uuid4().hex[:8]}"

    roadmap_a = f"rdm-a-{uuid.uuid4().hex[:8]}"
    wave_a = f"wv-a-{uuid.uuid4().hex[:8]}"
    task_legal = f"tsk-leg-{uuid.uuid4().hex[:8]}"
    task_sin_area = f"tsk-sin-area-{uuid.uuid4().hex[:8]}"

    roadmap_b = f"rdm-b-{uuid.uuid4().hex[:8]}"
    wave_b = f"wv-b-{uuid.uuid4().hex[:8]}"
    task_b = f"tsk-b-{uuid.uuid4().hex[:8]}"

    async with factory() as session:
        # Tenants
        for t in (ta, tb):
            await session.execute(text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                "VALUES (:id, :n, :r, :ruc)"
            ), {"id": t, "n": f"Tenant {t}", "r": f"Tenant {t} SA", "ruc": f"RUC{t[:20]}"})

        # Users
        users_meta = [
            (u_coord, f"{u_coord}@test.local", "Coordinador Test"),
            (u_resp_legal, f"{u_resp_legal}@test.local", "Abogado Responsable"),
            (u_resp_ti, f"{u_resp_ti}@test.local", "TI Responsable"),
            (u_no_resp, f"{u_no_resp}@test.local", "Implementador"),
        ]
        for uid, email, nombre in users_meta:
            await session.execute(text(
                "INSERT INTO users (id, email, nombre) VALUES (:id, :e, :n)"
            ), {"id": uid, "e": email, "n": nombre})

        # Áreas
        await session.execute(text(
            "INSERT INTO areas (id, tenant_id, nombre, codigo) VALUES (:id, :t, :n, :c)"
        ), {"id": area_legal, "t": ta, "n": "Área Legal", "c": "LEG"})
        await session.execute(text(
            "INSERT INTO areas (id, tenant_id, nombre, codigo) VALUES (:id, :t, :n, :c)"
        ), {"id": area_ti, "t": ta, "n": "Área TI", "c": "TI"})

        # Roles
        roles_meta = [
            (u_coord, ta, "coordinador", None),
            (u_resp_legal, ta, "responsable_area", area_legal),
            (u_resp_ti, ta, "responsable_area", area_ti),
            (u_no_resp, ta, "implementador", None),
        ]
        for uid, tid, role, aid in roles_meta:
            await session.execute(text(
                "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role, area_id) "
                "VALUES (:id, :uid, :tid, :r, :aid)"
            ), {"id": f"role-{uuid.uuid4().hex[:8]}", "uid": uid, "tid": tid, "r": role, "aid": aid})

        # Roadmaps & Waves
        await session.execute(text(
            "INSERT INTO roadmaps (id, tenant_id, status, variables_json) "
            "VALUES (:id, :t, 'active', '{}')"
        ), {"id": roadmap_a, "t": ta})
        await session.execute(text(
            "INSERT INTO roadmap_waves (id, roadmap_id, tenant_id, name, sort_order) "
            "VALUES (:id, :rid, :t, 'Ola 1', 1)"
        ), {"id": wave_a, "rid": roadmap_a, "t": ta})

        await session.execute(text(
            "INSERT INTO roadmaps (id, tenant_id, status, variables_json) "
            "VALUES (:id, :t, 'active', '{}')"
        ), {"id": roadmap_b, "t": tb})
        await session.execute(text(
            "INSERT INTO roadmap_waves (id, roadmap_id, tenant_id, name, sort_order) "
            "VALUES (:id, :rid, :t, 'Ola 1 B', 1)"
        ), {"id": wave_b, "rid": roadmap_b, "t": tb})

        # Tasks
        await session.execute(text(
            """
            INSERT INTO roadmap_tasks (
                id, wave_id, tenant_id, area_id, control_ref, dimension, title, description, priority, status
            ) VALUES (
                :id, :wid, :tid, :aid, 'P1', 'D01', 'Redactar Política', 'Desc', 'alta', 'pendiente'
            )
            """
        ), {"id": task_legal, "wid": wave_a, "tid": ta, "aid": area_legal})

        await session.execute(text(
            """
            INSERT INTO roadmap_tasks (
                id, wave_id, tenant_id, area_id, control_ref, dimension, title, description, priority, status
            ) VALUES (
                :id, :wid, :tid, NULL, 'P3', 'D01', 'Tarea generada sin área', 'Desc', 'alta', 'pendiente'
            )
            """
        ), {"id": task_sin_area, "wid": wave_a, "tid": ta})

        await session.execute(text(
            """
            INSERT INTO roadmap_tasks (
                id, wave_id, tenant_id, area_id, control_ref, dimension, title, description, priority, status
            ) VALUES (
                :id, :wid, :tid, NULL, 'P2', 'D01', 'Tarea Tenant B', 'Desc', 'alta', 'pendiente'
            )
            """
        ), {"id": task_b, "wid": wave_b, "tid": tb})

        await session.commit()

    yield {
        "tenant_a": ta,
        "tenant_b": tb,
        "u_coord": u_coord,
        "u_resp_legal": u_resp_legal,
        "u_resp_ti": u_resp_ti,
        "u_no_resp": u_no_resp,
        "area_legal": area_legal,
        "area_ti": area_ti,
        "task_legal": task_legal,
        "task_sin_area": task_sin_area,
        "task_b": task_b,
    }

    # Cleanup
    async with factory() as session:
        try:
            for t in (ta, tb):
                await session.execute(text("DELETE FROM task_audit_log WHERE tenant_id = :t"), {"t": t})
                await session.execute(text("DELETE FROM task_evidence WHERE tenant_id = :t"), {"t": t})
                await session.execute(text(
                    "DELETE FROM task_dependencies WHERE task_id IN "
                    "(SELECT id FROM roadmap_tasks WHERE tenant_id = :t)"
                ), {"t": t})
                await session.execute(text("DELETE FROM roadmap_tasks WHERE tenant_id = :t"), {"t": t})
                await session.execute(text("DELETE FROM roadmap_waves WHERE tenant_id = :t"), {"t": t})
                await session.execute(text("DELETE FROM roadmaps WHERE tenant_id = :t"), {"t": t})
                await session.execute(text("DELETE FROM areas WHERE tenant_id = :t"), {"t": t})
                await session.execute(text("DELETE FROM user_tenant_roles WHERE tenant_id = :t"), {"t": t})
                await session.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t})
            for uid, _, _ in users_meta:
                await session.execute(text("DELETE FROM users WHERE id = :u"), {"u": uid})
            await session.commit()
        except Exception:
            await session.rollback()

    await engine.dispose()


def _headers(user_id: str, tenant_id: str, role: str) -> dict:
    return {
        "X-User-ID": user_id,
        "X-Tenant-ID": tenant_id,
        "X-Role": role,
    }


async def test_assign_exitoso_misma_area(api_client, seed_data):
    """Coordinador asigna tarea a responsable de su misma área -> 200 OK y audit log registrado."""
    res = await api_client.post(
        f"/api/v1/roadmaps/tasks/{seed_data['task_legal']}/assign",
        headers=_headers(seed_data["u_coord"], seed_data["tenant_a"], "coordinador"),
        json={"responsable_id": seed_data["u_resp_legal"]},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["id"] == seed_data["task_legal"]
    assert data["owner"] == "Abogado Responsable"

    # Verificar registro en task_audit_log
    engine = create_async_engine(_async_url())
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        log_row = (await session.execute(
            text(
                "SELECT task_id, tenant_id, action, user_id, payload "
                "FROM task_audit_log WHERE task_id = :tid"
            ),
            {"tid": seed_data["task_legal"]},
        )).mappings().first()
        assert log_row is not None
        assert log_row["action"] == "task_assigned"
        assert log_row["user_id"] == seed_data["u_coord"]
        assert log_row["tenant_id"] == seed_data["tenant_a"]
        assert log_row["payload"]["responsable_id"] == seed_data["u_resp_legal"]
    await engine.dispose()


async def test_asigna_area_y_responsable_a_tarea_generada(api_client, seed_data):
    res = await api_client.post(
        f"/api/v1/roadmaps/tasks/{seed_data['task_sin_area']}/assign",
        headers=_headers(seed_data["u_coord"], seed_data["tenant_a"], "coordinador"),
        json={"responsable_id": seed_data["u_resp_legal"], "area_id": seed_data["area_legal"]},
    )
    assert res.status_code == 200, res.text
    assert res.json()["area_id"] == seed_data["area_legal"]


async def test_tarea_sin_area_exige_area_explicita(api_client, seed_data):
    res = await api_client.post(
        f"/api/v1/roadmaps/tasks/{seed_data['task_sin_area']}/assign",
        headers=_headers(seed_data["u_coord"], seed_data["tenant_a"], "coordinador"),
        json={"responsable_id": seed_data["u_resp_legal"]},
    )
    assert res.status_code == 422, res.text
    assert res.json()["code"] == "TASK_AREA_REQUIRED"
    assert "seleccionar el área" in res.json()["detail"].lower()


async def test_area_inexistente_o_de_otro_tenant_responde_404(api_client, seed_data):
    res = await api_client.post(
        f"/api/v1/roadmaps/tasks/{seed_data['task_sin_area']}/assign",
        headers=_headers(seed_data["u_coord"], seed_data["tenant_a"], "coordinador"),
        json={"responsable_id": seed_data["u_resp_legal"], "area_id": "area-de-otro-tenant"},
    )
    assert res.status_code == 404, res.text
    assert "área no encontrada" in res.json()["detail"].lower()


async def test_redistribuye_area_y_audita_anterior_y_nueva(api_client, seed_data):
    res = await api_client.post(
        f"/api/v1/roadmaps/tasks/{seed_data['task_legal']}/assign",
        headers=_headers(seed_data["u_coord"], seed_data["tenant_a"], "coordinador"),
        json={"responsable_id": seed_data["u_resp_ti"], "area_id": seed_data["area_ti"]},
    )
    assert res.status_code == 200, res.text
    assert res.json()["area_id"] == seed_data["area_ti"]

    engine = create_async_engine(_async_url())
    async with engine.connect() as conn:
        payload = (await conn.execute(text(
            "SELECT payload FROM task_audit_log WHERE task_id = :id AND action = 'task_assigned' "
            "ORDER BY timestamp DESC LIMIT 1"
        ), {"id": seed_data["task_legal"]})).scalar_one()
    await engine.dispose()
    assert payload["area_id_anterior"] == seed_data["area_legal"]
    assert payload["area_id_nueva"] == seed_data["area_ti"]


async def test_assign_rechazado_distinta_area_422(api_client, seed_data):
    """Responsable pertenece a TI pero la tarea es de Legal -> 422 con ErrorNegocio."""
    res = await api_client.post(
        f"/api/v1/roadmaps/tasks/{seed_data['task_legal']}/assign",
        headers=_headers(seed_data["u_coord"], seed_data["tenant_a"], "coordinador"),
        json={"responsable_id": seed_data["u_resp_ti"]},
    )
    assert res.status_code == 422, res.text
    error_data = res.json()
    assert error_data["code"] == "RESPONSABLE_AREA_MISMATCH"
    assert "área" in error_data["detail"].lower()


async def test_assign_rechazado_rol_no_coordinador_403(api_client, seed_data):
    """Usuario con rol implementador intenta asignar -> 403 Forbidden."""
    res = await api_client.post(
        f"/api/v1/roadmaps/tasks/{seed_data['task_legal']}/assign",
        headers=_headers(seed_data["u_no_resp"], seed_data["tenant_a"], "implementador"),
        json={"responsable_id": seed_data["u_resp_legal"]},
    )
    assert res.status_code == 403


async def test_assign_rechazado_tarea_otro_tenant_404(api_client, seed_data):
    """Coordinador de Tenant A intenta asignar tarea perteneciente a Tenant B -> 404 Not Found."""
    res = await api_client.post(
        f"/api/v1/roadmaps/tasks/{seed_data['task_b']}/assign",
        headers=_headers(seed_data["u_coord"], seed_data["tenant_a"], "coordinador"),
        json={"responsable_id": seed_data["u_resp_legal"]},
    )
    assert res.status_code == 404
    assert "no encontrada" in res.json()["detail"].lower()


async def test_assign_rechazado_responsable_inexistente_404(api_client, seed_data):
    """responsable_id no existe en el tenant -> 404 Not Found."""
    res = await api_client.post(
        f"/api/v1/roadmaps/tasks/{seed_data['task_legal']}/assign",
        headers=_headers(seed_data["u_coord"], seed_data["tenant_a"], "coordinador"),
        json={"responsable_id": "usuario-inexistente"},
    )
    assert res.status_code == 404


async def test_assign_rechazado_usuario_sin_rol_responsable_404(api_client, seed_data):
    """Usuario existe en el tenant pero su rol es implementador, no responsable_area -> 404 Not Found."""
    res = await api_client.post(
        f"/api/v1/roadmaps/tasks/{seed_data['task_legal']}/assign",
        headers=_headers(seed_data["u_coord"], seed_data["tenant_a"], "coordinador"),
        json={"responsable_id": seed_data["u_no_resp"]},
    )
    assert res.status_code == 404
