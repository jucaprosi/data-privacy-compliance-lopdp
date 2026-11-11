# ¤diagnostico ¤diagnostico-estados ¤diagnostico-comparativo ¤roadmap ¤arbitro
"""DIAG-12: estados del diagnóstico, el assessment actual a partir del diagnóstico real.

Un estado parte de los niveles del real y suma solo las tareas cerradas con evidencia validada por cuatro
ojos; sin cifra única. Las pruebas de motor no usan base de datos; el recorrido corre contra PostgreSQL 16
local (TEST_DATABASE_URL; sin ella se omite) y nunca contra producción.

Prueba de mutación documentada: en `app_core/pasillo/roadmap.py#DIAG-12` se quitó de la consulta la
condición `EXISTS (... validation_status = 'approved' ...)` para contar también las tareas cerradas sin
evidencia validada; `pytest tests/test_diag12_estados.py::test_un_estado_suma_solo_tareas_con_evidencia_validada`
devolvió FAILED (el control P3, cerrado con evidencia pendiente, pasó a Conforme). Se restauró la consulta;
sin la mutación pasa.
"""
import os
import uuid
from datetime import datetime, timezone

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

from features.diagnostico.domain.resultados import (  # noqa: E402
    DimensionSellada,
    IndicadoresSellados,
    RespuestaSellada,
    ResultadoSellado,
)
from features.diagnostico.services.estados_engine import NIVEL_POR_CIERRE, sumar_tareas  # noqa: E402

ESTADOS = "/api/v1/diagnostico/estados"
RESPUESTAS = "/api/v1/diagnostico/respuestas"
RESULTADOS = "/api/v1/diagnostico/resultados"


# --- Motor (sin base de datos) -------------------------------------------------------------------


def _real_sellado(niveles: dict[int, int]) -> ResultadoSellado:
    respuestas = [
        RespuestaSellada(pregunta_id=pid, control=f"c{pid}", dimension="D01", estado="x", criticidad=3,
                         nivel_declarado=2, nivel_sellado=2, con_documento=False, nivel_asignado=nivel)
        for pid, nivel in niveles.items()
    ]
    return ResultadoSellado(
        id="real", tenant_id="t", secuencia=2, sellado_por="u", sellado_en=datetime(2026, 1, 2, tzinfo=timezone.utc),
        normativa="LOPDP", version_normativa="v", tamano="corporativo", perfil={}, respuestas=respuestas,
        indicadores=IndicadoresSellados(
            cumplimiento=True, brechas_criticas=0, brechas_altas=0,
            por_dimension=[DimensionSellada("D01", "n", 1, "x", 0.0, 0.0, 0, 0)],
            respaldo_documental=0.0, preguntas_evaluadas=len(niveles), preguntas_aplicables=len(niveles), cobertura=0.0,
        ),
    )


def _nivel_de(selladas: list[RespuestaSellada], pid: int) -> int | None:
    return next(r.nivel_asignado for r in selladas if r.pregunta_id == pid)


def test_la_suma_sube_a_conforme_sin_bajar_ni_llegar_a_cinco():
    real = _real_sellado({1: 1, 2: 5, 3: 2, 4: 4})
    _, selladas = sumar_tareas(real, [{"control_ref": "P1"}, {"control_ref": "P2"}, {"control_ref": "P4"}])
    assert _nivel_de(selladas, 1) == NIVEL_POR_CIERRE == 4
    assert _nivel_de(selladas, 2) == 5  # nunca baja
    assert _nivel_de(selladas, 3) == 2  # sin tarea validada no cambia
    assert _nivel_de(selladas, 4) == 4


def test_sin_tareas_el_estado_repite_los_niveles_del_real_y_no_hay_cifra_global():
    real = _real_sellado({1: 1, 2: 3})
    indicadores, selladas = sumar_tareas(real, [])
    assert [(r.pregunta_id, r.nivel_asignado) for r in selladas] == [(1, 1), (2, 3)]
    assert not {"avance", "avance_global", "madurez"} & set(indicadores.__dict__)


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
    a, b = f"diag12-a-{sufijo}", f"diag12-b-{sufijo}"
    usuarios = {
        "dpo": (f"diag12-dpo-{sufijo}", a, "dpo"),
        "impl": (f"diag12-impl-{sufijo}", a, "implementador"),
        "coord": (f"diag12-coord-{sufijo}", a, "coordinador"),
        "resp": (f"diag12-resp-{sufijo}", a, "responsable_area"),
        "dpo_b": (f"diag12-dpob-{sufijo}", b, "dpo"),
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
            yield {"client": client, "factory": factory, "a": a, "b": b, "u": usuarios, "sufijo": sufijo}
    finally:
        app.dependency_overrides.clear()
        async with factory() as s:
            for t in (a, b):
                await fijar_contexto_rls(s, t)
                for sentencia in (
                    "DELETE FROM task_evidence WHERE tenant_id = :t",
                    "DELETE FROM roadmap_tasks WHERE tenant_id = :t",
                    "DELETE FROM roadmap_waves WHERE tenant_id = :t",
                    "DELETE FROM roadmaps WHERE tenant_id = :t",
                    "DELETE FROM diagnostico_estados WHERE tenant_id = :t",
                    "DELETE FROM diagnostico_resultados WHERE tenant_id = :t",
                    "DELETE FROM diagnostico_respuestas WHERE tenant_id = :t",
                    "DELETE FROM audit_events WHERE tenant_id = :t",
                    "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
                ):
                    await s.execute(text(sentencia), {"t": t})
                await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t})
            await s.execute(text("DELETE FROM users WHERE id LIKE :p"), {"p": f"diag12-%-{sufijo}"})
            await s.commit()
        await engine.dispose()


def _como(ctx, clave):
    uid, tenant, rol = ctx["u"][clave]
    return _h(uid, tenant, rol)


async def _responder_y_sellar(ctx, *respuestas):
    c = ctx["client"]
    r = await c.put(RESPUESTAS, headers=_como(ctx, "dpo"), json={"respuestas": list(respuestas)})
    assert r.status_code == 200, r.text
    r = await c.post(RESULTADOS, headers=_como(ctx, "dpo"), json={"perfil": {}})
    assert r.status_code == 201, r.text


async def _sembrar_tarea(ctx, control_ref, *, estado="completada", evidencia=None):
    """Tarea de la hoja de ruta de la organización A; `evidencia` es (estado, sube, valida) o None."""
    from app_core.db.session import fijar_contexto_rls

    a = ctx["a"]
    async with ctx["factory"]() as s:
        await fijar_contexto_rls(s, a)
        raiz = {"r": f"r-{ctx['sufijo']}", "w": f"w-{ctx['sufijo']}"}
        await s.execute(text(
            "INSERT INTO roadmaps (id, tenant_id, variables_json) VALUES (:r, :t, '{}') ON CONFLICT DO NOTHING"
        ), {"r": raiz["r"], "t": a})
        await s.execute(text(
            "INSERT INTO roadmap_waves (id, roadmap_id, tenant_id, name) VALUES (:w, :r, :t, 'Ola 1') "
            "ON CONFLICT DO NOTHING"
        ), {"w": raiz["w"], "r": raiz["r"], "t": a})
        tarea = str(uuid.uuid4())
        await s.execute(text(
            "INSERT INTO roadmap_tasks (id, wave_id, tenant_id, control_ref, dimension, title, priority, status, "
            "completed_at) VALUES (:i, :w, :t, :c, 'D01', 'Tarea simulada', 'alta', CAST(:e AS varchar), "
            "CASE WHEN CAST(:e AS varchar) = 'completada' THEN now() END)"
        ), {"i": tarea, "w": raiz["w"], "t": a, "c": control_ref, "e": estado})
        if evidencia:
            validacion, sube, valida = evidencia
            await s.execute(text(
                "INSERT INTO task_evidence (id, task_id, tenant_id, r2_key, uploaded_by, validation_status, "
                "validated_by) VALUES (:i, :tk, :t, 'simulada/clave', :u, :v, :vb)"
            ), {"i": str(uuid.uuid4()), "tk": tarea, "t": a, "u": ctx["u"][sube][0], "v": validacion,
                "vb": ctx["u"][valida][0] if valida else None})
        await s.commit()
    return tarea


@pytest.mark.asyncio
async def test_sin_diagnostico_real_sellado_es_409(ctx):
    c = ctx["client"]
    r = await c.post(ESTADOS, headers=_como(ctx, "dpo"))
    assert r.status_code == 409 and r.json()["code"] == "DIAG_ESTADO_SIN_DIAGNOSTICO_REAL"
    await _responder_y_sellar(ctx, _respuesta(1, 1))  # solo el de prueba
    r = await c.post(ESTADOS, headers=_como(ctx, "dpo"))
    assert r.status_code == 409 and r.json()["code"] == "DIAG_ESTADO_SIN_DIAGNOSTICO_REAL"


@pytest.mark.asyncio
async def test_un_estado_suma_solo_tareas_con_evidencia_validada(ctx):
    c = ctx["client"]
    await _responder_y_sellar(ctx, _respuesta(1, 1), _respuesta(2, 1), _respuesta(3, 1), _respuesta(6, 1), _respuesta(5, 1))
    await _responder_y_sellar(ctx, _respuesta(1, 1), _respuesta(2, 1), _respuesta(3, 1), _respuesta(6, 1), _respuesta(5, 1))
    await _sembrar_tarea(ctx, "P1", evidencia=("approved", "impl", "dpo"))   # cuenta
    await _sembrar_tarea(ctx, "P2", evidencia=("rejected", "impl", "dpo"))   # evidencia rechazada (la base ya impide que valide quien la subió)
    await _sembrar_tarea(ctx, "P3", evidencia=("pending", "impl", None))     # evidencia sin validar
    await _sembrar_tarea(ctx, "P6")                                          # sin evidencia
    await _sembrar_tarea(ctx, "P5", estado="en_progreso", evidencia=("approved", "impl", "dpo"))  # no cerrada

    r = await c.post(ESTADOS, headers=_como(ctx, "dpo"))
    assert r.status_code == 201, r.text
    estado = r.json()
    niveles = {x["pregunta_id"]: x["nivel_asignado"] for x in estado["respuestas"]}
    assert niveles == {1: 4, 2: 1, 3: 1, 6: 1, 5: 1}
    assert [t["control_ref"] for t in estado["tareas"]] == ["P1"]
    assert estado["secuencia"] == 1 and estado["emitido_por"] == ctx["u"]["dpo"][0]


@pytest.mark.asyncio
async def test_emitir_un_estado_no_cambia_el_diagnostico_sellado(ctx):
    c = ctx["client"]
    await _responder_y_sellar(ctx, _respuesta(1, 1))
    await _responder_y_sellar(ctx, _respuesta(1, 1))
    antes = (await c.get(RESULTADOS, headers=_como(ctx, "dpo"))).json()
    await _sembrar_tarea(ctx, "P1", evidencia=("approved", "impl", "dpo"))
    assert (await c.post(ESTADOS, headers=_como(ctx, "dpo"))).status_code == 201
    assert (await c.post(ESTADOS, headers=_como(ctx, "dpo"))).status_code == 201
    despues = (await c.get(RESULTADOS, headers=_como(ctx, "dpo"))).json()
    assert antes == despues and despues["cadena_integra"] is True


@pytest.mark.asyncio
async def test_historial_cadena_y_comparativos(ctx):
    c = ctx["client"]
    await _responder_y_sellar(ctx, _respuesta(1, 1), _respuesta(2, 1))
    await _responder_y_sellar(ctx, _respuesta(1, 1), _respuesta(2, 1))
    primero = (await c.post(ESTADOS, headers=_como(ctx, "dpo"))).json()
    await _sembrar_tarea(ctx, "P1", evidencia=("approved", "impl", "dpo"))
    segundo = (await c.post(ESTADOS, headers=_como(ctx, "dpo"))).json()
    assert segundo["huella_anterior"] == primero["huella"] and segundo["secuencia"] == 2

    historial = (await c.get(ESTADOS, headers=_como(ctx, "coord"))).json()
    assert [e["secuencia"] for e in historial["estados"]] == [2, 1] and historial["cadena_integra"] is True

    con_real = (await c.get(f"{ESTADOS}/{segundo['id']}/comparativo", headers=_como(ctx, "impl"))).json()
    assert [x["pregunta_id"] for x in con_real["brechas"]["cerradas"]] == [1]
    assert [x["pregunta_id"] for x in con_real["brechas"]["siguen"]] == [2]
    assert (con_real["linea_base"]["tipo"], con_real["actual"]["tipo"]) == ("real", "estado")

    con_anterior = (await c.get(f"{ESTADOS}/{segundo['id']}/comparativo?con=anterior", headers=_como(ctx, "impl"))).json()
    assert [x["pregunta_id"] for x in con_anterior["brechas"]["cerradas"]] == [1]
    assert con_anterior["linea_base"]["id"] == primero["id"]

    r = await c.get(f"{ESTADOS}/{primero['id']}/comparativo?con=anterior", headers=_como(ctx, "impl"))
    assert r.status_code == 409 and r.json()["code"] == "DIAG_ESTADO_SIN_ANTERIOR"
    r = await c.get(f"{ESTADOS}/no-existe/comparativo", headers=_como(ctx, "impl"))
    assert r.status_code == 404


@pytest.mark.parametrize("clave", ["impl", "coord", "resp"])
@pytest.mark.asyncio
async def test_solo_el_dpo_emite(ctx, clave):
    r = await ctx["client"].post(ESTADOS, headers=_como(ctx, clave))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_roles_sin_permiso_no_consultan(ctx):
    assert (await ctx["client"].get(ESTADOS, headers=_como(ctx, "resp"))).status_code == 403


@pytest.mark.asyncio
async def test_rls_entre_organizaciones_y_lopdp_app_no_modifica(ctx):
    from app_core.db.session import fijar_contexto_rls

    c = ctx["client"]
    await _responder_y_sellar(ctx, _respuesta(1, 1))
    await _responder_y_sellar(ctx, _respuesta(1, 1))
    estado = (await c.post(ESTADOS, headers=_como(ctx, "dpo"))).json()
    assert (await c.get(ESTADOS, headers=_como(ctx, "dpo_b"))).json()["estados"] == []
    assert (await c.get(f"{ESTADOS}/{estado['id']}/comparativo", headers=_como(ctx, "dpo_b"))).status_code in (404, 409)

    async with ctx["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, ctx["b"])
        assert (await s.execute(text("SELECT count(*) FROM diagnostico_estados"))).scalar_one() == 0
    for sentencia in (
        "UPDATE diagnostico_estados SET escala = 'x' WHERE id = :id",
        "DELETE FROM diagnostico_estados WHERE id = :id",
    ):
        async with ctx["factory"]() as s:
            await s.execute(text("SET LOCAL ROLE lopdp_app"))
            await fijar_contexto_rls(s, ctx["a"])
            with pytest.raises(DBAPIError) as error:
                await s.execute(text(sentencia), {"id": estado["id"]})
            assert error.value.orig.sqlstate == "42501"
            await s.rollback()
