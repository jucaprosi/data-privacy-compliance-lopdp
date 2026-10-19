# ¤roadmap
"""Suite de pruebas para la edición de tareas de la hoja de ruta (RM-07).

Valida:
1. Endpoint PATCH /api/v1/roadmaps/tasks/{id}/details.
2. Rol 'implementador' requerido (roles no autorizados reciben 403).
3. Modificación exitosa de los campos editables:
   - título
   - fecha_inicio
   - fecha_fin
   - responsable_id
   - kpi
   - entregable
4. Validación de rango de fechas: fecha_fin < fecha_inicio devuelve 422 con ErrorNegocio.
5. Aislamiento multi-tenant: intento de edición de tarea perteneciente a otro tenant devuelve 404.
6. Registro inmutable de auditoría con evento 'task_edited' y payload de cambios en task_audit_log.
"""
import os
import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from main import app
from features.roadmap.roadmap_service import TaskDetailsUpdate, edit_task_details

client = TestClient(app)


def _async_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("Sin TEST_DATABASE_URL para tests de BD")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@pytest_asyncio.fixture
async def seed_data():
    """Crea tenant principal con usuario implementador, un segundo tenant ajeno y una tarea."""
    engine = create_async_engine(_async_url())
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    t1 = f"t1-{uuid.uuid4().hex[:8]}"
    t2 = f"t2-{uuid.uuid4().hex[:8]}"
    u_impl = f"uimpl-{uuid.uuid4().hex[:8]}"
    u_otro = f"uotro-{uuid.uuid4().hex[:8]}"
    rid = f"rm-{uuid.uuid4().hex[:8]}"
    wid = f"wv-{uuid.uuid4().hex[:8]}"
    task_id = f"task-{uuid.uuid4().hex[:8]}"

    d_ini = date.today()
    d_fin = d_ini + timedelta(days=15)

    async with factory() as session:
        # Tenants
        await session.execute(
            text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:id, :n, :r, :ruc)"),
            {"id": t1, "n": f"Tenant 1 {t1}", "r": f"Razón {t1}", "ruc": f"RUC{t1[:15]}"},
        )
        await session.execute(
            text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:id, :n, :r, :ruc)"),
            {"id": t2, "n": f"Tenant 2 {t2}", "r": f"Razón {t2}", "ruc": f"RUC{t2[:15]}"},
        )
        # Users
        await session.execute(
            text("INSERT INTO users (id, email, nombre) VALUES (:id, :e, :n)"),
            {"id": u_impl, "e": f"{u_impl}@test.local", "n": "Implementador"},
        )
        await session.execute(
            text("INSERT INTO users (id, email, nombre) VALUES (:id, :e, :n)"),
            {"id": u_otro, "e": f"{u_otro}@test.local", "n": "Otro Rol"},
        )
        # Roles
        await session.execute(
            text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :uid, :tid, 'implementador')"),
            {"id": f"r1-{uuid.uuid4().hex[:8]}", "uid": u_impl, "tid": t1},
        )
        await session.execute(
            text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :uid, :tid, 'coordinador')"),
            {"id": f"r2-{uuid.uuid4().hex[:8]}", "uid": u_otro, "tid": t1},
        )
        await session.execute(
            text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :uid, :tid, 'implementador')"),
            {"id": f"r3-{uuid.uuid4().hex[:8]}", "uid": u_impl, "tid": t2},
        )

        # Roadmap y Wave
        await session.execute(
            text("INSERT INTO roadmaps (id, tenant_id, status, variables_json, summary) VALUES (:id, :tid, 'draft', '{}', 'Test RM')"),
            {"id": rid, "tid": t1},
        )
        await session.execute(
            text("INSERT INTO roadmap_waves (id, roadmap_id, tenant_id, name, sort_order) VALUES (:id, :rid, :tid, 'Ola 1', 1)"),
            {"id": wid, "rid": rid, "tid": t1},
        )

        # Task
        await session.execute(
            text("""
                INSERT INTO roadmap_tasks
                    (id, wave_id, tenant_id, control_ref, dimension, title, description, owner, priority, effort_hours, start_date, end_date, status, kpi, deliverable)
                VALUES
                    (:id, :wid, :tid, 'P1', 'D01', 'Título Original', 'Desc', 'Responsable Original', 'critica', 10, :ini, :fin, 'pendiente', 'KPI Original', 'Entregable Original')
            """),
            {"id": task_id, "wid": wid, "tid": t1, "ini": d_ini, "fin": d_fin},
        )
        await session.commit()

    yield {
        "tenant_id": t1,
        "tenant_ajeno": t2,
        "user_impl": u_impl,
        "user_otro": u_otro,
        "task_id": task_id,
        "d_ini": d_ini,
        "d_fin": d_fin,
    }

    # Limpieza
    async with factory() as session:
        try:
            await session.execute(text("DELETE FROM task_audit_log WHERE tenant_id IN (:t1, :t2)"), {"t1": t1, "t2": t2})
            await session.execute(text("DELETE FROM roadmap_tasks WHERE tenant_id IN (:t1, :t2)"), {"t1": t1, "t2": t2})
            await session.execute(text("DELETE FROM roadmap_waves WHERE tenant_id IN (:t1, :t2)"), {"t1": t1, "t2": t2})
            await session.execute(text("DELETE FROM roadmaps WHERE tenant_id IN (:t1, :t2)"), {"t1": t1, "t2": t2})
            await session.execute(text("DELETE FROM user_tenant_roles WHERE tenant_id IN (:t1, :t2)"), {"t1": t1, "t2": t2})
            await session.execute(text("DELETE FROM users WHERE id IN (:u1, :u2)"), {"u1": u_impl, "u2": u_otro})
            await session.execute(text("DELETE FROM tenants WHERE id IN (:t1, :t2)"), {"t1": t1, "t2": t2})
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


def test_patch_task_details_exitoso(seed_data):
    """El implementador actualiza campos de la tarea y se registran en BD y auditoría."""
    t_id = seed_data["task_id"]
    headers = _headers(seed_data["user_impl"], seed_data["tenant_id"], "implementador")

    nueva_ini = (date.today() + timedelta(days=2)).isoformat()
    nueva_fin = (date.today() + timedelta(days=20)).isoformat()

    body = {
        "titulo": "Nuevo Título Actualizado",
        "fecha_inicio": nueva_ini,
        "fecha_fin": nueva_fin,
        "responsable_id": "DPO_Corporativo",
        "kpi": "100% de políticas aprobadas",
        "entregable": "Documento de Políticas v2",
    }

    resp = client.patch(f"/api/v1/roadmaps/tasks/{t_id}/details", json=body, headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["title"] == "Nuevo Título Actualizado"
    assert data["start_date"] == nueva_ini
    assert data["end_date"] == nueva_fin
    assert data["owner"] == "DPO_Corporativo"
    assert data["kpi"] == "100% de políticas aprobadas"
    assert data["deliverable"] == "Documento de Políticas v2"


@pytest.mark.asyncio
async def test_patch_task_details_registra_auditoria(seed_data):
    """Comprueba que la acción 'task_edited' quede asentada en task_audit_log."""
    engine = create_async_engine(_async_url())
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    t_id = seed_data["task_id"]
    headers = _headers(seed_data["user_impl"], seed_data["tenant_id"], "implementador")

    body = {"titulo": "Título Auditado"}
    resp = client.patch(f"/api/v1/roadmaps/tasks/{t_id}/details", json=body, headers=headers)
    assert resp.status_code == 200

    async with factory() as session:
        res = await session.execute(
            text("SELECT * FROM task_audit_log WHERE task_id = :tid AND action = 'task_edited'"),
            {"tid": t_id},
        )
        logs = res.mappings().all()
        assert len(logs) >= 1
        ultimo = logs[-1]
        assert ultimo["action"] == "task_edited"
        assert ultimo["user_id"] == seed_data["user_impl"]
        assert ultimo["tenant_id"] == seed_data["tenant_id"]
        assert "title" in ultimo["payload"]

    await engine.dispose()


def test_patch_task_details_fechas_invalidas_422(seed_data):
    """Si fecha_fin es anterior a fecha_inicio, responde 422 con ErrorNegocio."""
    t_id = seed_data["task_id"]
    headers = _headers(seed_data["user_impl"], seed_data["tenant_id"], "implementador")

    body = {
        "fecha_inicio": (date.today() + timedelta(days=10)).isoformat(),
        "fecha_fin": (date.today() + timedelta(days=5)).isoformat(),
    }

    resp = client.patch(f"/api/v1/roadmaps/tasks/{t_id}/details", json=body, headers=headers)
    assert resp.status_code == 422
    data = resp.json()
    assert data["code"] == "INVALID_DATE_RANGE"
    assert "fecha_fin anterior a fecha_inicio" in data["detail"]


def test_patch_task_details_rol_no_autorizado_403(seed_data):
    """Un usuario con rol distinto a 'implementador' (ej: 'coordinador') recibe 403."""
    t_id = seed_data["task_id"]
    headers = _headers(seed_data["user_otro"], seed_data["tenant_id"], "coordinador")

    body = {"titulo": "Intento no autorizado"}
    resp = client.patch(f"/api/v1/roadmaps/tasks/{t_id}/details", json=body, headers=headers)
    assert resp.status_code == 403


def test_patch_task_details_tenant_ajeno_404(seed_data):
    """Un implementador en tenant_ajeno intentando editar tarea de otro tenant recibe 404 (aislamiento RLS)."""
    t_id = seed_data["task_id"]
    headers = _headers(seed_data["user_impl"], seed_data["tenant_ajeno"], "implementador")

    body = {"titulo": "Intento en tenant ajeno"}
    resp = client.patch(f"/api/v1/roadmaps/tasks/{t_id}/details", json=body, headers=headers)
    assert resp.status_code == 404
