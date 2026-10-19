# ¤seguridad ¤rbac-tenant ¤evidencias
"""La API no entrega al responsable de área la evidencia que subió otra persona.

La matriz del PRD (Módulo 5, §5.2) dice que el `responsable_area` ve solo la evidencia que subió
él; el resto de roles ve toda la del tenant. Antes de SEC-04 solo la interfaz (FE-04) lo
ocultaba: quien llamara a `GET /roadmaps/tasks/{id}/evidence` recibía todo.

Las pruebas usan tenants y usuarios con identificadores propios en la base de pruebas y limpian
lo que crean.
"""
import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

pytestmark = pytest.mark.asyncio

ROLES_QUE_VEN_TODO = ["coordinador", "dpo", "implementador", "admin_organizacion"]


def _async_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _id(prefijo: str) -> str:
    return f"{prefijo}-{uuid.uuid4().hex[:10]}"


@pytest_asyncio.fixture
async def escenario():
    """Dos tenants. En el A: una tarea con tres evidencias de tres personas y un usuario por rol."""
    engine = create_async_engine(_async_url(), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    ta, tb = _id("sec04-a"), _id("sec04-b")
    usuarios = {rol: _id(f"u-{rol[:6]}") for rol in ["responsable_area", "coordinador", "dpo", "implementador", "admin_organizacion"]}
    usuarios["responsable_2"] = _id("u-resp2")
    usuarios["ajeno"] = _id("u-ajeno")
    roadmap, ola, tarea = _id("rm"), _id("wv"), _id("tk")
    ev = {"resp1": _id("ev-r1"), "resp2": _id("ev-r2"), "enc": _id("ev-enc"), "otro_tenant": _id("ev-b")}
    tarea_b = _id("tk-b")

    async with factory() as s:
        for t in (ta, tb):
            await s.execute(text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:i, :n, :r, :ruc)"
            ), {"i": t, "n": f"Org {t}", "r": f"Org {t} SA", "ruc": f"RUC{t[-12:]}"})
        for u in usuarios.values():
            await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:i, :e, :n)"),
                            {"i": u, "e": f"{u}@sec04.test", "n": u})
        for rol in ["responsable_area", "coordinador", "dpo", "implementador", "admin_organizacion"]:
            await s.execute(text(
                "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, :r)"
            ), {"i": _id("r"), "u": usuarios[rol], "t": ta, "r": rol})
        # Un segundo responsable de área del mismo tenant, y un responsable de otro tenant.
        await s.execute(text(
            "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, 'responsable_area')"
        ), {"i": _id("r"), "u": usuarios["responsable_2"], "t": ta})
        await s.execute(text(
            "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, 'responsable_area')"
        ), {"i": _id("r"), "u": usuarios["ajeno"], "t": tb})

        for t, rm, wv, tk in ((ta, roadmap, ola, tarea), (tb, _id("rm-b"), _id("wv-b"), tarea_b)):
            await s.execute(text(
                "INSERT INTO roadmaps (id, tenant_id, status, variables_json) VALUES (:i, :t, 'active', '{}')"
            ), {"i": rm, "t": t})
            await s.execute(text(
                "INSERT INTO roadmap_waves (id, roadmap_id, tenant_id, name, sort_order) VALUES (:i, :rm, :t, 'Ola', 1)"
            ), {"i": wv, "rm": rm, "t": t})
            await s.execute(text(
                "INSERT INTO roadmap_tasks (id, wave_id, tenant_id, control_ref, dimension, title, description, priority, status) "
                "VALUES (:i, :w, :t, 'P1', 'D01', 'Tarea', 'Desc', 'alta', 'pendiente')"
            ), {"i": tk, "w": wv, "t": t})

        def evidencia(eid, tenant, task, subida_por, archivo):
            return s.execute(text(
                "INSERT INTO task_evidence (id, task_id, tenant_id, r2_key, mime_type, file_size, uploaded_by, validation_status) "
                "VALUES (:i, :tk, :t, :k, 'application/pdf', 100, :u, 'pending')"
            ), {"i": eid, "tk": task, "t": tenant, "k": f"{tenant}/{task}/{archivo}", "u": subida_por})

        await evidencia(ev["resp1"], ta, tarea, usuarios["responsable_area"], "a.pdf")
        await evidencia(ev["resp2"], ta, tarea, usuarios["responsable_2"], "b.pdf")
        await evidencia(ev["enc"], ta, tarea, usuarios["coordinador"], "c.pdf")
        await evidencia(ev["otro_tenant"], tb, tarea_b, usuarios["ajeno"], "d.pdf")
        await s.commit()

    yield {"tenant": ta, "tenant_b": tb, "usuarios": usuarios, "tarea": tarea, "tarea_b": tarea_b, "ev": ev}

    async with factory() as s:
        try:
            for t in (ta, tb):
                await s.execute(text("DELETE FROM task_audit_log WHERE tenant_id = :t"), {"t": t})
                await s.execute(text("DELETE FROM task_evidence WHERE tenant_id = :t"), {"t": t})
                await s.execute(text("DELETE FROM roadmap_tasks WHERE tenant_id = :t"), {"t": t})
                await s.execute(text("DELETE FROM roadmap_waves WHERE tenant_id = :t"), {"t": t})
                await s.execute(text("DELETE FROM roadmaps WHERE tenant_id = :t"), {"t": t})
                await s.execute(text("DELETE FROM user_tenant_roles WHERE tenant_id = :t"), {"t": t})
                await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t})
            await s.execute(text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": list(usuarios.values())})
            await s.commit()
        except Exception:
            await s.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def cliente():
    from app_core.db.session import get_session
    from main import app

    engine = create_async_engine(_async_url(), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def _sesion():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    # Se restaura lo que había: otros módulos de prueba registran overrides al importarse.
    anteriores = dict(app.dependency_overrides)
    app.dependency_overrides[get_session] = _sesion
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
    app.dependency_overrides.update(anteriores)
    await engine.dispose()


def _cab(usuario, tenant, rol):
    return {"X-User-ID": usuario, "X-Tenant-ID": tenant, "X-Role": rol}


async def _ids_vistos(cliente, e, usuario, rol, tenant=None, tarea=None):
    r = await cliente.get(
        f"/api/v1/roadmaps/tasks/{tarea or e['tarea']}/evidence",
        headers=_cab(usuario, tenant or e["tenant"], rol),
    )
    assert r.status_code == 200, r.text
    return {fila["id"] for fila in r.json()}


async def test_responsable_de_area_ve_solo_la_evidencia_que_subio(cliente, escenario):
    e = escenario
    vistos = await _ids_vistos(cliente, e, e["usuarios"]["responsable_area"], "responsable_area")
    assert vistos == {e["ev"]["resp1"]}


async def test_cada_responsable_de_area_ve_la_suya_y_no_la_del_otro(cliente, escenario):
    """Distingue «filtrar por usuario» de «ocultar todo a los responsables» o de filtrar por rol."""
    e = escenario
    vistos = await _ids_vistos(cliente, e, e["usuarios"]["responsable_2"], "responsable_area")
    assert vistos == {e["ev"]["resp2"]}


@pytest.mark.parametrize("rol", ROLES_QUE_VEN_TODO)
async def test_los_demas_roles_ven_toda_la_evidencia_del_tenant(cliente, escenario, rol):
    e = escenario
    vistos = await _ids_vistos(cliente, e, e["usuarios"][rol], rol)
    assert vistos == {e["ev"]["resp1"], e["ev"]["resp2"], e["ev"]["enc"]}


async def test_la_evidencia_de_otro_tenant_nunca_aparece(cliente, escenario):
    """Ni siquiera para un rol que lo ve todo: el aislamiento por tenant no se rompe con el filtro."""
    e = escenario
    vistos = await _ids_vistos(cliente, e, e["usuarios"]["implementador"], "implementador")
    assert e["ev"]["otro_tenant"] not in vistos
    # Un responsable de área de OTRO tenant que pide la tarea de este no recibe nada.
    ajeno = await _ids_vistos(cliente, e, e["usuarios"]["ajeno"], "responsable_area", tenant=e["tenant_b"])
    assert ajeno == set()


async def test_el_filtro_falla_cerrado_si_falta_el_usuario():
    """Un responsable de área sin identidad de usuario no recibe «todo»: recibe nada."""
    from features.roadmap.roadmap_service import list_evidence

    engine = create_async_engine(_async_url(), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with factory() as session:
            assert await list_evidence(session, "tenant-inexistente", "tarea-x", rol="responsable_area", user_id=None) == []
    finally:
        await engine.dispose()


async def test_llamar_sin_rol_conserva_el_comportamiento_anterior(escenario):
    """Los llamadores internos con tres argumentos siguen recibiendo toda la evidencia del tenant."""
    from features.roadmap.roadmap_service import list_evidence

    e = escenario
    engine = create_async_engine(_async_url(), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with factory() as session:
            filas = await list_evidence(session, e["tenant"], e["tarea"])
        assert {f["id"] for f in filas} == {e["ev"]["resp1"], e["ev"]["resp2"], e["ev"]["enc"]}
    finally:
        await engine.dispose()
