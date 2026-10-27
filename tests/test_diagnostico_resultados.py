# ¤diagnostico ¤dpo-independencia ¤rbac-tenant ¤arbitro
"""DIAG-03: el DPO responde y sella el diagnóstico; el resultado sellado no se edita ni se borra.

La paridad de indicadores es una prueba pura: con los casos de frontend/tests/diagnostico/paridad.json
el servidor debe dar los mismos cuatro indicadores que el tablero de la pantalla (paridad.spec.ts
compara el otro lado contra los mismos valores). El resto recorre PostgreSQL real (rama Neon de
desarrollo o la rama test del CI, nunca producción); sin TEST_DATABASE_URL se omite.

Prueba de mutación ejecutada en la rama Neon rama-diag-03:
- En api/routers/diagnostico_resultados.py se cambió ROLES_SELLO = ("dpo",) por
  ("dpo", "implementador").
- pytest tests/test_diagnostico_resultados.py::test_solo_el_dpo_sella devolvió 1
  (FAILED test_solo_el_dpo_sella[impl]: assert 201 == 403; los otros tres roles siguieron en 403).
- Se restauró ROLES_SELLO; sin la mutación la prueba pasa.
"""
import json
import os
import uuid
from dataclasses import asdict
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_TEST_URL = os.environ.get("TEST_DATABASE_URL", "")
if _TEST_URL:
    os.environ["DATABASE_URL"] = _TEST_URL
else:
    os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://sin-base:sin-base@localhost:1/sin-base")

from features.diagnostico.services.engine import cargar_banco_preguntas_raw  # noqa: E402
from features.diagnostico.services.resultados_engine import (  # noqa: E402
    calcular_indicadores,
    controles_aplicables,
    normalizar_perfil,
)

PARIDAD = Path(__file__).resolve().parents[1] / "frontend" / "tests" / "diagnostico" / "paridad.json"
CASOS_PARIDAD = json.loads(PARIDAD.read_text(encoding="utf-8"))["casos"]
RESPUESTAS = "/api/v1/diagnostico/respuestas"
RESULTADOS = "/api/v1/diagnostico/resultados"


# --- Paridad con la pantalla (sin base de datos) ----------------------------------------------


@pytest.mark.parametrize("caso", CASOS_PARIDAD, ids=[c["nombre"] for c in CASOS_PARIDAD])
def test_paridad_de_indicadores_con_la_pantalla(caso):
    aplicables = controles_aplicables(cargar_banco_preguntas_raw(), caso["tamano"], normalizar_perfil(caso["perfil"]))
    guardadas = [{**r, "control": "", "dimension": "D01"} for r in caso["respuestas"]]
    indicadores, _ = calcular_indicadores(aplicables, guardadas, set(caso["controles_con_documento"]))
    assert asdict(indicadores) == caso["esperado"]


def test_un_control_sin_documento_comprobable_se_sella_como_e0():
    aplicables = controles_aplicables(cargar_banco_preguntas_raw(), "corporativo", normalizar_perfil({}))
    guardadas = [{"pregunta_id": 1, "estado": "Conforme", "nivel_evidencia": 3, "control": "", "dimension": "D01"}]
    _, sin_documento = calcular_indicadores(aplicables, guardadas, set())
    _, con_documento = calcular_indicadores(aplicables, guardadas, {1})
    assert (sin_documento[0].nivel_declarado, sin_documento[0].nivel_sellado) == (3, 0)
    assert (con_documento[0].nivel_declarado, con_documento[0].nivel_sellado) == (3, 3)


# --- Recorrido contra PostgreSQL ----------------------------------------------------------------


def _h(user: str, tenant: str, role: str) -> dict[str, str]:
    return {"X-User-ID": user, "X-Tenant-ID": tenant, "X-Role": role}


def _respuesta(pregunta_id: int, estado: str = "Conforme", nivel: int = 2) -> dict:
    return {
        "pregunta_id": pregunta_id, "control": "Control del banco", "dimension": "D01", "estado": estado,
        "nivel_evidencia": nivel, "criticidad": 3, "es_critica": False, "riesgo_base": 5,
    }


@pytest_asyncio.fixture
async def ctx(monkeypatch):
    if not _TEST_URL:
        pytest.skip("TEST_DATABASE_URL no configurada")
    # Rama de desarrollo o la rama test del CI, nunca producción.
    assert "ep-late-hall" not in _TEST_URL, "Se requiere una rama de desarrollo o test (nunca producción)"
    monkeypatch.setenv("AUTH_MODE", "headers")
    from app_core.db.session import fijar_contexto_rls, get_session
    from features.evidencias import evidencias_service
    from main import app

    engine = create_async_engine(_TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    a, b, c = (f"diag3-{x}-{sufijo}" for x in "abc")
    usuarios = {
        "dpo": (f"diag3-dpo-{sufijo}", a, "dpo"),
        "impl": (f"diag3-impl-{sufijo}", a, "implementador"),
        "coord": (f"diag3-coord-{sufijo}", a, "coordinador"),
        "admin": (f"diag3-admin-{sufijo}", a, "admin_organizacion"),
        "resp": (f"diag3-resp-{sufijo}", a, "responsable_area"),
        "dpo_b": (f"diag3-dpob-{sufijo}", b, "dpo"),
        "impl_c": (f"diag3-implc-{sufijo}", c, "implementador"),
    }
    async with factory() as s:
        # a: mediana; b: sin tamaño configurado; c: sin DPO.
        for tenant, tamano in ((a, "mediana"), (b, None), (c, "micro")):
            await s.execute(text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
                "VALUES (:t, :t, :t, :t, :tamano)"
            ), {"t": tenant, "tamano": tamano})
        for uid, tenant, rol in usuarios.values():
            await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :u)"),
                            {"u": uid, "e": f"{uid}@example.test"})
            await fijar_contexto_rls(s, tenant, uid)
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
    evidencias_service.reiniciar_repositorio_evidencias()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield {"client": client, "factory": factory, "a": a, "b": b, "c": c, "u": usuarios}
    finally:
        app.dependency_overrides.clear()
        evidencias_service.reiniciar_repositorio_evidencias()
        async with factory() as s:
            for t in (a, b, c):
                await fijar_contexto_rls(s, t)
                for sentencia in (
                    "DELETE FROM diagnostico_resultados WHERE tenant_id = :t",
                    "DELETE FROM diagnostico_respuestas WHERE tenant_id = :t",
                    "DELETE FROM audit_events WHERE tenant_id = :t",
                    "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
                ):
                    await s.execute(text(sentencia), {"t": t})
                await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t})
            await s.execute(text("DELETE FROM users WHERE id LIKE :p"), {"p": f"diag3-%-{sufijo}"})
            await s.commit()
        await engine.dispose()


def _como(ctx, clave):
    uid, tenant, rol = ctx["u"][clave]
    return _h(uid, tenant, rol)


async def _responder(ctx, *respuestas):
    r = await ctx["client"].put(RESPUESTAS, headers=_como(ctx, "dpo"), json={"respuestas": list(respuestas)})
    assert r.status_code == 200, r.text


@pytest.mark.parametrize("clave", ["impl", "coord", "admin", "resp"])
@pytest.mark.asyncio
async def test_solo_el_dpo_sella(ctx, clave):
    await _responder(ctx, _respuesta(1))
    r = await ctx["client"].post(RESULTADOS, headers=_como(ctx, clave), json={"perfil": {}})
    assert r.status_code == 403, r.text


@pytest.mark.parametrize("clave", ["impl", "coord", "admin"])
@pytest.mark.asyncio
async def test_solo_el_dpo_responde(ctx, clave):
    r = await ctx["client"].put(RESPUESTAS, headers=_como(ctx, clave), json={"respuestas": [_respuesta(1)]})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_el_servidor_sella_lo_que_tiene_e_ignora_lo_que_manda_el_navegador(ctx):
    await _responder(ctx, _respuesta(1, "Conforme", 3), _respuesta(9, "No Conforme", 0), _respuesta(28, "Parcial", 2))
    cuerpo = {
        "perfil": {"camaras": "no"},
        "respuestas": [{"pregunta_id": 1, "estado": "Conforme", "nivel_evidencia": 3}] * 5,
        "indicadores": {"madurez": 100, "cumplimiento": True},
        "sellado_por": "otra-persona",
    }
    r = await ctx["client"].post(RESULTADOS, headers=_como(ctx, "dpo"), json=cuerpo)
    assert r.status_code == 201, r.text
    sellado = r.json()

    aplicables = controles_aplicables(cargar_banco_preguntas_raw(), "mediana", normalizar_perfil({"camaras": "no"}))
    guardadas = [_respuesta(1, "Conforme", 3), _respuesta(9, "No Conforme", 0), _respuesta(28, "Parcial", 2)]
    esperado, _ = calcular_indicadores(aplicables, guardadas, set())
    assert sellado["indicadores"] == asdict(esperado)
    assert sellado["sellado_por"] == ctx["u"]["dpo"][0]
    assert sellado["tamano"] == "mediana" and sellado["perfil"]["camaras"] == "no"
    assert [(x["pregunta_id"], x["nivel_declarado"], x["nivel_sellado"]) for x in sellado["respuestas"]] == [
        (1, 3, 0), (9, 0, 0), (28, 2, 0)]

    async with ctx["factory"]() as s:
        eventos = (await s.execute(text(
            "SELECT count(*) FROM audit_events WHERE tenant_id = :t AND action = 'diagnostico_resultado_sellado'"
        ), {"t": ctx["a"]})).scalar_one()
    assert eventos == 1


@pytest.mark.asyncio
async def test_con_un_documento_que_el_servidor_comprueba_se_sella_el_nivel_declarado(ctx):
    from features.evidencias import evidencias_service

    evidencias_service.registrar_evidencia_deduplicada(evidencias_service.EvidenciaRegistro(
        tenant_id=ctx["a"], nombre_archivo="politica.pdf", sha256_hash="ab" * 32, controles_vinculados=[1],
    ))
    await _responder(ctx, _respuesta(1, "Conforme", 3), _respuesta(2, "Parcial", 2))
    r = await ctx["client"].post(RESULTADOS, headers=_como(ctx, "dpo"), json={})
    assert r.status_code == 201, r.text
    por_pregunta = {x["pregunta_id"]: x for x in r.json()["respuestas"]}
    assert (por_pregunta[1]["con_documento"], por_pregunta[1]["nivel_sellado"]) == (True, 3)
    assert (por_pregunta[2]["con_documento"], por_pregunta[2]["nivel_sellado"]) == (False, 0)


@pytest.mark.asyncio
async def test_el_resultado_sobrevive_a_una_sesion_nueva_y_lo_consultan_los_demas_roles(ctx):
    from main import app

    await _responder(ctx, _respuesta(1))
    sellado = (await ctx["client"].post(RESULTADOS, headers=_como(ctx, "dpo"), json={})).json()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as nuevo:
        for clave in ("impl", "coord", "admin", "dpo"):
            r = await nuevo.get(RESULTADOS, headers=_como(ctx, clave))
            assert r.status_code == 200, r.text
            assert [x["id"] for x in r.json()["resultados"]] == [sellado["id"]]
    assert (await ctx["client"].get(RESULTADOS, headers=_como(ctx, "resp"))).status_code == 403


@pytest.mark.asyncio
async def test_historial_del_mas_reciente_al_mas_antiguo_con_la_cadena_integra(ctx):
    await _responder(ctx, _respuesta(1))
    primero = (await ctx["client"].post(RESULTADOS, headers=_como(ctx, "dpo"), json={})).json()
    await _responder(ctx, _respuesta(2, "Parcial", 1))
    segundo = (await ctx["client"].post(RESULTADOS, headers=_como(ctx, "dpo"), json={})).json()

    historial = (await ctx["client"].get(RESULTADOS, headers=_como(ctx, "impl"))).json()
    assert [x["id"] for x in historial["resultados"]] == [segundo["id"], primero["id"]]
    assert (primero["secuencia"], segundo["secuencia"]) == (1, 2)
    assert segundo["huella_anterior"] == primero["huella"]
    assert historial["cadena_integra"] is True and historial["primer_alterado"] is None
    assert historial["dpo_vigente"] is True


@pytest.mark.asyncio
async def test_alterar_un_resultado_en_la_base_rompe_la_cadena(ctx):
    await _responder(ctx, _respuesta(1))
    primero = (await ctx["client"].post(RESULTADOS, headers=_como(ctx, "dpo"), json={})).json()
    await ctx["client"].post(RESULTADOS, headers=_como(ctx, "dpo"), json={})

    # El dueño de la base (no la aplicación) reescribe un indicador del primer resultado.
    async with ctx["factory"]() as s:
        from app_core.db.session import fijar_contexto_rls

        await fijar_contexto_rls(s, ctx["a"])
        await s.execute(text(
            "UPDATE diagnostico_resultados SET indicadores = jsonb_set(indicadores, '{madurez}', '99') WHERE id = :id"
        ), {"id": primero["id"]})
        await s.commit()

    historial = (await ctx["client"].get(RESULTADOS, headers=_como(ctx, "coord"))).json()
    assert historial["cadena_integra"] is False
    assert historial["primer_alterado"] == primero["id"]


@pytest.mark.asyncio
async def test_la_aplicacion_no_puede_editar_ni_borrar_un_resultado(ctx):
    from app_core.db.session import fijar_contexto_rls

    await _responder(ctx, _respuesta(1))
    sellado = (await ctx["client"].post(RESULTADOS, headers=_como(ctx, "dpo"), json={})).json()
    for sentencia in (
        "UPDATE diagnostico_resultados SET tamano = 'micro' WHERE id = :id",
        "DELETE FROM diagnostico_resultados WHERE id = :id",
    ):
        async with ctx["factory"]() as s:
            await s.execute(text("SET LOCAL ROLE lopdp_app"))
            await fijar_contexto_rls(s, ctx["a"])
            with pytest.raises(DBAPIError) as error:
                await s.execute(text(sentencia), {"id": sellado["id"]})
            assert error.value.orig.sqlstate == "42501"
            await s.rollback()


@pytest.mark.asyncio
async def test_rls_entre_organizaciones(ctx):
    from app_core.db.session import fijar_contexto_rls

    await _responder(ctx, _respuesta(1))
    await ctx["client"].post(RESULTADOS, headers=_como(ctx, "dpo"), json={})
    assert (await ctx["client"].get(RESULTADOS, headers=_como(ctx, "dpo_b"))).json()["resultados"] == []
    async with ctx["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, ctx["b"])
        assert (await s.execute(text("SELECT count(*) FROM diagnostico_resultados"))).scalar_one() == 0
        with pytest.raises(DBAPIError):
            await s.execute(text(
                "INSERT INTO diagnostico_resultados (id, tenant_id, secuencia, sellado_por, sellado_en, normativa, "
                "version_normativa, tamano, perfil, respuestas, indicadores, huella_anterior, huella) "
                "VALUES (:id, :a, 99, :u, now(), 'LOPDP', 'v', 'micro', '{}', '[]', '{}', :h, :h)"
            ), {"id": str(uuid.uuid4()), "a": ctx["a"], "u": ctx["u"]["dpo_b"][0], "h": "f" * 64})


@pytest.mark.asyncio
async def test_sin_respuestas_o_sin_tamano_no_se_sella(ctx):
    r = await ctx["client"].post(RESULTADOS, headers=_como(ctx, "dpo"), json={})
    assert r.status_code == 409 and "respuestas" in r.json()["detail"]
    r = await ctx["client"].post(RESULTADOS, headers=_como(ctx, "dpo_b"), json={})
    assert r.status_code == 409 and "tamaño" in r.json()["detail"]


@pytest.mark.parametrize("perfil", [{"camaras": "tal vez"}, {"desconocida": "si"}])
@pytest.mark.asyncio
async def test_perfil_fuera_de_vocabulario_es_422(ctx, perfil):
    await _responder(ctx, _respuesta(1))
    r = await ctx["client"].post(RESULTADOS, headers=_como(ctx, "dpo"), json={"perfil": perfil})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_una_organizacion_sin_dpo_lo_sabe_por_el_historial(ctx):
    r = await ctx["client"].get(RESULTADOS, headers=_como(ctx, "impl_c"))
    assert r.status_code == 200
    assert r.json()["dpo_vigente"] is False
