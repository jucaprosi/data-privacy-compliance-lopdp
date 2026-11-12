# ¤rbac-tenant ¤cartera ¤arbitro
"""ORG-15: cartera de organizaciones por pertenencia, sin abrir la RLS.

Contrato: governance/especificaciones/ORG-15.md §5. Invariante: INV_LOPDP_PORTFOLIO_BY_MEMBERSHIP.

Las pruebas de la API recorren PostgreSQL 16 local con el rol `lopdp_app` (sin BYPASSRLS): los datos
se siembran como dueño y la aplicación consulta con `SET ROLE lopdp_app`. Sin TEST_DATABASE_URL se omiten;
nunca producción. Las pruebas puras (mapeo del sellado) corren sin base.

Prueba de mutación ejecutada en el PostgreSQL 16 local org15-pg16:
- En features/organizacion/services/cartera_engine.py, `armar_cartera` listó TODAS las organizaciones
  (`SELECT id, nombre_comercial, ... FROM tenants`) en lugar de `listar_mis_organizaciones`.
- pytest tests/test_organizacion_cartera.py::test_cartera_por_pertenencia devolvió 1: la cartera de la
  persona incluyó la organización donde no tiene rol (assert B no aparece).
- Se restauró `listar_mis_organizaciones`; sin la mutación las pruebas pasan.
"""
import os
import uuid
from datetime import date, datetime, timedelta, timezone

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

from api.rbac import get_usuario_autenticado  # noqa: E402
from app_core.db.session import fijar_contexto_rls, get_session  # noqa: E402
from app_core.pasillo import diagnostico as pasillo_diagnostico  # noqa: E402
from features.diagnostico.domain.resultados import (  # noqa: E402
    DimensionSellada,
    IndicadoresSellados,
    ResultadoSellado,
)
from features.diagnostico.services.resultados_engine import calcular_huella  # noqa: E402
from main import app  # noqa: E402

RUTA = "/api/v1/organizacion/cartera"
requiere_base = pytest.mark.skipif(not _TEST_URL, reason="TEST_DATABASE_URL no configurada")


# --- Mapeo del último sellado (sin base) -------------------------------------------------------


def _resultado(secuencia: int, huella_anterior: str) -> ResultadoSellado:
    indicadores = IndicadoresSellados(
        cumplimiento=False,
        brechas_criticas=2,
        brechas_altas=3,
        por_dimension=[
            DimensionSellada("D01", "Gobierno", 3, "Definido", 61.0, 100.0, 1, 1),
            DimensionSellada("D02", "Derechos", 1, "Inicial", 20.0, 80.0, 1, 2),
        ],
        respaldo_documental=42.5,
        preguntas_evaluadas=10,
        preguntas_aplicables=12,
        cobertura=83.3,
    )
    resultado = ResultadoSellado(
        id=str(uuid.uuid4()),
        tenant_id="t",
        secuencia=secuencia,
        sellado_por="u",
        sellado_en=datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc),
        normativa="LOPDP",
        version_normativa="1",
        tamano="mediana",
        perfil={},
        respuestas=[],
        indicadores=indicadores,
        huella_anterior=huella_anterior,
    )
    resultado.huella = calcular_huella(resultado.contenido())
    return resultado


def _resumen_con(monkeypatch, resultados):
    from features.diagnostico import diagnostico_service

    async def listar(session, tenant_id, user_id):
        return resultados

    monkeypatch.setattr(diagnostico_service, "listar_resultados", listar)
    return pasillo_diagnostico.resumen_para_cartera(None, "t", "u")


@pytest.mark.asyncio
async def test_resumen_lleva_dimensiones_por_separado_y_sin_cifra_unica(monkeypatch):
    resumen = await _resumen_con(monkeypatch, [_resultado(1, "0" * 64)])
    diag = resumen["diagnostico"]
    assert diag["niveles_por_dimension"] == [{"dimension": "D01", "nivel": 3}, {"dimension": "D02", "nivel": 1}]
    assert (diag["brechas_criticas"], diag["brechas_altas"], diag["respaldo_documental"]) == (2, 3, 42.5)
    assert resumen["cadena_integra"] is True
    assert not {"promedio", "puntaje", "score"} & set(diag)


@pytest.mark.asyncio
async def test_resumen_sin_sellado_es_none_y_cadena_vacia_integra(monkeypatch):
    assert await _resumen_con(monkeypatch, []) == {"diagnostico": None, "cadena_integra": True}


@pytest.mark.asyncio
async def test_resumen_detecta_cadena_alterada(monkeypatch):
    primero = _resultado(1, "0" * 64)
    object.__setattr__(primero.indicadores, "brechas_altas", 99)  # alteración posterior al sellado
    resumen = await _resumen_con(monkeypatch, [primero])
    assert resumen["cadena_integra"] is False


# --- API contra PostgreSQL, con lopdp_app ------------------------------------------------------


@pytest_asyncio.fixture
async def ctx():
    assert "ep-late-hall" not in _TEST_URL, "Se requiere una base local o de pruebas (nunca producción)"
    engine = create_async_engine(_TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    tenants = {clave: f"org15-{clave}-{sufijo}" for clave in ("a", "b", "c")}
    persona, otra = f"org15-persona-{sufijo}", f"org15-otra-{sufijo}"
    async with factory() as s:
        for clave, t in tenants.items():
            await s.execute(text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
                "VALUES (:t, :n, :t, :t, 'mediana')"
            ), {"t": t, "n": f"Organización {clave.upper()}"})
        for uid in (persona, otra):
            await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :u)"),
                            {"u": uid, "e": f"{uid}@correo.invalid"})
        await _rol(s, tenants["a"], persona, "dpo")
        await _rol(s, tenants["b"], persona, "implementador")
        await _rol(s, tenants["c"], otra, "dpo")
        await s.commit()

    async def sesion_de_aplicacion():
        async with factory() as sesion:
            await sesion.execute(text("SET ROLE lopdp_app"))
            try:
                yield sesion
                await sesion.commit()
            except Exception:
                await sesion.rollback()
                raise
            finally:
                await sesion.execute(text("RESET ROLE"))
                await sesion.commit()  # sin esto el RESET ROLE se revierte al cerrar y el rol queda en la conexión

    app.dependency_overrides[get_session] = sesion_de_aplicacion
    app.dependency_overrides[get_usuario_autenticado] = lambda: persona
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield {"client": client, "factory": factory, "t": tenants, "persona": persona, "otra": otra}
    finally:
        app.dependency_overrides.clear()
        async with factory() as s:
            for t in tenants.values():
                await fijar_contexto_rls(s, t)
                for sentencia in (
                    "DELETE FROM roadmap_tasks WHERE tenant_id = :t",
                    "DELETE FROM roadmap_waves WHERE tenant_id = :t",
                    "DELETE FROM roadmaps WHERE tenant_id = :t",
                    "DELETE FROM hallazgos WHERE tenant_id = :t",
                    "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
                ):
                    await s.execute(text(sentencia), {"t": t})
                await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t})
            await s.execute(text("DELETE FROM users WHERE id IN (:p, :o)"), {"p": persona, "o": otra})
            await s.commit()
        await engine.dispose()


async def _rol(s, tenant: str, usuario: str, rol: str) -> None:
    await fijar_contexto_rls(s, tenant)
    await s.execute(text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, :r)"),
                    {"i": str(uuid.uuid4()), "u": usuario, "t": tenant, "r": rol})


async def _hallazgo(ctx, clave: str, referencia: str, estado: str = "abierto") -> None:
    async with ctx["factory"]() as s:
        t = ctx["t"][clave]
        await fijar_contexto_rls(s, t)
        await s.execute(text(
            "INSERT INTO hallazgos (id, tenant_id, origen, origen_ref, severidad, titulo, estado, creado_por) "
            "VALUES (:i, :t, 'auditoria', :ref, 'alta', 'Hallazgo sintético', :e, :u)"
        ), {"i": str(uuid.uuid4()), "t": t, "ref": referencia, "e": estado, "u": ctx["persona"]})
        await s.commit()


async def _tarea(ctx, clave: str, fin: date, estado: str) -> None:
    async with ctx["factory"]() as s:
        t = ctx["t"][clave]
        await fijar_contexto_rls(s, t)
        ola = (await s.execute(text("SELECT id FROM roadmap_waves WHERE tenant_id = :t"), {"t": t})).scalar()
        if ola is None:
            hoja, ola = str(uuid.uuid4()), str(uuid.uuid4())
            await s.execute(text("INSERT INTO roadmaps (id, tenant_id, variables_json) VALUES (:i, :t, '{}')"),
                            {"i": hoja, "t": t})
            await s.execute(text("INSERT INTO roadmap_waves (id, roadmap_id, tenant_id, name) VALUES (:i, :r, :t, 'Ola')"),
                            {"i": ola, "r": hoja, "t": t})
        await s.execute(text(
            "INSERT INTO roadmap_tasks (id, wave_id, tenant_id, control_ref, dimension, title, priority, end_date, status) "
            "VALUES (:i, :w, :t, 'P1', 'D01', 'Tarea sintética', 'alta', :f, :e)"
        ), {"i": str(uuid.uuid4()), "w": ola, "t": t, "f": fin, "e": estado})
        await s.commit()


async def _revocar(ctx, clave: str) -> None:
    async with ctx["factory"]() as s:
        t = ctx["t"][clave]
        await fijar_contexto_rls(s, t)
        await s.execute(text(
            "UPDATE user_tenant_roles SET valid_to = now() - interval '1 day' WHERE tenant_id = :t AND user_id = :u"
        ), {"t": t, "u": ctx["persona"]})
        await s.commit()


def _por_tenant(respuesta) -> dict:
    assert respuesta.status_code == 200, respuesta.text
    return {f["tenant_id"]: f for f in respuesta.json()["organizaciones"]}


@requiere_base
@pytest.mark.asyncio
async def test_cartera_por_pertenencia(ctx):
    """INV_LOPDP_PORTFOLIO_BY_MEMBERSHIP: A y B con rol vigente; tras revocar B, solo A; nunca C."""
    filas = _por_tenant(await ctx["client"].get(RUTA))
    assert set(filas) == {ctx["t"]["a"], ctx["t"]["b"]}
    assert filas[ctx["t"]["a"]]["roles"] == ["dpo"]
    assert filas[ctx["t"]["b"]]["roles"] == ["implementador"]
    await _revocar(ctx, "b")
    assert set(_por_tenant(await ctx["client"].get(RUTA))) == {ctx["t"]["a"]}


@requiere_base
@pytest.mark.asyncio
async def test_cartera_vacia_para_quien_no_pertenece_a_ninguna(ctx):
    app.dependency_overrides[get_usuario_autenticado] = lambda: "org15-sin-roles"
    r = await ctx["client"].get(RUTA)
    assert r.status_code == 200
    assert r.json() == {"organizaciones": []}


@requiere_base
@pytest.mark.asyncio
async def test_cartera_contexto_por_organizacion(ctx):
    """Un hallazgo abierto solo en B no aparece en la fila de A, aunque A y B vayan en la misma respuesta."""
    await _hallazgo(ctx, "b", "ref-1")
    await _hallazgo(ctx, "b", "ref-2")
    await _hallazgo(ctx, "b", "ref-3", estado="cerrado")
    filas = _por_tenant(await ctx["client"].get(RUTA))
    assert filas[ctx["t"]["a"]]["hallazgos_abiertos"] == 0
    assert filas[ctx["t"]["b"]]["hallazgos_abiertos"] == 2


@requiere_base
@pytest.mark.asyncio
async def test_cartera_tareas_vencidas_por_organizacion_en_zona_de_negocio(ctx):
    from app_core.zona_negocio import hoy_negocio

    hoy = hoy_negocio()
    await _tarea(ctx, "a", hoy - timedelta(days=1), "pendiente")      # vencida
    await _tarea(ctx, "a", hoy - timedelta(days=5), "completada")     # completada: no cuenta
    await _tarea(ctx, "a", hoy, "pendiente")                          # vence hoy: no está vencida
    await _tarea(ctx, "b", hoy - timedelta(days=2), "en_progreso")    # vencida, solo de B
    await _tarea(ctx, "b", hoy - timedelta(days=3), "pendiente")      # vencida, solo de B
    filas = _por_tenant(await ctx["client"].get(RUTA))
    assert filas[ctx["t"]["a"]]["tareas_vencidas"] == 1
    assert filas[ctx["t"]["b"]]["tareas_vencidas"] == 2


@requiere_base
@pytest.mark.asyncio
async def test_cartera_sin_diagnostico(ctx):
    filas = _por_tenant(await ctx["client"].get(RUTA))
    for fila in filas.values():
        assert fila["diagnostico"] is None
        assert fila["cadena_integra"] is True
        assert "error" not in fila


@requiere_base
@pytest.mark.asyncio
async def test_cartera_una_organizacion_que_falla_no_tumba_las_demas(ctx, monkeypatch):
    from app_core.pasillo import roadmap as pasillo_roadmap

    original = pasillo_roadmap.contar_hallazgos_abiertos

    async def con_fallo(session, tenant_id, user_id):
        if tenant_id == ctx["t"]["a"]:
            raise RuntimeError("fallo simulado")
        return await original(session, tenant_id, user_id)

    monkeypatch.setattr(pasillo_roadmap, "contar_hallazgos_abiertos", con_fallo)
    filas = _por_tenant(await ctx["client"].get(RUTA))
    assert filas[ctx["t"]["a"]]["error"] == "SIN_DATOS"
    assert filas[ctx["t"]["a"]]["diagnostico"] is None and filas[ctx["t"]["a"]]["hallazgos_abiertos"] is None
    assert filas[ctx["t"]["b"]]["hallazgos_abiertos"] == 0 and "error" not in filas[ctx["t"]["b"]]


def _claves(valor) -> set[str]:
    if isinstance(valor, dict):
        return set(valor) | {c for v in valor.values() for c in _claves(v)}
    if isinstance(valor, list):
        return {c for v in valor for c in _claves(v)}
    return set()


@requiere_base
@pytest.mark.asyncio
async def test_cartera_sin_datos_personales_ni_cifra_unica(ctx):
    await _hallazgo(ctx, "a", "ref-x")
    cuerpo = (await ctx["client"].get(RUTA)).json()
    claves = {c.lower() for c in _claves(cuerpo)}
    assert not {"email", "correo", "promedio", "puntaje", "score", "nombre_usuario"} & claves
    assert "org15-persona" not in str(cuerpo) and ".invalid" not in str(cuerpo)
    assert ctx["t"]["c"] not in str(cuerpo)


@requiere_base
@pytest.mark.asyncio
async def test_cartera_ordenada_por_nombre(ctx):
    nombres = [f["nombre"] for f in (await ctx["client"].get(RUTA)).json()["organizaciones"]]
    assert nombres == sorted(nombres)
