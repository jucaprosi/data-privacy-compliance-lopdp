# ¤diagnostico ¤diagnostico-no-aplica ¤arbitro
"""DIAG-05: «no aplica» exige una justificación en el assessment.

Recorrido real contra un PostgreSQL 16 local en contenedor: sin justificación (o demasiado corta) es
422 y no se guarda nada; con ella, la justificación y su autor (el usuario de la identidad, nunca el
cuerpo) sobreviven a una sesión nueva. La base repite la regla con una restricción.

La identidad se inyecta sobreescribiendo `get_context` (lo que entrega el token verificado); no se
usa AUTH_MODE=headers. Sin TEST_DATABASE_URL las pruebas se omiten.

Mutación documentada: si `_validar_no_aplica` de respuestas_engine.py retorna sin comprobar, las pruebas
`test_no_aplica_sin_justificacion_es_422_y_no_guarda_nada` fallan en la API con 500 (la restricción
de la base lo rechaza) en vez de 422, y `test_la_base_rechaza_no_aplica_sin_justificacion` sigue en verde.
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

from api.rbac import get_context  # noqa: E402
from app_core.db.session import fijar_contexto_rls, get_session  # noqa: E402
from main import app  # noqa: E402

pytestmark = pytest.mark.asyncio
RUTA = "/api/v1/diagnostico/respuestas"
JUSTIFICACION = "La organización no trata datos de menores de edad"


def _url() -> str:
    return _TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1)


def _respuesta(pregunta_id: int = 1, **cambios) -> dict:
    base = {
        "pregunta_id": pregunta_id, "control": "Tratamiento de datos de menores", "dimension": "D03",
        "nivel_asignado": 1, "nivel_evidencia": 0, "criticidad": 3, "es_critica": False, "riesgo_base": 4,
    }
    return {**base, **cambios}


@pytest_asyncio.fixture
async def ctx():
    engine = create_async_engine(_url(), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    tenant = f"diag05-{sufijo}"
    dpo = f"diag05-dpo-{sufijo}"
    async with factory() as s:
        await s.execute(text(
            "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:t, :t, :t, :t)"
        ), {"t": tenant})
        await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :u)"),
                        {"u": dpo, "e": f"{dpo}@ejemplo.invalid"})
        await s.commit()

    identidad = {"user_id": dpo, "tenant_id": tenant, "role": "dpo"}

    async def session_override():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = session_override
    app.dependency_overrides[get_context] = lambda: dict(identidad)
    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test") as client:
        yield {"client": client, "factory": factory, "tenant": tenant, "dpo": dpo, "identidad": identidad}
    app.dependency_overrides.clear()

    async with factory() as s:
        await fijar_contexto_rls(s, tenant)
        await s.execute(text("DELETE FROM diagnostico_respuestas WHERE tenant_id = :t"), {"t": tenant})
        await s.execute(text("DELETE FROM audit_events WHERE tenant_id = :t"), {"t": tenant})
        await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": tenant})
        await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": dpo})
        await s.commit()
    await engine.dispose()


@pytest.mark.parametrize("justificacion", [None, "", "        ", "corta"])
async def test_no_aplica_sin_justificacion_es_422_y_no_guarda_nada(ctx, justificacion):
    c = ctx["client"]
    cuerpo = {"respuestas": [_respuesta(1), _respuesta(2, no_aplica=True, justificacion_no_aplica=justificacion)]}
    r = await _guardar(ctx, RUTA, cuerpo)
    assert r.status_code == 422, r.text
    assert r.json()["code"] == "DIAG_NO_APLICA_SIN_JUSTIFICACION"
    assert (await c.get(RUTA)).json()["respuestas"] == []

async def _guardar(ctx, ruta, cuerpo):
    """Siembra como administrador (DIAG-07b): cambia el rol de la identidad solo durante el PUT."""
    identidad = ctx["identidad"]
    antes = identidad["role"]
    identidad["role"] = "admin_organizacion"
    try:
        return await ctx["client"].put(ruta, json=cuerpo)
    finally:
        identidad["role"] = antes



async def test_no_aplica_justificado_sobrevive_a_una_sesion_nueva_con_su_autor(ctx):
    r = await _guardar(ctx, RUTA, {"respuestas": [
        _respuesta(7, no_aplica=True, justificacion_no_aplica=f"  {JUSTIFICACION}  ", justificado_por="otra-persona"),
    ]})
    # El autor no es una entrada: un campo extra en el cuerpo se rechaza.
    assert r.status_code == 422
    r = await _guardar(ctx, RUTA, {"respuestas": [
        _respuesta(7, no_aplica=True, justificacion_no_aplica=f"  {JUSTIFICACION}  "),
    ]})
    assert r.status_code == 200, r.text

    async with ctx["factory"]() as s:  # sesión nueva, sin la caché de la API
        await fijar_contexto_rls(s, ctx["tenant"])
        fila = (await s.execute(text(
            "SELECT no_aplica, justificacion_no_aplica, justificado_por, justificado_en "
            "FROM diagnostico_respuestas WHERE tenant_id = :t AND pregunta_id = 7"
        ), {"t": ctx["tenant"]})).mappings().one()
    assert fila["no_aplica"] is True
    assert fila["justificacion_no_aplica"] == JUSTIFICACION
    assert fila["justificado_por"] == ctx["dpo"]
    assert fila["justificado_en"] is not None

    leida = (await ctx["client"].get(RUTA)).json()["respuestas"][0]
    assert (leida["no_aplica"], leida["justificacion_no_aplica"], leida["justificado_por"]) == (True, JUSTIFICACION, ctx["dpo"])


async def test_quitar_no_aplica_borra_la_justificacion(ctx):
    c = ctx["client"]
    await _guardar(ctx, RUTA, {"respuestas": [_respuesta(3, no_aplica=True, justificacion_no_aplica=JUSTIFICACION)]})
    await _guardar(ctx, RUTA, {"respuestas": [_respuesta(3)]})
    leida = (await c.get(RUTA)).json()["respuestas"][0]
    assert (leida["no_aplica"], leida["justificacion_no_aplica"], leida["justificado_por"]) == (False, None, None)


async def test_la_base_rechaza_no_aplica_sin_justificacion(ctx):
    async with ctx["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, ctx["tenant"])
        with pytest.raises(Exception):
            await s.execute(text(
                "INSERT INTO diagnostico_respuestas (tenant_id, pregunta_id, control, dimension, estado, "
                "nivel_evidencia, criticidad, es_critica, riesgo_base, respondido_por, no_aplica) "
                "VALUES (:t, 9, 'Control', 'D01', 'No Conforme', 0, 3, false, 5, :u, true)"
            ), {"t": ctx["tenant"], "u": ctx["dpo"]})
