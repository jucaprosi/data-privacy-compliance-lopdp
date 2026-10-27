# ¤diagnostico ¤rbac-tenant ¤arbitro
"""DIAG-01: las respuestas del diagnóstico se guardan en el servidor, por organización.

Desde DIAG-03 solo el DPO responde; implementador, coordinador y administrador consultan.

Recorrido real contra PostgreSQL (rama Neon de revisión): guardar, leer desde otro usuario de
la misma organización, aislamiento entre organizaciones por la API y por RLS, permisos y
catálogo. Sin TEST_DATABASE_URL las pruebas se omiten.
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
RUTA = "/api/v1/diagnostico/respuestas"


def _url() -> str:
    return _TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1)


def _h(user: str, tenant: str, role: str) -> dict[str, str]:
    return {"X-User-ID": user, "X-Tenant-ID": tenant, "X-Role": role}


def _respuesta(pregunta_id: int = 1, **cambios) -> dict:
    base = {
        "pregunta_id": pregunta_id, "control": "Política de protección de datos personales", "dimension": "D01", "estado": "Parcial",
        "nivel_evidencia": 2, "criticidad": 4, "es_critica": True, "riesgo_base": 7,
    }
    return {**base, **cambios}


@pytest_asyncio.fixture
async def ctx(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    engine = create_async_engine(_url(), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    a, b = f"diag-a-{sufijo}", f"diag-b-{sufijo}"
    usuarios = {
        "impl": (f"diag-impl-{sufijo}", a, "implementador"),
        "dpo": (f"diag-dpo-{sufijo}", a, "dpo"),
        "resp": (f"diag-resp-{sufijo}", a, "responsable_area"),
        "impl_b": (f"diag-implb-{sufijo}", b, "implementador"),
    }
    async with factory() as s:
        for t in (a, b):
            await s.execute(text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:t, :t, :t, :t)"
            ), {"t": t})
        for uid, tenant, rol in usuarios.values():
            await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :u)"),
                            {"u": uid, "e": f"{uid}@example.test"})
            await s.execute(text(
                "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, :r)"
            ), {"i": str(uuid.uuid4()), "u": uid, "t": tenant, "r": rol})
        await s.commit()

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
            await s.execute(text("DELETE FROM diagnostico_respuestas WHERE tenant_id = :t"), {"t": t})
        await s.execute(text("DELETE FROM audit_events WHERE tenant_id IN (:a, :b)"), {"a": a, "b": b})
        await s.execute(text("DELETE FROM user_tenant_roles WHERE tenant_id IN (:a, :b)"), {"a": a, "b": b})
        await s.execute(text("DELETE FROM tenants WHERE id IN (:a, :b)"), {"a": a, "b": b})
        await s.execute(text("DELETE FROM users WHERE id LIKE :p"), {"p": f"diag-%-{sufijo}"})
        await s.commit()
    await engine.dispose()


def _como(ctx, clave):
    uid, tenant, rol = ctx["u"][clave]
    return _h(uid, tenant, rol)


async def test_lo_que_responde_el_dpo_lo_lee_el_implementador(ctx):
    c = ctx["client"]
    r = await c.put(RUTA, headers=_como(ctx, "dpo"), json={"respuestas": [_respuesta(1), _respuesta(2, control="Plan de capacitación", dimension="D10")]})
    assert r.status_code == 200, r.text

    leidas = (await c.get(RUTA, headers=_como(ctx, "impl"))).json()["respuestas"]
    assert [(x["pregunta_id"], x["control"], x["dimension"]) for x in leidas] == [
        (1, "Política de protección de datos personales", "D01"), (2, "Plan de capacitación", "D10")]
    primera = leidas[0]
    assert (primera["estado"], primera["nivel_evidencia"], primera["criticidad"], primera["es_critica"], primera["riesgo_base"]) == ("Parcial", 2, 4, True, 7)
    assert primera["respondido_por"] == ctx["u"]["dpo"][0]


async def test_volver_a_responder_reemplaza_la_respuesta_y_deja_un_evento(ctx):
    c = ctx["client"]
    await c.put(RUTA, headers=_como(ctx, "dpo"), json={"respuestas": [_respuesta(5)]})
    await c.put(RUTA, headers=_como(ctx, "dpo"), json={"respuestas": [_respuesta(5, estado="Conforme", nivel_evidencia=3)]})

    leidas = (await c.get(RUTA, headers=_como(ctx, "impl"))).json()["respuestas"]
    assert len(leidas) == 1 and leidas[0]["estado"] == "Conforme" and leidas[0]["nivel_evidencia"] == 3
    async with ctx["factory"]() as s:
        eventos = (await s.execute(text(
            "SELECT count(*) FROM audit_events WHERE tenant_id = :t AND action = 'diagnostico_respuestas_guardadas'"
        ), {"t": ctx["a"]})).scalar_one()
    assert eventos == 2


async def test_otra_organizacion_no_ve_las_respuestas(ctx):
    c = ctx["client"]
    await c.put(RUTA, headers=_como(ctx, "dpo"), json={"respuestas": [_respuesta(1)]})
    assert (await c.get(RUTA, headers=_como(ctx, "impl_b"))).json()["respuestas"] == []


async def test_rls_oculta_las_filas_aunque_la_consulta_no_filtre(ctx):
    await ctx["client"].put(RUTA, headers=_como(ctx, "dpo"), json={"respuestas": [_respuesta(1)]})
    async with ctx["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, ctx["b"])
        assert (await s.execute(text("SELECT count(*) FROM diagnostico_respuestas"))).scalar_one() == 0


async def test_rls_impide_escribir_en_otra_organizacion(ctx):
    async with ctx["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, ctx["b"])
        with pytest.raises(Exception):
            await s.execute(text(
                "INSERT INTO diagnostico_respuestas (tenant_id, pregunta_id, control, dimension, estado, "
                "nivel_evidencia, criticidad, es_critica, riesgo_base, respondido_por) "
                "VALUES (:a, 1, 'Control', 'D01', 'Parcial', 1, 3, false, 5, :u)"
            ), {"a": ctx["a"], "u": ctx["u"]["impl_b"][0]})


@pytest.mark.parametrize("clave, metodo", [("resp", "get"), ("resp", "put"), ("impl", "put")])
async def test_roles_sin_permiso_reciben_403(ctx, clave, metodo):
    c = ctx["client"]
    if metodo == "get":
        r = await c.get(RUTA, headers=_como(ctx, clave))
    else:
        r = await c.put(RUTA, headers=_como(ctx, clave), json={"respuestas": [_respuesta(1)]})
    assert r.status_code == 403


@pytest.mark.parametrize("cambio", [
    {"dimension": "D11"}, {"dimension": "D1"}, {"dimension": "D00"}, {"control": "   "},
])
async def test_fuera_de_catalogo_es_422_y_no_guarda_nada(ctx, cambio):
    c = ctx["client"]
    r = await c.put(RUTA, headers=_como(ctx, "dpo"), json={"respuestas": [_respuesta(1), _respuesta(2, **cambio)]})
    assert r.status_code == 422
    assert (await c.get(RUTA, headers=_como(ctx, "dpo"))).json()["respuestas"] == []
