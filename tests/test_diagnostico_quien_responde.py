# ¤diagnostico ¤dpo-independencia ¤rbac-tenant ¤arbitro
"""DIAG-07: quién responde, quién objeta y cuándo se puede sellar.

Recorrido real contra PostgreSQL. Sin TEST_DATABASE_URL las pruebas se omiten. Solo valores generados y
correos `.invalid`. Esta primera parte cubre las objeciones (motor y RLS); las reglas de quién escribe y
el bloqueo del sello se añaden con el cambio de rol del router de respuestas.
"""
import os
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_TEST_URL = os.environ.get("TEST_DATABASE_URL")
if not _TEST_URL:
    pytest.skip("TEST_DATABASE_URL no configurada", allow_module_level=True)
os.environ["DATABASE_URL"] = _TEST_URL

from app_core.db.session import fijar_contexto_rls  # noqa: E402
from app_core.errors import ErrorNegocio  # noqa: E402
from features.diagnostico.services import objeciones_engine  # noqa: E402

pytestmark = pytest.mark.asyncio
MOTIVO = "La evidencia declarada no respalda el nivel indicado."


def _url() -> str:
    return _TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1)


@pytest_asyncio.fixture
async def ctx():
    engine = create_async_engine(_url(), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    a, b = f"obj-a-{sufijo}", f"obj-b-{sufijo}"
    async with factory() as s:
        for t in (a, b):
            await s.execute(text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:t, :t, :t, :t)"
            ), {"t": t})
        dpo = f"obj-dpo-{sufijo}"
        await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :u)"),
                        {"u": dpo, "e": f"{dpo}@example.invalid"})
        await s.commit()
    ctx_dpo = dpo
    yield {"factory": factory, "a": a, "b": b, "dpo": dpo, "sufijo": sufijo}
    async with factory() as s:
        for t in (a, b):
            await fijar_contexto_rls(s, t)
            await s.execute(text("DELETE FROM diagnostico_objeciones WHERE tenant_id = :t"), {"t": t})
        await s.execute(text("DELETE FROM audit_events WHERE tenant_id IN (:a, :b)"), {"a": a, "b": b})
        await s.execute(text("DELETE FROM tenants WHERE id IN (:a, :b)"), {"a": a, "b": b})
        await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": ctx_dpo})
        await s.commit()
    await engine.dispose()


async def test_objecion_unica(ctx):
    async with ctx["factory"]() as s:
        creada = await objeciones_engine.crear_objecion(s, ctx["a"], ctx["dpo"], 12, MOTIVO)
        assert creada["pregunta_id"] == 12 and creada["resuelta_en"] is None
        with pytest.raises(ErrorNegocio) as error:
            await objeciones_engine.crear_objecion(s, ctx["a"], ctx["dpo"], 12, MOTIVO)
        assert error.value.code == "OBJECION_DUPLICADA" and error.value.status_code == 409
        await s.rollback()


async def test_guardar_la_pregunta_resuelve_y_permite_objetar_de_nuevo(ctx):
    async with ctx["factory"]() as s:
        await objeciones_engine.crear_objecion(s, ctx["a"], ctx["dpo"], 12, MOTIVO)
        with pytest.raises(ErrorNegocio) as error:
            await objeciones_engine.exigir_sin_objeciones_abiertas(s, ctx["a"], ctx["dpo"])
        assert error.value.code == "OBJECIONES_ABIERTAS"
        assert await objeciones_engine.resolver_por_guardado(s, ctx["a"], ctx["dpo"], [11, 12]) == [12]
        await objeciones_engine.exigir_sin_objeciones_abiertas(s, ctx["a"], ctx["dpo"])
        await objeciones_engine.crear_objecion(s, ctx["a"], ctx["dpo"], 12, MOTIVO)
        historial = await objeciones_engine.listar_objeciones(s, ctx["a"], ctx["dpo"])
        assert len(historial) == 2
        assert len(await objeciones_engine.listar_objeciones(s, ctx["a"], ctx["dpo"], solo_abiertas=True)) == 1
        await s.commit()


async def test_el_motivo_corto_no_entra_en_la_base(ctx):
    async with ctx["factory"]() as s:
        with pytest.raises(Exception):
            await objeciones_engine.crear_objecion(s, ctx["a"], ctx["dpo"], 3, "muy corto")
        await s.rollback()


async def test_rls_objeciones(ctx):
    async with ctx["factory"]() as s:
        await objeciones_engine.crear_objecion(s, ctx["a"], ctx["dpo"], 12, MOTIVO)
        await s.commit()
    async with ctx["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, ctx["a"])
        assert (await s.execute(text("SELECT count(*) FROM diagnostico_objeciones"))).scalar_one() == 1
    async with ctx["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, ctx["b"])
        assert (await s.execute(text("SELECT count(*) FROM diagnostico_objeciones"))).scalar_one() == 0
        with pytest.raises(Exception):
            await s.execute(text(
                "INSERT INTO diagnostico_objeciones (id, tenant_id, pregunta_id, motivo, objetado_por) "
                "VALUES (:i, :a, 1, :m, 'x')"
            ), {"i": str(uuid.uuid4()), "a": ctx["a"], "m": MOTIVO})


# --- API: objetar y sellar ---------------------------------------------------------------------

OBJECIONES = "/api/v1/diagnostico/objeciones"
RESPUESTAS = "/api/v1/diagnostico/respuestas"
RESULTADOS = "/api/v1/diagnostico/resultados"


def _h(user: str, tenant: str, role: str) -> dict[str, str]:
    return {"X-User-ID": user, "X-Tenant-ID": tenant, "X-Role": role}


def _respuesta(pregunta_id: int) -> dict:
    return {
        "pregunta_id": pregunta_id, "control": "Control del banco", "dimension": "D01", "nivel_asignado": 4,
        "nivel_evidencia": 2, "criticidad": 3, "es_critica": False, "riesgo_base": 5,
    }


@pytest_asyncio.fixture
async def api(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    from httpx import ASGITransport, AsyncClient

    from app_core.db.session import get_session
    from main import app

    engine = create_async_engine(_url(), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    a = f"obj-api-{sufijo}"
    usuarios = {
        "dpo": (f"obj-dpo-{sufijo}", a, "dpo"),
        "admin": (f"obj-admin-{sufijo}", a, "admin_organizacion"),
        "impl": (f"obj-impl-{sufijo}", a, "implementador"),
        "coord": (f"obj-coord-{sufijo}", a, "coordinador"),
        "resp": (f"obj-resp-{sufijo}", a, "responsable_area"),
    }
    async with factory() as s:
        await s.execute(text(
            "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
            "VALUES (:t, :t, :t, :t, 'mediana')"
        ), {"t": a})
        for uid, tenant, rol in usuarios.values():
            await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :u)"),
                            {"u": uid, "e": f"{uid}@example.invalid"})
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
        yield {"client": client, "a": a, "u": usuarios}
    app.dependency_overrides.clear()
    async with factory() as s:
        await fijar_contexto_rls(s, a)
        for sentencia in (
            "DELETE FROM diagnostico_objeciones WHERE tenant_id = :t",
            "DELETE FROM diagnostico_resultados WHERE tenant_id = :t",
            "DELETE FROM diagnostico_respuestas WHERE tenant_id = :t",
            "DELETE FROM audit_events WHERE tenant_id = :t",
            "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
        ):
            await s.execute(text(sentencia), {"t": a})
        await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": a})
        await s.execute(text("DELETE FROM users WHERE id LIKE :p"), {"p": f"obj-%-{sufijo}"})
        await s.commit()
    await engine.dispose()


def _como(api, clave):
    uid, tenant, rol = api["u"][clave]
    return _h(uid, tenant, rol)


@pytest.mark.parametrize("clave", ["admin", "impl", "coord", "resp"])
async def test_solo_el_dpo_objeta(api, clave):
    r = await api["client"].post(OBJECIONES, headers=_como(api, clave), json={"pregunta_id": 12, "motivo": MOTIVO})
    assert r.status_code == 403


async def test_objetar_y_listar_por_api(api):
    c = api["client"]
    dpo = _como(api, "dpo")
    corto = await c.post(OBJECIONES, headers=dpo, json={"pregunta_id": 12, "motivo": "corto"})
    assert corto.status_code == 422
    r = await c.post(OBJECIONES, headers=dpo, json={"pregunta_id": 12, "motivo": MOTIVO})
    assert r.status_code == 201 and r.json()["resuelta_en"] is None
    repetida = await c.post(OBJECIONES, headers=dpo, json={"pregunta_id": 12, "motivo": MOTIVO})
    assert repetida.status_code == 409 and repetida.json()["code"] == "OBJECION_DUPLICADA"
    for lector in ("dpo", "admin", "impl", "coord", "resp"):
        filas = (await c.get(f"{OBJECIONES}?abiertas=true", headers=_como(api, lector))).json()["objeciones"]
        assert [f["pregunta_id"] for f in filas] == [12]


async def test_sello_sin_objeciones(api):
    c = api["client"]
    dpo = _como(api, "dpo")
    guardado = await c.put(RESPUESTAS, headers=dpo, json={"respuestas": [_respuesta(12)]})
    assert guardado.status_code == 200, guardado.text
    await c.post(OBJECIONES, headers=dpo, json={"pregunta_id": 12, "motivo": MOTIVO})

    bloqueado = await c.post(RESULTADOS, headers=dpo, json={"perfil": {}})
    assert bloqueado.status_code == 409 and bloqueado.json()["code"] == "OBJECIONES_ABIERTAS", bloqueado.text

    # El respondiente vuelve a guardar la 12: se resuelve la objeción y ya se puede sellar.
    from features.diagnostico import diagnostico_service
    from app_core.db.session import get_session
    from main import app

    async for sesion in app.dependency_overrides[get_session]():
        assert await diagnostico_service.resolver_por_guardado(sesion, api["a"], api["u"]["dpo"][0], [12]) == [12]
    sellado = await c.post(RESULTADOS, headers=dpo, json={"perfil": {}})
    assert sellado.status_code == 201, sellado.text
