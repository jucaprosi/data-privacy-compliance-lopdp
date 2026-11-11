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
