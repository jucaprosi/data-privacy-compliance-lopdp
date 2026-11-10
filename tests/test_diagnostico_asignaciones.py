# ¤diagnostico ¤diagnostico-asignacion ¤rbac-tenant ¤arbitro
"""DIAG-04: el administrador asigna los dominios (D01-D10) a encargados del diagnóstico.

Recorrido real contra PostgreSQL: encargado válido, vigente = última, permisos, RLS y auditoría.
Sin TEST_DATABASE_URL las pruebas se omiten. Solo valores generados y correos `.invalid`.
"""
import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_TEST_URL = os.environ.get("TEST_DATABASE_URL")
if not _TEST_URL:
    pytest.skip("TEST_DATABASE_URL no configurada", allow_module_level=True)
os.environ["DATABASE_URL"] = _TEST_URL

from app_core.db.session import fijar_contexto_rls, get_session  # noqa: E402
from main import app  # noqa: E402

pytestmark = pytest.mark.asyncio
RUTA = "/api/v1/diagnostico/asignaciones"


def _url() -> str:
    return _TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1)


def _h(user: str, tenant: str, role: str) -> dict[str, str]:
    return {"X-User-ID": user, "X-Tenant-ID": tenant, "X-Role": role}


@pytest_asyncio.fixture
async def ctx(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    engine = create_async_engine(_url(), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    a, b = f"asig-a-{sufijo}", f"asig-b-{sufijo}"
    usuarios = {
        "admin": (f"asig-admin-{sufijo}", a, "admin_organizacion"),
        "dpo": (f"asig-dpo-{sufijo}", a, "dpo"),
        "coord": (f"asig-coord-{sufijo}", a, "coordinador"),
        "impl": (f"asig-impl-{sufijo}", a, "implementador"),
        "resp": (f"asig-resp-{sufijo}", a, "responsable_area"),
        "admin_b": (f"asig-adminb-{sufijo}", b, "admin_organizacion"),
    }
    sin_rol = f"asig-sinrol-{sufijo}"
    async with factory() as s:
        for t in (a, b):
            await s.execute(text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:t, :t, :t, :t)"
            ), {"t": t})
        for uid, tenant, rol in usuarios.values():
            await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :u)"),
                            {"u": uid, "e": f"{uid}@example.invalid"})
            await s.execute(text(
                "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, :r)"
            ), {"i": str(uuid.uuid4()), "u": uid, "t": tenant, "r": rol})
        await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :u)"),
                        {"u": sin_rol, "e": f"{sin_rol}@example.invalid"})
        await s.commit()
    usuarios["sin_rol"] = (sin_rol, a, "admin_organizacion")

    async def session_override():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = session_override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield {"client": client, "factory": factory, "a": a, "b": b, "u": usuarios}
    app.dependency_overrides.clear()

    async with factory() as s:
        for t in (a, b):
            await fijar_contexto_rls(s, t)
            await s.execute(text("DELETE FROM diagnostico_asignaciones WHERE tenant_id = :t"), {"t": t})
        await s.execute(text("DELETE FROM audit_events WHERE tenant_id IN (:a, :b)"), {"a": a, "b": b})
        await s.execute(text("DELETE FROM user_tenant_roles WHERE tenant_id IN (:a, :b)"), {"a": a, "b": b})
        await s.execute(text("DELETE FROM tenants WHERE id IN (:a, :b)"), {"a": a, "b": b})
        await s.execute(text("DELETE FROM users WHERE id LIKE :p"), {"p": f"asig-%-{sufijo}"})
        await s.commit()
    await engine.dispose()


def _como(ctx, clave):
    uid, tenant, rol = ctx["u"][clave]
    return _h(uid, tenant, rol)


async def test_asignacion_exige_encargado(ctx):
    c = ctx["client"]
    sin_rol = await c.put(f"{RUTA}/D04", headers=_como(ctx, "admin"), json={"responsable_user_id": ctx["u"]["sin_rol"][0]})
    assert sin_rol.status_code == 422 and sin_rol.json()["code"] == "ENCARGADO_SIN_ROL", sin_rol.text
    dpo = await c.put(f"{RUTA}/D04", headers=_como(ctx, "admin"), json={"responsable_user_id": ctx["u"]["dpo"][0]})
    assert dpo.status_code == 422 and dpo.json()["code"] == "ENCARGADO_ES_DPO", dpo.text
    ok = await c.put(f"{RUTA}/D04", headers=_como(ctx, "admin"), json={"responsable_user_id": ctx["u"]["impl"][0]})
    assert ok.status_code == 200 and ok.json()["responsable_user_id"] == ctx["u"]["impl"][0]
    otra_org = await c.put(f"{RUTA}/D04", headers=_como(ctx, "admin"), json={"responsable_user_id": ctx["u"]["admin_b"][0]})
    assert otra_org.status_code == 422 and otra_org.json()["code"] == "ENCARGADO_SIN_ROL"


async def test_asignacion_vigente_es_ultima(ctx):
    c = ctx["client"]
    primero, segundo = ctx["u"]["impl"][0], ctx["u"]["coord"][0]
    await c.put(f"{RUTA}/D04", headers=_como(ctx, "admin"), json={"responsable_user_id": primero})
    await c.put(f"{RUTA}/D04", headers=_como(ctx, "admin"), json={"responsable_user_id": segundo})

    filas = (await c.get(RUTA, headers=_como(ctx, "coord"))).json()["asignaciones"]
    assert [f["dimension"] for f in filas] == [f"D{i:02d}" for i in range(1, 11)]
    d04 = next(f for f in filas if f["dimension"] == "D04")
    assert d04["responsable_user_id"] == segundo and d04["nombre_dimension"]
    assert all(f["responsable_user_id"] is None for f in filas if f["dimension"] != "D04")

    historial = (await c.get(f"{RUTA}/historial?dimension=D04", headers=_como(ctx, "dpo"))).json()["historial"]
    assert [h["responsable_user_id"] for h in historial] == [segundo, primero]

    await c.put(f"{RUTA}/D04", headers=_como(ctx, "admin"), json={"responsable_user_id": None})
    filas = (await c.get(RUTA, headers=_como(ctx, "dpo"))).json()["asignaciones"]
    assert next(f for f in filas if f["dimension"] == "D04")["responsable_user_id"] is None
    async with ctx["factory"]() as s:
        acciones = (await s.execute(text(
            "SELECT action FROM audit_events WHERE tenant_id = :t AND entity_type = 'diagnostico_asignacion' "
            "ORDER BY timestamp, id"
        ), {"t": ctx["a"]})).scalars().all()
    assert acciones == ["asignada", "asignada", "desasignada"]


@pytest.mark.parametrize("clave", ["dpo", "coord", "impl", "resp"])
async def test_solo_admin_asigna(ctx, clave):
    c = ctx["client"]
    r = await c.put(f"{RUTA}/D01", headers=_como(ctx, clave), json={"responsable_user_id": ctx["u"]["impl"][0]})
    assert r.status_code == 403
    for lector in ("dpo", "coord", "impl"):
        assert (await c.get(RUTA, headers=_como(ctx, lector))).status_code == 200
    assert (await c.get(f"{RUTA}/historial", headers=_como(ctx, "resp"))).status_code == 403


@pytest.mark.parametrize("dimension", ["D00", "D11", "G01", "d04"])
async def test_dimension_fuera_de_catalogo_es_422(ctx, dimension):
    r = await ctx["client"].put(f"{RUTA}/{dimension}", headers=_como(ctx, "admin"),
                                json={"responsable_user_id": ctx["u"]["impl"][0]})
    assert r.status_code == 422


async def test_rls_asignaciones(ctx):
    await ctx["client"].put(f"{RUTA}/D02", headers=_como(ctx, "admin"), json={"responsable_user_id": ctx["u"]["impl"][0]})
    async with ctx["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, ctx["a"])
        assert (await s.execute(text("SELECT count(*) FROM diagnostico_asignaciones"))).scalar_one() == 1
    async with ctx["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, ctx["b"])
        assert (await s.execute(text("SELECT count(*) FROM diagnostico_asignaciones"))).scalar_one() == 0
    filas = (await ctx["client"].get(RUTA, headers=_como(ctx, "admin_b"))).json()["asignaciones"]
    assert all(f["responsable_user_id"] is None for f in filas)
    async with ctx["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, ctx["b"])
        with pytest.raises(Exception):
            await s.execute(text(
                "INSERT INTO diagnostico_asignaciones (id, tenant_id, dimension, asignado_por) VALUES (:i, :a, 'D01', 'x')"
            ), {"i": str(uuid.uuid4()), "a": ctx["a"]})
