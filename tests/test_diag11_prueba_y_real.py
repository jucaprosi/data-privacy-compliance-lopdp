# ¤diagnostico ¤dpo-independencia ¤arbitro
"""DIAG-11: el diagnóstico se sella dos veces como máximo; el primero es de prueba y el segundo, el real.

Recorrido contra un PostgreSQL 16 de revisión (contenedor local o el servicio del CI, nunca producción):
- primer sello `prueba`, segundo `real` con las mismas respuestas, tercero 409 DIAG_SELLOS_AGOTADOS;
- guardar respuestas tras el real, por el router de respuestas, 409 DIAG_RESPUESTAS_CERRADAS;
- la cadena de huellas de DIAG-03 sigue íntegra;
- `diagnostico_real_sellado` del pasillo: falso antes del real, verdadero después y, con `lopdp_app`,
  no ve otra organización (RLS);
- la base rechaza una tercera secuencia aunque la aplicación no lo impida.

La identidad se inyecta sobreescribiendo `get_context` (lo que entrega el token verificado); no se usa
AUTH_MODE=headers. Sin TEST_DATABASE_URL las pruebas de base se omiten.

Mutación documentada: con el límite quitado en `sellar_resultado` (sin el `raise ErrorNegocio(SELLOS_AGOTADOS)`),
`test_primer_sello_prueba_segundo_real_tercero_409` falla: el tercer sello devuelve 500 (lo detiene el
disparador de la base) en vez de 409.
"""
import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_TEST_URL = os.environ.get("TEST_DATABASE_URL", "")
if _TEST_URL:
    os.environ["DATABASE_URL"] = _TEST_URL
else:
    os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://sin-base:sin-base@localhost:1/sin-base")

from features.diagnostico.services.resultados_engine import (  # noqa: E402
    SELLOS_MAXIMOS,
    etapa_por_sellos,
    tipo_de_secuencia,
)

RESPUESTAS = "/api/v1/diagnostico/respuestas"
RESULTADOS = "/api/v1/diagnostico/resultados"
ETAPA = "/api/v1/diagnostico/etapa"


# --- Sin base de datos ------------------------------------------------------------------------


def test_la_secuencia_fija_el_tipo_y_no_hay_tercero():
    assert SELLOS_MAXIMOS == 2
    assert (tipo_de_secuencia(1), tipo_de_secuencia(2)) == ("prueba", "real")
    with pytest.raises(ValueError):
        tipo_de_secuencia(3)


def test_etapa_por_cantidad_de_sellos():
    assert etapa_por_sellos(0) == {"etapa": None, "siguiente": "prueba"}
    assert etapa_por_sellos(1) == {"etapa": "prueba", "siguiente": "real"}
    assert etapa_por_sellos(2) == {"etapa": "real", "siguiente": None}


# --- Recorrido contra PostgreSQL --------------------------------------------------------------


def _url() -> str:
    return _TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1)


def _respuesta(pregunta_id: int = 1, nivel_asignado: int = 3) -> dict:
    return {
        "pregunta_id": pregunta_id, "control": "Control del banco", "dimension": "D01",
        "nivel_asignado": nivel_asignado, "nivel_evidencia": 1, "criticidad": 3, "es_critica": False,
        "riesgo_base": 5,
    }


@pytest_asyncio.fixture
async def ctx():
    if not _TEST_URL:
        pytest.skip("TEST_DATABASE_URL no configurada")
    from api.rbac import get_context
    from app_core.db.session import fijar_contexto_rls, get_session
    from main import app

    engine = create_async_engine(_url(), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    tenant, otro = f"diag11-{sufijo}", f"diag11-otro-{sufijo}"
    dpo = f"diag11-dpo-{sufijo}"
    async with factory() as s:
        for t in (tenant, otro):
            await s.execute(text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
                "VALUES (:t, :t, :t, :t, 'micro')"
            ), {"t": t})
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
        yield {"client": client, "factory": factory, "tenant": tenant, "otro": otro, "dpo": dpo}
    app.dependency_overrides.clear()

    async with factory() as s:
        for t in (tenant, otro):
            await fijar_contexto_rls(s, t)
            for borrado in (
                "DELETE FROM diagnostico_resultados WHERE tenant_id = :t",
                "DELETE FROM diagnostico_respuestas WHERE tenant_id = :t",
                "DELETE FROM audit_events WHERE tenant_id = :t",
            ):
                await s.execute(text(borrado), {"t": t})
            await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t})
        await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": dpo})
        await s.commit()
    await engine.dispose()


async def _real_sellado(factory, tenant: str, como_app: bool = False) -> bool:
    from app_core.pasillo import diagnostico as pasillo

    async with factory() as s:
        if como_app:
            await s.execute(text("SET LOCAL ROLE lopdp_app"))
        return await pasillo.diagnostico_real_sellado(s, tenant)


@pytest.mark.asyncio
async def test_primer_sello_prueba_segundo_real_tercero_409(ctx):
    c = ctx["client"]
    assert (await c.put(RESPUESTAS, json={"respuestas": [_respuesta(1)]})).status_code == 200
    assert (await c.get(ETAPA)).json() == {"etapa": None, "siguiente": "prueba"}

    primero = await c.post(RESULTADOS, json={"perfil": {}})
    assert primero.status_code == 201, primero.text
    assert (await c.get(ETAPA)).json() == {"etapa": "prueba", "siguiente": "real"}
    assert await _real_sellado(ctx["factory"], ctx["tenant"]) is False

    # Sin información nueva del administrador, el DPO sella el real igual al de prueba.
    segundo = await c.post(RESULTADOS, json={"perfil": {}})
    assert segundo.status_code == 201, segundo.text
    assert segundo.json()["huella_anterior"] == primero.json()["huella"]
    assert segundo.json()["respuestas"] == primero.json()["respuestas"]
    assert (await c.get(ETAPA)).json() == {"etapa": "real", "siguiente": None}

    tercero = await c.post(RESULTADOS, json={"perfil": {}})
    assert tercero.status_code == 409, tercero.text
    assert tercero.json()["code"] == "DIAG_SELLOS_AGOTADOS"

    historial = (await c.get(RESULTADOS)).json()
    assert len(historial["resultados"]) == 2 and historial["cadena_integra"] is True

    async with ctx["factory"]() as s:
        from app_core.db.session import fijar_contexto_rls

        await fijar_contexto_rls(s, ctx["tenant"])
        tipos = (await s.execute(text(
            "SELECT secuencia, tipo FROM diagnostico_resultados WHERE tenant_id = :t ORDER BY secuencia"
        ), {"t": ctx["tenant"]})).all()
    assert [tuple(f) for f in tipos] == [(1, "prueba"), (2, "real")]


@pytest.mark.asyncio
async def test_tras_el_real_guardar_respuestas_es_409(ctx):
    c = ctx["client"]
    await c.put(RESPUESTAS, json={"respuestas": [_respuesta(1)]})
    # Entre el de prueba y el real las respuestas siguen abiertas.
    assert (await c.post(RESULTADOS, json={"perfil": {}})).status_code == 201
    assert (await c.put(RESPUESTAS, json={"respuestas": [_respuesta(1, 4)]})).status_code == 200
    assert (await c.post(RESULTADOS, json={"perfil": {}})).status_code == 201

    r = await c.put(RESPUESTAS, json={"respuestas": [_respuesta(1, 5)]})
    assert r.status_code == 409, r.text
    assert r.json()["code"] == "DIAG_RESPUESTAS_CERRADAS"
    assert (await c.get(RESPUESTAS)).json()["respuestas"][0]["nivel_asignado"] == 4


@pytest.mark.asyncio
async def test_diagnostico_real_sellado_no_ve_otra_organizacion(ctx):
    c = ctx["client"]
    await c.put(RESPUESTAS, json={"respuestas": [_respuesta(1)]})
    await c.post(RESULTADOS, json={"perfil": {}})
    await c.post(RESULTADOS, json={"perfil": {}})

    assert await _real_sellado(ctx["factory"], ctx["tenant"], como_app=True) is True
    assert await _real_sellado(ctx["factory"], ctx["otro"], como_app=True) is False
    # Con el contexto de la otra organización, lopdp_app no ve las filas ajenas aunque las nombre.
    from app_core.db.session import fijar_contexto_rls

    async with ctx["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, ctx["otro"])
        ajenas = (await s.execute(text(
            "SELECT count(*) FROM diagnostico_resultados WHERE tenant_id = :t"
        ), {"t": ctx["tenant"]})).scalar_one()
    assert ajenas == 0


@pytest.mark.asyncio
async def test_la_base_rechaza_un_tercer_sello(ctx):
    c = ctx["client"]
    await c.put(RESPUESTAS, json={"respuestas": [_respuesta(1)]})
    await c.post(RESULTADOS, json={"perfil": {}})
    await c.post(RESULTADOS, json={"perfil": {}})
    from app_core.db.session import fijar_contexto_rls

    async with ctx["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, ctx["tenant"], ctx["dpo"])
        with pytest.raises(Exception, match="DIAG_SELLOS_AGOTADOS"):
            await s.execute(text(
                "INSERT INTO diagnostico_resultados (id, tenant_id, secuencia, sellado_por, sellado_en, normativa, "
                "version_normativa, tamano, perfil, respuestas, indicadores, huella_anterior, huella) VALUES "
                "(:id, :t, 3, :u, now(), 'LOPDP', 'v', 'micro', '{}', '[]', '{}', 'x', 'y')"
            ), {"id": str(uuid.uuid4()), "t": ctx["tenant"], "u": ctx["dpo"]})
