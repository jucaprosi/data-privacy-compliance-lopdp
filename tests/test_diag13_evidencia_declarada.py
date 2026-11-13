# ¤diagnostico ¤evidencias ¤arbitro
"""DIAG-13: en el PMV el sello conserva la evidencia declarada por el DPO, marcada como no verificada.

Contrato: INV_LOPDP_PMV_DECLARED_EVIDENCE (governance/artefactos/INVARIANTS.md) y la decisión del
propietario del 2026-11-05. La política se lee de EVIDENCIA_DIAGNOSTICO en un solo sitio
(`resultados_engine.politica_evidencia`): «declarada» por omisión, «verificada» para EVYDENTIA.

Las pruebas puras corren sin base. Las que recorren PostgreSQL (sello por la API, cadena de
huellas y RLS con lopdp_app) exigen TEST_DATABASE_URL de una rama Neon de revisión propia, nunca
producción; sin ella se omiten.

Prueba de mutación documentada (DIAG-13), ejecutada el 2026-11-05 en la rama Neon
test-juan-carlos-diag13: en features/diagnostico/services/resultados_engine.py,
dentro de calcular_indicadores, se cambió
`sellado, verificada = nivel_sellado_y_verificacion(declarado, con_documento, politica)` por
`sellado, verificada = (declarado if con_documento else 0), False` (la regla de DIAG-03 sin
importar la política). La primera prueba,
test_declarada_sella_el_nivel_declarado_y_lo_marca_no_verificado, falló (assert (3, 0) == (3, 3)), igual
que test_el_sello_por_la_api_conserva_lo_declarado_y_la_cadena_cuadra; se restauró la línea y
ambas pasan.
"""
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

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

from features.diagnostico.domain.models import (  # noqa: E402
    FichaOrganizacion,
    NivelEvidencia,
    RespuestaDiagnostico,
)
from features.diagnostico.domain.resultados import HUELLA_GENESIS  # noqa: E402
from features.diagnostico.services.engine import cargar_banco_preguntas_raw  # noqa: E402
from features.diagnostico.services.report_generator import (  # noqa: E402
    generar_informe_html,
    generar_informe_markdown,
)
from features.diagnostico.services.resultados_engine import (  # noqa: E402
    PoliticaEvidenciaDesconocida,
    _fila_a_resultado,
    calcular_huella,
    calcular_indicadores,
    controles_aplicables,
    normalizar_perfil,
    politica_evidencia,
    primer_resultado_alterado,
)
from features.diagnostico.services.engine import calcular_scoring_multidimensional  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
RESPUESTAS = "/api/v1/diagnostico/respuestas"
RESULTADOS = "/api/v1/diagnostico/resultados"
MARCA = "declarada, no verificada"


def _aplicables():
    return controles_aplicables(cargar_banco_preguntas_raw(), "corporativo", normalizar_perfil({}))


def _guardada(pregunta_id=1, asignado=4, evidencia=3):
    return {"pregunta_id": pregunta_id, "nivel_asignado": asignado, "nivel_evidencia": evidencia,
            "control": "", "dimension": "D01"}


# --- Política y sello (sin base) --------------------------------------------------------------


def test_declarada_sella_el_nivel_declarado_y_lo_marca_no_verificado(monkeypatch):
    monkeypatch.delenv("EVIDENCIA_DIAGNOSTICO", raising=False)
    assert politica_evidencia() == "declarada"
    indicadores, selladas = calcular_indicadores(_aplicables(), [_guardada()], set())
    assert (selladas[0].nivel_declarado, selladas[0].nivel_sellado) == (3, 3)
    assert selladas[0].evidencia_verificada is False and selladas[0].con_documento is False
    # La calidad de evidencia ya no sale en cero: media(3) / 4 * 100.
    assert indicadores.respaldo_documental == 75.0


def test_declarada_no_marca_verificada_ni_con_documento(monkeypatch):
    monkeypatch.setenv("EVIDENCIA_DIAGNOSTICO", "declarada")
    _, selladas = calcular_indicadores(_aplicables(), [_guardada()], {1})
    assert (selladas[0].nivel_sellado, selladas[0].evidencia_verificada) == (3, False)


def test_verificada_conserva_la_regla_de_diag03(monkeypatch):
    monkeypatch.setenv("EVIDENCIA_DIAGNOSTICO", "verificada")
    _, sin_documento = calcular_indicadores(_aplicables(), [_guardada()], set())
    _, con_documento = calcular_indicadores(_aplicables(), [_guardada()], {1})
    assert (sin_documento[0].nivel_sellado, sin_documento[0].evidencia_verificada) == (0, False)
    assert (con_documento[0].nivel_sellado, con_documento[0].evidencia_verificada) == (3, True)


@pytest.mark.parametrize("valor", ["verificda", "si", "E0"])
def test_un_valor_desconocido_se_rechaza(monkeypatch, valor):
    monkeypatch.setenv("EVIDENCIA_DIAGNOSTICO", valor)
    with pytest.raises(PoliticaEvidenciaDesconocida):
        politica_evidencia()
    with pytest.raises(PoliticaEvidenciaDesconocida):
        calcular_indicadores(_aplicables(), [_guardada()], set())


def test_un_valor_desconocido_hace_fallar_el_arranque():
    env = {**os.environ, "EVIDENCIA_DIAGNOSTICO": "otra",
           "DATABASE_URL": "postgresql+psycopg://sin-base:sin-base@localhost:1/sin-base"}
    r = subprocess.run([sys.executable, "-c", "import features.diagnostico.diagnostico_service"],
                       cwd=RAIZ, env=env, capture_output=True, text=True, timeout=120)
    assert r.returncode != 0
    assert "PoliticaEvidenciaDesconocida" in r.stderr and "EVIDENCIA_DIAGNOSTICO" in r.stderr


# --- Huella --------------------------------------------------------------------------------------


def _fila(respuestas):
    fila = {"id": str(uuid.uuid4()), "tenant_id": "t", "secuencia": 1, "sellado_por": "u",
            "sellado_en": datetime(2026, 11, 1, tzinfo=timezone.utc), "normativa": "LOPDP",
            "version_normativa": "LOPDP-EC-2026.v1", "tamano": "micro", "perfil": {},
            "respuestas": respuestas, "indicadores": {"forma": "anterior"},
            "huella_anterior": HUELLA_GENESIS, "huella": ""}
    sellable = {**fila, "sellado_en": fila["sellado_en"].isoformat()}
    del sellable["huella"]
    fila["huella"] = calcular_huella(sellable)
    return fila


def test_un_resultado_sellado_antes_de_diag13_sigue_verificando_su_cadena():
    # Forma de DIAG-08: con nivel asignado y sin `evidencia_verificada`.
    anterior = [{"pregunta_id": 1, "control": "C", "dimension": "D01", "estado": "Conforme",
                 "criticidad": 3, "nivel_declarado": 3, "nivel_sellado": 0, "con_documento": False,
                 "nivel_asignado": 4}]
    resultado = _fila_a_resultado(_fila(anterior))
    assert resultado.respuestas[0].evidencia_verificada is None
    assert "evidencia_verificada" not in resultado.contenido()["respuestas"][0]
    assert primer_resultado_alterado([resultado]) is None


def test_evidencia_verificada_entra_en_la_huella():
    nueva = [{"pregunta_id": 1, "control": "C", "dimension": "D01", "estado": "Conforme",
              "criticidad": 3, "nivel_declarado": 3, "nivel_sellado": 3, "con_documento": False,
              "nivel_asignado": 4, "evidencia_verificada": False}]
    fila = _fila(nueva)
    resultado = _fila_a_resultado(fila)
    assert resultado.contenido()["respuestas"][0]["evidencia_verificada"] is False
    assert primer_resultado_alterado([resultado]) is None
    # Quien cambie «no verificada» por «verificada» en la base rompe la cadena.
    alterada = _fila_a_resultado({**fila, "respuestas": [{**nueva[0], "evidencia_verificada": True}]})
    assert primer_resultado_alterado([alterada]) is alterada


# --- Reporte -------------------------------------------------------------------------------------


def _informes(politica):
    ficha = FichaOrganizacion(tenant_id="empresa-demo-ec", sector="Comercio", tamano="Mediana")
    respuestas = [
        RespuestaDiagnostico(id_pregunta="1", respuesta_afirmativa=True, nivel_evidencia=NivelEvidencia.E3_OPERATIVA),
        RespuestaDiagnostico(id_pregunta="9", respuesta_afirmativa=False, nivel_evidencia=NivelEvidencia.E2_DOCUMENTAL),
    ]
    scoring = calcular_scoring_multidimensional(respuestas)
    return (generar_informe_markdown(ficha, scoring, respuestas, politica=politica),
            generar_informe_html(ficha, scoring, respuestas, politica=politica))


@pytest.mark.parametrize("politica", ["declarada", None])
def test_el_reporte_marca_declarada_no_verificada_y_nunca_verificada(monkeypatch, politica):
    monkeypatch.delenv("EVIDENCIA_DIAGNOSTICO", raising=False)
    for informe in _informes(politica):
        assert MARCA in informe
        assert "E2_DOCUMENTAL (declarada, no verificada)" in informe
        assert "verificada" not in informe.lower().replace("no verificada", "")


def test_con_verificada_el_reporte_no_lleva_la_marca(monkeypatch):
    monkeypatch.setenv("EVIDENCIA_DIAGNOSTICO", "verificada")
    for informe in _informes(None):
        assert MARCA not in informe


# --- Recorrido contra PostgreSQL ----------------------------------------------------------------


@pytest_asyncio.fixture
async def ctx(monkeypatch):
    if not _TEST_URL:
        pytest.skip("TEST_DATABASE_URL no configurada")
    assert "ep-late-hall" not in _TEST_URL, "Se requiere una rama de desarrollo o test (nunca producción)"
    monkeypatch.setenv("AUTH_MODE", "headers")
    monkeypatch.delenv("EVIDENCIA_DIAGNOSTICO", raising=False)
    from app_core.db.session import fijar_contexto_rls, get_session
    from features.evidencias import evidencias_service
    from main import app

    engine = create_async_engine(_TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    a, b = f"diag13-a-{sufijo}", f"diag13-b-{sufijo}"
    usuarios = {"dpo": (f"diag13-dpo-{sufijo}", a, "dpo"), "admin": (f"diag13-admin-{sufijo}", a, "admin_organizacion"), "dpo_b": (f"diag13-dpob-{sufijo}", b, "dpo")}
    async with factory() as s:
        for tenant in (a, b):
            await s.execute(text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
                "VALUES (:t, :t, :t, :t, 'mediana')"
            ), {"t": tenant})
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
            yield {"client": client, "factory": factory, "a": a, "b": b, "u": usuarios}
    finally:
        app.dependency_overrides.clear()
        evidencias_service.reiniciar_repositorio_evidencias()
        async with factory() as s:
            for t in (a, b):
                await fijar_contexto_rls(s, t)
                for sentencia in (
                    "DELETE FROM diagnostico_resultados WHERE tenant_id = :t",
                    "DELETE FROM diagnostico_respuestas WHERE tenant_id = :t",
                    "DELETE FROM audit_events WHERE tenant_id = :t",
                    "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
                ):
                    await s.execute(text(sentencia), {"t": t})
                await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t})
            await s.execute(text("DELETE FROM users WHERE id LIKE :p"), {"p": f"diag13-%-{sufijo}"})
            await s.commit()
        await engine.dispose()


def _como(ctx, clave):
    uid, tenant, rol = ctx["u"][clave]
    return {"X-User-ID": uid, "X-Tenant-ID": tenant, "X-Role": rol}


async def _responder_y_sellar(ctx):
    respuesta = {"pregunta_id": 1, "control": "Control del banco", "dimension": "D01", "nivel_asignado": 4,
                 "nivel_evidencia": 3, "criticidad": 3, "es_critica": False, "riesgo_base": 5}
    r = await ctx["client"].put(RESPUESTAS, headers=_como(ctx, "admin"), json={"respuestas": [respuesta]})
    assert r.status_code == 200, r.text
    r = await ctx["client"].post(RESULTADOS, headers=_como(ctx, "dpo"), json={})
    assert r.status_code == 201, r.text
    return r.json()


@pytest.mark.asyncio
async def test_el_sello_por_la_api_conserva_lo_declarado_y_la_cadena_cuadra(ctx):
    sellado = await _responder_y_sellar(ctx)
    p1 = next(x for x in sellado["respuestas"] if x["pregunta_id"] == 1)
    assert (p1["nivel_declarado"], p1["nivel_sellado"], p1["evidencia_verificada"]) == (3, 3, False)
    historial = (await ctx["client"].get(RESULTADOS, headers=_como(ctx, "dpo"))).json()
    assert historial["cadena_integra"] is True and historial["primer_alterado"] is None


@pytest.mark.asyncio
async def test_rls_con_lopdp_app_sobre_el_sello_declarado(ctx):
    from app_core.db.session import fijar_contexto_rls

    sellado = await _responder_y_sellar(ctx)
    async with ctx["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, ctx["a"])
        guardado = (await s.execute(text(
            "SELECT r->>'evidencia_verificada' FROM diagnostico_resultados, jsonb_array_elements(respuestas) r "
            "WHERE id = :id AND (r->>'pregunta_id')::int = 1"
        ), {"id": sellado["id"]})).scalar_one()
        assert guardado == "false"
        await s.rollback()
    async with ctx["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, ctx["b"])
        assert (await s.execute(text("SELECT count(*) FROM diagnostico_resultados"))).scalar_one() == 0
        await s.rollback()


@pytest.mark.asyncio
async def test_el_contexto_de_la_hoja_de_ruta_dice_que_la_evidencia_es_declarada(ctx):
    from features.roadmap.roadmap_service import armar_contexto_generacion

    await _responder_y_sellar(ctx)
    uid, tenant, _ = ctx["u"]["dpo"]
    async with ctx["factory"]() as s:
        contexto = await armar_contexto_generacion(s, tenant, uid)
    evidencia = contexto["evidencia_diagnostico"]
    assert evidencia["politica"] == "declarada" and evidencia["evidencia_verificada"] is False
    assert "no lo ha verificado" in evidencia["indicacion"]
