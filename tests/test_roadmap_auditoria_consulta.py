# ¤roadmap ¤seguridad
"""Pruebas para RM-09: Consulta del registro de auditoría de Hoja de Ruta.

Endpoint: GET /api/v1/roadmaps/{roadmap_id}/audit-log
Roles autorizados: coordinador, dpo, implementador, admin_organizacion.
Roles prohibidos: responsable_area (u otros sin permiso) -> 403 Forbidden.
Aislamiento: Roadmap ajeno o inexistente -> 404 Not Found.
Paginación: limit y offset deterministas.
Invariante: Cero SQL interpolado.
"""
import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from main import app
from app_core.db.session import get_session
from features.roadmap import roadmap_service


def _async_url() -> str:
    import os
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@pytest_asyncio.fixture
async def db_session_factory():
    """Generador de sesiones contra la base de datos de test."""
    engine = create_async_engine(_async_url(), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        yield factory
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def api_client(db_session_factory):
    """Cliente HTTP asíncrono para probar el gateway FastAPI."""
    async def _test_get_session():
        async with db_session_factory() as session:
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
async def seed_data(db_session_factory):
    """Inserta datos de prueba: 2 tenants, usuarios con diversos roles, roadmap, wave, tasks y eventos de auditoría."""
    t1_id = f"t1-{uuid.uuid4().hex[:8]}"
    t2_id = f"t2-{uuid.uuid4().hex[:8]}"

    u_coord = f"u-coord-{uuid.uuid4().hex[:8]}"
    u_dpo = f"u-dpo-{uuid.uuid4().hex[:8]}"
    u_impl = f"u-imp-{uuid.uuid4().hex[:8]}"
    u_admin = f"u-adm-{uuid.uuid4().hex[:8]}"
    u_resp = f"u-resp-{uuid.uuid4().hex[:8]}"
    u_t2_impl = f"u-t2imp-{uuid.uuid4().hex[:8]}"

    rm1_id = f"rm-{uuid.uuid4().hex[:8]}"
    wave1_id = f"wv-{uuid.uuid4().hex[:8]}"
    task1_id = f"tsk-{uuid.uuid4().hex[:8]}"
    task2_id = f"tsk-{uuid.uuid4().hex[:8]}"

    async with db_session_factory() as session:
        # 1. Crear tenants
        await session.execute(
            text("""
                INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion)
                VALUES
                (:t1, 'Tenant 1', 'Tenant 1 S.A.', :ruc1),
                (:t2, 'Tenant 2', 'Tenant 2 S.A.', :ruc2)
            """),
            {
                "t1": t1_id, "ruc1": f"RUC{t1_id[:10]}",
                "t2": t2_id, "ruc2": f"RUC{t2_id[:10]}",
            },
        )
        # 2. Crear usuarios
        await session.execute(
            text("""
                INSERT INTO users (id, email, nombre) VALUES
                (:u1, :e1, 'Coordinador'),
                (:u2, :e2, 'DPO'),
                (:u3, :e3, 'Implementador'),
                (:u4, :e4, 'Admin'),
                (:u5, :e5, 'Responsable Area'),
                (:u6, :e6, 'Tenant 2 Imp')
            """),
            {
                "u1": u_coord, "e1": f"{u_coord}@test.local",
                "u2": u_dpo, "e2": f"{u_dpo}@test.local",
                "u3": u_impl, "e3": f"{u_impl}@test.local",
                "u4": u_admin, "e4": f"{u_admin}@test.local",
                "u5": u_resp, "e5": f"{u_resp}@test.local",
                "u6": u_t2_impl, "e6": f"{u_t2_impl}@test.local",
            },
        )
        # 3. Asignar roles (user_tenant_roles usa valid_to para caducidad; valid_to IS NULL es activo)
        await session.execute(
            text("""
                INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES
                (:r1, :u1, :t1, 'coordinador'),
                (:r2, :u2, :t1, 'dpo'),
                (:r3, :u3, :t1, 'implementador'),
                (:r4, :u4, :t1, 'admin_organizacion'),
                (:r5, :u5, :t1, 'responsable_area'),
                (:r6, :u6, :t2, 'implementador')
            """),
            {
                "r1": str(uuid.uuid4()), "u1": u_coord, "t1": t1_id,
                "r2": str(uuid.uuid4()), "u2": u_dpo, "t1": t1_id,
                "r3": str(uuid.uuid4()), "u3": u_impl, "t1": t1_id,
                "r4": str(uuid.uuid4()), "u4": u_admin, "t1": t1_id,
                "r5": str(uuid.uuid4()), "u5": u_resp, "t1": t1_id,
                "r6": str(uuid.uuid4()), "u6": u_t2_impl, "t2": t2_id,
            },
        )
        # 4. Crear roadmap, wave y tasks en tenant 1
        await session.execute(
            text("""
                INSERT INTO roadmaps (id, tenant_id, status, variables_json)
                VALUES (:rid, :tid, 'draft', '{}')
            """),
            {"rid": rm1_id, "tid": t1_id},
        )
        await session.execute(
            text("""
                INSERT INTO roadmap_waves (id, roadmap_id, tenant_id, name, sort_order)
                VALUES (:wid, :rid, :tid, 'Ola 1', 1)
            """),
            {"wid": wave1_id, "rid": rm1_id, "tid": t1_id},
        )
        await session.execute(
            text("""
                INSERT INTO roadmap_tasks (id, wave_id, tenant_id, title, control_ref, dimension, status, priority)
                VALUES
                (:t1, :wid, :tid, 'Tarea 1', 'P1', 'D01', 'pendiente', 'alta'),
                (:t2, :wid, :tid, 'Tarea 2', 'P2', 'D02', 'en_progreso', 'media')
            """),
            {"t1": task1_id, "t2": task2_id, "wid": wave1_id, "tid": t1_id},
        )

        # 5. Insertar 3 eventos de auditoría para las tareas
        await roadmap_service.registrar_auditoria(session, t1_id, u_impl, task1_id, "task_created", {"nota": "inicio"})
        await roadmap_service.registrar_auditoria(session, t1_id, u_impl, task1_id, "status_change", {"from": "pendiente", "to": "en_progreso"})
        await roadmap_service.registrar_auditoria(session, t1_id, u_impl, task2_id, "task_assigned", {"to_user": u_impl})

        await session.commit()

    return {
        "tenant_1": t1_id,
        "tenant_2": t2_id,
        "users": {
            "coordinador": u_coord,
            "dpo": u_dpo,
            "implementador": u_impl,
            "admin_organizacion": u_admin,
            "responsable_area": u_resp,
            "t2_implementador": u_t2_impl,
        },
        "roadmap_id": rm1_id,
        "task_ids": [task1_id, task2_id],
    }


@pytest.mark.asyncio
async def test_compuerta_roadmap_service(db_session_factory, seed_data):
    """Comprueba que la compuerta roadmap_service expone get_roadmap_audit_log y funciona a nivel de servicio."""
    assert hasattr(roadmap_service, "get_roadmap_audit_log")
    assert "get_roadmap_audit_log" in roadmap_service.__all__

    async with db_session_factory() as session:
        t1 = seed_data["tenant_1"]
        rm_id = seed_data["roadmap_id"]

        # Consulta válida
        res = await roadmap_service.get_roadmap_audit_log(session, t1, rm_id, limit=10, offset=0)
        assert res is not None
        assert res["total"] == 3
        assert len(res["items"]) == 3
        assert res["limit"] == 10
        assert res["offset"] == 0

        # Paginación
        res_pag = await roadmap_service.get_roadmap_audit_log(session, t1, rm_id, limit=2, offset=0)
        assert res_pag["total"] == 3
        assert len(res_pag["items"]) == 2

        res_offset = await roadmap_service.get_roadmap_audit_log(session, t1, rm_id, limit=2, offset=2)
        assert res_offset["total"] == 3
        assert len(res_offset["items"]) == 1

        # Tenant ajeno devuelve None
        t2 = seed_data["tenant_2"]
        res_t2 = await roadmap_service.get_roadmap_audit_log(session, t2, rm_id)
        assert res_t2 is None

        # Roadmap inexistente devuelve None
        res_inexistente = await roadmap_service.get_roadmap_audit_log(session, t1, "rm-inexistente")
        assert res_inexistente is None


@pytest.mark.asyncio
async def test_audit_log_rbac_roles_autorizados(api_client, seed_data):
    """Roles autorizados: coordinador, dpo, implementador, admin_organizacion pueden consultar (200 OK)."""
    t1 = seed_data["tenant_1"]
    rm_id = seed_data["roadmap_id"]
    roles_permitidos = ["coordinador", "dpo", "implementador", "admin_organizacion"]

    for rol in roles_permitidos:
        user_id = seed_data["users"][rol]
        headers = {
            "X-User-ID": user_id,
            "X-Tenant-ID": t1,
            "X-Role": rol,
        }
        resp = await api_client.get(f"/api/v1/roadmaps/{rm_id}/audit-log", headers=headers)
        assert resp.status_code == 200, f"Rol {rol} debe tener acceso, obtuvo {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
        assert "items" in data
        assert "limit" in data
        assert "offset" in data


@pytest.mark.asyncio
async def test_audit_log_rbac_roles_prohibidos(api_client, seed_data):
    """Roles no autorizados (responsable_area u otros) reciben 403 Forbidden."""
    t1 = seed_data["tenant_1"]
    rm_id = seed_data["roadmap_id"]
    user_id = seed_data["users"]["responsable_area"]

    headers = {
        "X-User-ID": user_id,
        "X-Tenant-ID": t1,
        "X-Role": "responsable_area",
    }
    resp = await api_client.get(f"/api/v1/roadmaps/{rm_id}/audit-log", headers=headers)
    assert resp.status_code == 403
    assert "no autorizado" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_audit_log_aislamiento_multitenant(api_client, seed_data):
    """Un usuario con rol implementador de otro tenant no puede consultar roadmap ajeno (404 Not Found)."""
    t2 = seed_data["tenant_2"]
    rm_id = seed_data["roadmap_id"]
    u_t2 = seed_data["users"]["t2_implementador"]

    headers = {
        "X-User-ID": u_t2,
        "X-Tenant-ID": t2,
        "X-Role": "implementador",
    }
    resp = await api_client.get(f"/api/v1/roadmaps/{rm_id}/audit-log", headers=headers)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Roadmap no encontrado"


@pytest.mark.asyncio
async def test_audit_log_roadmap_inexistente(api_client, seed_data):
    """Un roadmap inexistente devuelve 404 Not Found."""
    t1 = seed_data["tenant_1"]
    u_impl = seed_data["users"]["implementador"]

    headers = {
        "X-User-ID": u_impl,
        "X-Tenant-ID": t1,
        "X-Role": "implementador",
    }
    resp = await api_client.get("/api/v1/roadmaps/rm-inexistente-12345/audit-log", headers=headers)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Roadmap no encontrado"


@pytest.mark.asyncio
async def test_audit_log_paginacion(api_client, seed_data):
    """Comprueba parámetros limit y offset en el endpoint."""
    t1 = seed_data["tenant_1"]
    rm_id = seed_data["roadmap_id"]
    u_impl = seed_data["users"]["implementador"]

    headers = {
        "X-User-ID": u_impl,
        "X-Tenant-ID": t1,
        "X-Role": "implementador",
    }

    # limit=2, offset=0
    resp = await api_client.get(f"/api/v1/roadmaps/{rm_id}/audit-log?limit=2&offset=0", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 0

    # limit=2, offset=2
    resp_off = await api_client.get(f"/api/v1/roadmaps/{rm_id}/audit-log?limit=2&offset=2", headers=headers)
    assert resp_off.status_code == 200
    data_off = resp_off.json()
    assert data_off["total"] == 3
    assert len(data_off["items"]) == 1
    assert data_off["offset"] == 2
