# ¤diagnostico ¤diagnostico-scoring ¤arbitro
"""DIAG-08: escala SMARTCIDI en el servidor (nivel asignado 1 a 5, evidencia 0 a 4, nivel por dimensión).

Las pruebas puras (motor, esquema, sellado anterior) corren sin base. Las que recorren PostgreSQL
(API, migración, RLS con lopdp_app) exigen TEST_DATABASE_URL de una rama Neon de revisión propia,
nunca producción ni la rama compartida `test`; sin ella se omiten.

Prueba de mutación documentada (DIAG-08): volver a la tabla de tres estados en
features/diagnostico/services/dimensiones_sgpdp.py, es decir, hacer que calcular_nivel_efectivo
tome `{Conforme: 5, Parcial: 3, No Conforme: 1}[estado]` en lugar de `nivel_asignado`, hace fallar
test_nivel_asignado_tal_cual en los casos de nivel asignado 2 y 4 (efectivo 3 y 5 en lugar de 2 y 4).
"""
import importlib.util
import os
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pytest
import pytest_asyncio
from pydantic import ValidationError

_TEST_URL = os.environ.get("TEST_DATABASE_URL", "")
if _TEST_URL:
    os.environ["DATABASE_URL"] = _TEST_URL
else:
    os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://sin-base:sin-base@localhost:1/sin-base")

from api.routers.diagnostico_respuestas import RespuestaEntrada  # noqa: E402
from features.diagnostico.domain.models import (  # noqa: E402
    NIVELES_ASIGNADOS,
    NIVELES_EVIDENCIA,
    RespuestaControl,
    estado_desde_nivel_asignado,
)
from features.diagnostico.domain.resultados import (  # noqa: E402
    HUELLA_GENESIS,
    indicadores_a_salida,
)
from features.diagnostico.services.dimensiones_sgpdp import calcular_nivel_efectivo  # noqa: E402
from features.diagnostico.services.engine import cargar_banco_preguntas_raw  # noqa: E402
from features.diagnostico.services.resultados_engine import (  # noqa: E402
    _fila_a_resultado,
    calcular_huella,
    calcular_indicadores,
    controles_aplicables,
    normalizar_perfil,
    primer_resultado_alterado,
)

RUTA = "/api/v1/diagnostico/respuestas"
MIGRACION = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "20261031_diagnostico_escala_smartcidi.py"


def _aplicables():
    return controles_aplicables(cargar_banco_preguntas_raw(), "corporativo", normalizar_perfil({}))


def _guardada(pregunta_id: int, nivel_asignado, nivel_evidencia: int) -> dict:
    return {"pregunta_id": pregunta_id, "nivel_asignado": nivel_asignado, "nivel_evidencia": nivel_evidencia,
            "control": "", "dimension": "D01"}


# --- Escala y reglas (sin base de datos) -------------------------------------------------------


def test_la_escala_es_la_del_archivo_smartcidi():
    assert sorted(NIVELES_ASIGNADOS) == [1, 2, 3, 4, 5]
    assert sorted(NIVELES_EVIDENCIA) == [0, 1, 2, 3, 4]
    assert NIVELES_ASIGNADOS[1][0] == "Inicial / Reactivo" and NIVELES_ASIGNADOS[5][0] == "Optimizado / Mejora continua"
    assert NIVELES_EVIDENCIA[0].startswith("Verbal") and NIVELES_EVIDENCIA[4].startswith("Revisada")


@pytest.mark.parametrize("asignado, estado", [(None, "Pendiente"), (1, "No Conforme"), (2, "Parcial"),
                                              (3, "Parcial"), (4, "Conforme"), (5, "Conforme")])
def test_estado_derivado_del_nivel_asignado(asignado, estado):
    assert estado_desde_nivel_asignado(asignado).value == estado


@pytest.mark.parametrize("asignado, estado", [(4, "Conforme"), (2, "Parcial")])
def test_nivel_asignado_tal_cual(asignado, estado):
    # Con documento y evidencia 4 el nivel efectivo es el asignado, sin la tabla de tres estados.
    indicadores, selladas = calcular_indicadores(_aplicables(), [_guardada(1, asignado, 4)], {1})
    assert selladas[0].estado == estado and selladas[0].nivel_asignado == asignado
    assert calcular_nivel_efectivo(RespuestaControl(pregunta_id=1, nivel_asignado=asignado, evidencia_nivel=4)) == asignado


def test_evidencia_acota_nivel():
    # Asignado 5, evidencia 2 con documento: efectivo min(5, 2 + 1) = 3.
    _, con_documento = calcular_indicadores(_aplicables(), [_guardada(1, 5, 2)], {1})
    assert con_documento[0].nivel_sellado == 2
    assert calcular_nivel_efectivo(RespuestaControl(pregunta_id=1, nivel_asignado=5, evidencia_nivel=2)) == 3
    # Sin documento la evidencia se sella en 0 y el efectivo es 1.
    _, sin_documento = calcular_indicadores(_aplicables(), [_guardada(1, 5, 2)], set())
    assert (sin_documento[0].nivel_declarado, sin_documento[0].nivel_sellado) == (2, 0)
    assert calcular_nivel_efectivo(
        RespuestaControl(pregunta_id=1, nivel_asignado=5, evidencia_nivel=sin_documento[0].nivel_sellado)) == 1


@pytest.mark.parametrize("cambio", [{"estado": "Conforme"}, {"nivel_asignado": 6}, {"nivel_asignado": 0},
                                    {"nivel_evidencia": 5}, {"nivel_evidencia": -1}])
def test_escala_validada(cambio):
    cuerpo = {"pregunta_id": 1, "control": "Control", "dimension": "D01", "nivel_asignado": 3,
              "nivel_evidencia": 2, "criticidad": 3, "riesgo_base": 5}
    RespuestaEntrada(**cuerpo)
    with pytest.raises(ValidationError):
        RespuestaEntrada(**{**cuerpo, **cambio})


def test_indicadores_por_dimension():
    guardadas = [_guardada(1, 4, 3), _guardada(2, 2, 2)]
    indicadores, _ = calcular_indicadores(_aplicables(), guardadas, {1, 2})
    crudo = asdict(indicadores)
    assert crudo["escala"] == "smartcidi_1_5"
    assert not {"madurez", "nivel_madurez", "riesgo_residual"} & set(crudo)
    assert crudo["por_dimension"], "debe traer al menos una dimensión"
    for d in crudo["por_dimension"]:
        assert set(d) == {"dimension", "nombre", "nivel", "etiqueta", "score", "cobertura",
                          "brechas_criticas", "brechas_altas"}
        assert 0 <= d["nivel"] <= 5
    # respaldo_documental = media(evidencia sellada de lo evaluado) / 4 * 100 = (3 + 2) / 2 / 4 * 100
    assert crudo["respaldo_documental"] == 62.5
    assert crudo["preguntas_evaluadas"] == 2 and crudo["cumplimiento"] is (crudo["brechas_criticas"] == 0)


def test_pregunta_con_nivel_asignado_nulo_computa_como_pendiente():
    indicadores, selladas = calcular_indicadores(_aplicables(), [_guardada(1, None, 3)], {1})
    assert selladas[0].estado == "Pendiente"
    assert indicadores.preguntas_evaluadas == 0 and indicadores.respaldo_documental == 0.0


def test_resultado_anterior_legible():
    anterior = {"madurez": 61.2, "nivel_madurez": 3, "cumplimiento": True, "brechas_criticas": 0,
                "respaldo_documental": 50.0, "riesgo_residual": 38.8, "preguntas_evaluadas": 1,
                "preguntas_aplicables": 1, "cobertura": 100.0}
    respuestas = [{"pregunta_id": 1, "control": "C", "dimension": "D01", "estado": "Conforme", "criticidad": 3,
                   "nivel_declarado": 2, "nivel_sellado": 2, "con_documento": True}]
    fila = {"id": str(uuid.uuid4()), "tenant_id": "t", "secuencia": 1, "sellado_por": "u",
            "sellado_en": datetime(2026, 10, 1, tzinfo=timezone.utc),
            "normativa": "LOPDP", "version_normativa": "v", "tamano": "micro", "perfil": {},
            "respuestas": respuestas, "indicadores": anterior, "huella_anterior": HUELLA_GENESIS, "huella": ""}
    # La huella con que se selló: la forma de entonces, sin `nivel_asignado`.
    sellable = {**fila, "sellado_en": fila["sellado_en"].isoformat()}
    del sellable["huella"]
    fila["huella"] = calcular_huella(sellable)

    resultado = _fila_a_resultado(fila)
    assert primer_resultado_alterado([resultado]) is None
    assert indicadores_a_salida(resultado.indicadores)["escala"] == "anterior"
    assert resultado.indicadores == anterior, "se lee con su escala anterior, sin reescribir"


# --- Recorrido contra PostgreSQL (rama Neon de revisión propia) ---------------------------------


def _h(user: str, tenant: str, role: str) -> dict[str, str]:
    return {"X-User-ID": user, "X-Tenant-ID": tenant, "X-Role": role}


def _cuerpo(pregunta_id: int = 1, **cambios) -> dict:
    base = {"pregunta_id": pregunta_id, "control": "Política", "dimension": "D01", "nivel_asignado": 3,
            "nivel_evidencia": 2, "criticidad": 3, "es_critica": False, "riesgo_base": 5}
    return {**base, **cambios}


@pytest_asyncio.fixture
async def ctx(monkeypatch):
    if not _TEST_URL:
        pytest.skip("TEST_DATABASE_URL no configurada")
    assert "ep-late-hall" not in _TEST_URL, "Se requiere la rama Neon de revisión propia (nunca producción)"
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app_core.db.session import fijar_contexto_rls, get_session
    from main import app

    monkeypatch.setenv("AUTH_MODE", "headers")
    engine = create_async_engine(_TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    a, b = f"diag8-a-{sufijo}", f"diag8-b-{sufijo}"
    usuarios = {"dpo": (f"diag8-dpo-{sufijo}", a, "dpo"), "dpo_b": (f"diag8-dpob-{sufijo}", b, "dpo")}
    async with factory() as s:
        for t in (a, b):
            await s.execute(text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:t, :t, :t, :t)"
            ), {"t": t})
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
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield {"client": client, "factory": factory, "a": a, "b": b, "u": usuarios}
    finally:
        app.dependency_overrides.clear()
        async with factory() as s:
            for t in (a, b):
                await fijar_contexto_rls(s, t)
                for sentencia in ("DELETE FROM diagnostico_respuestas WHERE tenant_id = :t",
                                  "DELETE FROM audit_events WHERE tenant_id = :t",
                                  "DELETE FROM user_tenant_roles WHERE tenant_id = :t"):
                    await s.execute(text(sentencia), {"t": t})
                await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t})
            await s.execute(text("DELETE FROM users WHERE id LIKE :p"), {"p": f"diag8-%-{sufijo}"})
            await s.commit()
        await engine.dispose()


def _como(ctx, clave):
    uid, tenant, rol = ctx["u"][clave]
    return _h(uid, tenant, rol)


@pytest.mark.asyncio
@pytest.mark.parametrize("cambio", [{"estado": "Conforme"}, {"nivel_asignado": 6}, {"nivel_evidencia": 5}])
async def test_escala_validada_en_la_api(ctx, cambio):
    r = await ctx["client"].put(RUTA, headers=_como(ctx, "dpo"), json={"respuestas": [_cuerpo(1, **cambio)]})
    assert r.status_code == 422
    assert (await ctx["client"].get(RUTA, headers=_como(ctx, "dpo"))).json()["respuestas"] == []


@pytest.mark.asyncio
async def test_el_servidor_deriva_el_estado(ctx):
    cuerpos = [_cuerpo(i + 1, nivel_asignado=n) for i, n in enumerate((1, 2, 3, 4, 5))]
    r = await ctx["client"].put(RUTA, headers=_como(ctx, "dpo"), json={"respuestas": cuerpos})
    assert r.status_code == 200, r.text
    assert [x["estado"] for x in r.json()["respuestas"]] == ["No Conforme", "Parcial", "Parcial", "Conforme", "Conforme"]
    assert [x["nivel_asignado"] for x in r.json()["respuestas"]] == [1, 2, 3, 4, 5]


@pytest.mark.asyncio
async def test_rls_respuestas_escala(ctx):
    from sqlalchemy import text

    from app_core.db.session import fijar_contexto_rls

    await ctx["client"].put(RUTA, headers=_como(ctx, "dpo"), json={"respuestas": [_cuerpo(1)]})
    async with ctx["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, ctx["b"])
        assert (await s.execute(text("SELECT count(*) FROM diagnostico_respuestas"))).scalar_one() == 0


@pytest.mark.asyncio
async def test_migracion_escala(ctx):
    """Con la tabla en la forma anterior (downgrade), evidencia 1, 2 y 3 pasan a 2, 3 y 4; todo en una
    transacción que se revierte al final."""
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import text

    especificacion = importlib.util.spec_from_file_location("migracion_diag08", MIGRACION)
    migracion = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(migracion)

    usuario, tenant, _ = ctx["u"]["dpo"]

    def _ejecutar(operacion, sync_conn):
        with Operations.context(MigrationContext.configure(sync_conn)):
            operacion()

    async with ctx["factory"]() as s:
        conexion = await s.connection()
        await conexion.run_sync(lambda c: _ejecutar(migracion.downgrade, c))
        await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant})
        for pid, evidencia in ((1, 0), (2, 1), (3, 2), (4, 3)):
            await s.execute(text(
                "INSERT INTO diagnostico_respuestas (tenant_id, pregunta_id, control, dimension, estado, "
                "nivel_evidencia, criticidad, es_critica, riesgo_base, respondido_por) "
                "VALUES (:t, :p, 'Control', 'D01', 'Parcial', :e, 3, false, 5, :u)"
            ), {"t": tenant, "p": pid, "e": evidencia, "u": usuario})
        await conexion.run_sync(lambda c: _ejecutar(migracion.upgrade, c))
        filas = (await s.execute(text(
            "SELECT pregunta_id, nivel_evidencia, nivel_asignado FROM diagnostico_respuestas "
            "WHERE tenant_id = :t ORDER BY pregunta_id"
        ), {"t": tenant})).all()
        await s.rollback()
    assert [tuple(f) for f in filas] == [(1, 0, None), (2, 2, None), (3, 3, None), (4, 4, None)]
