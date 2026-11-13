# ¤diagnostico ¤diagnostico-comparativo ¤tablero-dimensiones ¤arbitro
"""DIAG-06: comparativo del diagnóstico de prueba con el real, por dimensión y por control.

INV_LOPDP_MULTIDIMENSIONAL_METRICS: sin cifra única; cada dimensión se compara con la suya.
Las pruebas de motor no usan base de datos; el recorrido por la API corre contra PostgreSQL 16 local
(TEST_DATABASE_URL; sin ella se omite) y nunca contra producción.

Prueba de mutación documentada: en `comparar` se cambió `_por_control(linea_base), _por_control(actual)`
por `_por_control(actual), _por_control(linea_base)` (base y actual invertidas);
`pytest tests/test_diagnostico_comparativo.py::test_cerradas_nuevas_y_siguen_en_un_caso_construido`
y `::test_la_api_compara_prueba_con_real` devolvieron FAILED (cerradas y nuevas intercambiadas).
Se restauró el orden; sin la mutación pasan.
"""
import os
import uuid
from datetime import datetime, timezone

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

from app_core.errors import ErrorNegocio  # noqa: E402
from features.diagnostico.domain.resultados import (  # noqa: E402
    DimensionSellada,
    IndicadoresSellados,
    RespuestaSellada,
    ResultadoSellado,
)
from features.diagnostico.services.comparativo_engine import comparar  # noqa: E402

COMPARATIVO = "/api/v1/diagnostico/comparativo"
RESPUESTAS = "/api/v1/diagnostico/respuestas"
RESULTADOS = "/api/v1/diagnostico/resultados"


# --- Motor (sin base de datos) -------------------------------------------------------------------


def _resp(pid: int, estado: str, dimension: str = "D01") -> RespuestaSellada:
    return RespuestaSellada(
        pregunta_id=pid, control=f"c{pid}", dimension=dimension, estado=estado, criticidad=3,
        nivel_declarado=0, nivel_sellado=0, con_documento=False, nivel_asignado=1,
    )


def _dim(dimension: str, nivel: int) -> DimensionSellada:
    return DimensionSellada(dimension=dimension, nombre=f"Dimensión {dimension}", nivel=nivel, etiqueta="x",
                            score=0.0, cobertura=100.0, brechas_criticas=0, brechas_altas=0)


def _resultado(secuencia: int, respuestas: list[RespuestaSellada], dims: list[DimensionSellada]) -> ResultadoSellado:
    return ResultadoSellado(
        id=f"r{secuencia}", tenant_id="t", secuencia=secuencia, sellado_por="u",
        sellado_en=datetime(2026, 1, secuencia, tzinfo=timezone.utc), normativa="LOPDP",
        version_normativa="v", tamano="mediana", perfil={}, respuestas=respuestas,
        indicadores=IndicadoresSellados(
            cumplimiento=True, brechas_criticas=0, brechas_altas=0, por_dimension=dims,
            respaldo_documental=0.0, preguntas_evaluadas=len(respuestas), preguntas_aplicables=len(respuestas),
            cobertura=100.0,
        ),
    )


def test_cerradas_nuevas_y_siguen_en_un_caso_construido():
    prueba = _resultado(1, [_resp(1, "No Conforme"), _resp(2, "Conforme"), _resp(3, "Parcial", "D02"),
                            _resp(4, "Conforme", "D02")], [_dim("D01", 1), _dim("D02", 3)])
    real = _resultado(2, [_resp(1, "Conforme"), _resp(2, "No Conforme"), _resp(3, "Parcial", "D02"),
                          _resp(4, "Conforme", "D02")], [_dim("D01", 3), _dim("D02", 3)])
    comp = comparar(prueba, real)
    assert comp["comparable"] is True
    assert [c["pregunta_id"] for c in comp["brechas"]["cerradas"]] == [1]
    assert [c["pregunta_id"] for c in comp["brechas"]["nuevas"]] == [2]
    assert [c["pregunta_id"] for c in comp["brechas"]["siguen"]] == [3]
    assert (comp["linea_base"]["tipo"], comp["actual"]["tipo"]) == ("prueba", "real")
    d1, d2 = comp["por_dimension"]
    assert (d1["nivel_base"], d1["nivel_actual"], d1["diferencia_nivel"]) == (1, 3, 2)
    assert (d1["cerradas"], d1["nuevas"], d1["siguen"]) == (1, 1, 0)
    assert (d2["diferencia_nivel"], d2["siguen"]) == (0, 1)


def test_sin_cifra_unica():
    prueba = _resultado(1, [_resp(1, "No Conforme")], [_dim("D01", 1)])
    real = _resultado(2, [_resp(1, "Conforme")], [_dim("D01", 4)])
    comp = comparar(prueba, real)
    assert not {"avance", "avance_global", "cifra_global", "diferencia_global"} & set(comp)


def test_un_control_sin_respuesta_en_un_lado_no_se_compara():
    prueba = _resultado(1, [_resp(1, "No Conforme")], [_dim("D01", 1)])
    real = _resultado(2, [_resp(2, "No Conforme")], [_dim("D01", 1)])
    comp = comparar(prueba, real)
    assert comp["brechas"] == {"cerradas": [], "nuevas": [], "siguen": []}


def test_un_sellado_de_escala_anterior_no_se_compara():
    prueba = _resultado(1, [_resp(1, "Parcial")], [_dim("D01", 1)])
    prueba.indicadores = {"cumplimiento": True, "brechas_criticas": 0}
    real = _resultado(2, [_resp(1, "Parcial")], [_dim("D01", 1)])
    with pytest.raises(ErrorNegocio) as exc:
        comparar(prueba, real)
    assert exc.value.code == "DIAG_COMPARATIVO_ESCALA_ANTERIOR"


# --- Recorrido contra PostgreSQL -----------------------------------------------------------------


def _h(user: str, tenant: str, role: str) -> dict[str, str]:
    return {"X-User-ID": user, "X-Tenant-ID": tenant, "X-Role": role}


def _respuesta(pregunta_id: int, nivel_asignado: int, nivel: int = 2) -> dict:
    return {
        "pregunta_id": pregunta_id, "control": "Control del banco", "dimension": "D01",
        "nivel_asignado": nivel_asignado, "nivel_evidencia": nivel, "criticidad": 3,
        "es_critica": False, "riesgo_base": 5,
    }


@pytest_asyncio.fixture
async def ctx(monkeypatch):
    if not _TEST_URL:
        pytest.skip("TEST_DATABASE_URL no configurada")
    assert "ep-late-hall" not in _TEST_URL, "Se requiere una base de pruebas (nunca producción)"
    monkeypatch.setenv("AUTH_MODE", "headers")
    from app_core.db.session import fijar_contexto_rls, get_session
    from main import app

    engine = create_async_engine(_TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    a, b = f"diag6-a-{sufijo}", f"diag6-b-{sufijo}"
    usuarios = {
        "dpo": (f"diag6-dpo-{sufijo}", a, "dpo"),
        "admin": (f"diag6-admin-{sufijo}", a, "admin_organizacion"),
        "impl": (f"diag6-impl-{sufijo}", a, "implementador"),
        "resp": (f"diag6-resp-{sufijo}", a, "responsable_area"),
        "dpo_b": (f"diag6-dpob-{sufijo}", b, "dpo"),
    }
    async with factory() as s:
        for tenant in (a, b):
            await s.execute(text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
                "VALUES (:t, :t, :t, :t, 'mediana')"
            ), {"t": tenant})
        for uid, tenant, rol in usuarios.values():
            await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :u)"),
                            {"u": uid, "e": f"{uid}@example.invalid"})
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
            yield {"client": client, "u": usuarios}
    finally:
        app.dependency_overrides.clear()
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
            await s.execute(text("DELETE FROM users WHERE id LIKE :p"), {"p": f"diag6-%-{sufijo}"})
            await s.commit()
        await engine.dispose()


def _como(ctx, clave):
    uid, tenant, rol = ctx["u"][clave]
    return _h(uid, tenant, rol)


async def _responder_y_sellar(ctx, clave, *respuestas):
    c = ctx["client"]
    r = await c.put(RESPUESTAS, headers=_como(ctx, "admin"), json={"respuestas": list(respuestas)})
    assert r.status_code == 200, r.text
    r = await c.post(RESULTADOS, headers=_como(ctx, clave), json={"perfil": {}})
    assert r.status_code == 201, r.text


@pytest.mark.asyncio
async def test_sin_sellos_o_con_uno_no_compara_y_lo_dice(ctx):
    c = ctx["client"]
    r = await c.get(COMPARATIVO, headers=_como(ctx, "impl"))
    assert r.status_code == 200 and r.json()["comparable"] is False and r.json()["linea_base"] is None
    assert r.json()["codigo_motivo"] == "sin_sellos"
    await _responder_y_sellar(ctx, "dpo", _respuesta(1, 1))
    r = await c.get(COMPARATIVO, headers=_como(ctx, "impl"))
    cuerpo = r.json()
    assert cuerpo["comparable"] is False and cuerpo["linea_base"]["tipo"] == "prueba"
    assert cuerpo["codigo_motivo"] == "sin_real"
    assert cuerpo["actual"] is None and cuerpo["motivo"]


@pytest.mark.asyncio
async def test_la_api_compara_prueba_con_real(ctx):
    c = ctx["client"]
    await _responder_y_sellar(ctx, "dpo", _respuesta(1, 1), _respuesta(2, 5), _respuesta(3, 2))
    await _responder_y_sellar(ctx, "dpo", _respuesta(1, 5), _respuesta(2, 1), _respuesta(3, 2))
    r = await c.get(COMPARATIVO, headers=_como(ctx, "impl"))
    assert r.status_code == 200, r.text
    comp = r.json()
    assert comp["comparable"] is True
    assert [x["pregunta_id"] for x in comp["brechas"]["cerradas"]] == [1]
    assert [x["pregunta_id"] for x in comp["brechas"]["nuevas"]] == [2]
    assert [x["pregunta_id"] for x in comp["brechas"]["siguen"]] == [3]


@pytest.mark.asyncio
async def test_no_se_comparan_resultados_de_otra_organizacion(ctx):
    c = ctx["client"]
    await _responder_y_sellar(ctx, "dpo", _respuesta(1, 1))
    await _responder_y_sellar(ctx, "dpo", _respuesta(1, 5))
    r = await c.get(COMPARATIVO, headers=_como(ctx, "dpo_b"))
    assert r.status_code == 200
    assert r.json()["comparable"] is False and r.json()["linea_base"] is None


@pytest.mark.asyncio
async def test_roles_sin_permiso_reciben_403(ctx):
    r = await ctx["client"].get(COMPARATIVO, headers=_como(ctx, "resp"))
    assert r.status_code == 403
