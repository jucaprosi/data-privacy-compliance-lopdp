# ¤roadmap ¤hallazgos ¤rbac-tenant ¤arbitro
"""RM-21: hallazgos con origen y una sola compuerta que los convierte en tareas del plan de acción.

Contrato: governance/especificaciones/RM-21.md (§5 Aceptación). Invariante: INV_LOPDP_SINGLE_ACTION_PLAN
(R7: todo hallazgo que salió de `abierto` tiene exactamente una tarea con su `hallazgo_id`).

Las pruebas puras corren sin base. El resto recorre PostgreSQL real en una rama Neon de revisión
propia (nunca producción ni la rama compartida `test`); sin TEST_DATABASE_URL se omiten.

Prueba de mutación ejecutada en la rama Neon efímera rm-21-efimera (hija de `revision`):
- En features/roadmap/services/hallazgo_engine.py, en el INSERT de crear_tareas_desde_hallazgos,
  se cambió el valor de `hallazgo_id` de `:h` a `NULL` (la tarea se crea sin guardar su origen).
- pytest tests/test_roadmap_hallazgos.py -k "inv_single_action_plan or conversion" devolvió 1:
  test_inv_single_action_plan falló (hallazgos en_tratamiento con 0 tareas de origen) y
  test_conversion_no_duplica también (la segunda conversión duplicó tareas).
- Se restauró `:h`; sin la mutación las pruebas pasan.
"""
import ast
import os
import uuid
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
from features.diagnostico.services.resultados_engine import controles_aplicables, normalizar_perfil  # noqa: E402
from features.roadmap.roadmap_service import (  # noqa: E402
    PATRON_CONTROL,
    origen_ref_diagnostico,
    validar_hallazgo,
)

RAIZ = Path(__file__).resolve().parents[1]
HALLAZGOS = "/api/v1/roadmaps/hallazgos"
DESDE_DIAGNOSTICO = "/api/v1/roadmaps/hallazgos/desde-diagnostico"
RESPUESTAS = "/api/v1/diagnostico/respuestas"
RESULTADOS = "/api/v1/diagnostico/resultados"


def _convertir(roadmap_id: str) -> str:
    return f"/api/v1/roadmaps/{roadmap_id}/hallazgos/convertir"


# --- Pruebas puras --------------------------------------------------------------------------------


@pytest.mark.parametrize("control", ["P1", "P9", "P10", "P73", "P74", "P78", "P80"])
def test_catalogo_de_controles_admite_p1_a_p80(control):
    assert PATRON_CONTROL.match(control)


@pytest.mark.parametrize("control", ["P0", "P01", "P81", "P100", "D01", "p5"])
def test_catalogo_de_controles_rechaza_lo_que_no_es_p1_p80(control):
    assert not PATRON_CONTROL.match(control)
    with pytest.raises(ValueError):
        validar_hallazgo("diagnostico", "ref", "critica", "titulo", control, None)


def test_validacion_de_origen_severidad_y_titulo():
    validar_hallazgo("tercero", "ref", "media", "t" * 200, "P80", "D10")
    for args in (
        ("otro", "ref", "media", "t", None, None),
        ("tercero", "ref", "grave", "t", None, None),
        ("tercero", "ref", "media", "t" * 201, None, None),
        ("tercero", "", "media", "t", None, None),
        ("tercero", "ref", "media", "t", None, "D11"),
    ):
        with pytest.raises(ValueError):
            validar_hallazgo(*args)


def test_clave_de_origen_del_diagnostico():
    assert origen_ref_diagnostico("res-1", 42) == "res-1:P42"


def _sentencias_sql(arbol: ast.AST):
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
            yield nodo.value.lower()


def test_ninguna_otra_sala_inserta_hallazgos_ni_crea_tareas_correctoras():
    """R1 / INV_LOPDP_SINGLE_ACTION_PLAN: solo la sala roadmap escribe en hallazgos y roadmap_tasks."""
    infractores = []
    for archivo in RAIZ.rglob("*.py"):
        relativo = archivo.relative_to(RAIZ).as_posix()
        if relativo.startswith(("features/roadmap/", "alembic/", "tests/", ".venv/", "frontend/", ".worktrees/")):
            continue
        if "/node_modules/" in relativo or "/.venv/" in relativo:
            continue
        try:
            arbol = ast.parse(archivo.read_text(encoding="utf-8-sig"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for sentencia in _sentencias_sql(arbol):
            plano = " ".join(sentencia.split())
            if any(f"insert into {t}" in plano for t in ("hallazgos", "roadmap_tasks")):
                infractores.append(relativo)
    assert not infractores, f"Escriben hallazgos o tareas fuera de la sala roadmap: {sorted(set(infractores))}"


# --- Recorrido contra PostgreSQL ------------------------------------------------------------------


def _h(user: str, tenant: str, role: str) -> dict[str, str]:
    return {"X-User-ID": user, "X-Tenant-ID": tenant, "X-Role": role}


def _respuesta(pregunta: dict) -> dict:
    return {
        "pregunta_id": pregunta["id"], "control": pregunta.get("control", ""), "dimension": pregunta["dimensionId"],
        "estado": "No Conforme", "nivel_evidencia": 0, "criticidad": pregunta["criticidad"],
        "es_critica": False, "riesgo_base": 5,
    }


def _preguntas_del_caso() -> tuple[list[dict], list[dict]]:
    """3 controles que sin evidencia dan brecha CRÍTICA (criticidad >= 4: riesgo 16) y 2 ALTA (criticidad 3: 12)."""
    aplicables = controles_aplicables(cargar_banco_preguntas_raw(), "mediana", normalizar_perfil({}))
    criticas = [p for p in aplicables if int(p["criticidad"]) >= 4][:3]
    altas = [p for p in aplicables if int(p["criticidad"]) == 3][:2]
    assert len(criticas) == 3 and len(altas) == 2
    return criticas, altas


@pytest_asyncio.fixture
async def ctx(monkeypatch):
    if not _TEST_URL:
        pytest.skip("TEST_DATABASE_URL no configurada")
    # Rama Neon de revisión propia: nunca producción.
    assert "ep-late-hall" not in _TEST_URL, "Se requiere una rama de revisión (nunca producción)"
    monkeypatch.setenv("AUTH_MODE", "headers")
    from app_core.db.session import fijar_contexto_rls, get_session
    from features.evidencias import evidencias_service
    from main import app

    engine = create_async_engine(_TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    a, b = (f"rm21-{x}-{sufijo}" for x in "ab")
    usuarios = {
        "dpo": (f"rm21-dpo-{sufijo}", a, "dpo"),
        "impl": (f"rm21-impl-{sufijo}", a, "implementador"),
        "coord": (f"rm21-coord-{sufijo}", a, "coordinador"),
        "admin": (f"rm21-admin-{sufijo}", a, "admin_organizacion"),
        "impl_b": (f"rm21-implb-{sufijo}", b, "implementador"),
    }
    olas = {}
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
        for tenant in (a, b):
            roadmap_id, wave_id = f"rm21-rm-{tenant}", f"rm21-ola-{tenant}"
            await fijar_contexto_rls(s, tenant)
            await s.execute(text(
                "INSERT INTO roadmaps (id, tenant_id, status, variables_json) VALUES (:r, :t, 'active', '{}')"
            ), {"r": roadmap_id, "t": tenant})
            await s.execute(text(
                "INSERT INTO roadmap_waves (id, roadmap_id, tenant_id, name) VALUES (:w, :r, :t, 'Ola 1')"
            ), {"w": wave_id, "r": roadmap_id, "t": tenant})
            olas[tenant] = (roadmap_id, wave_id)
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
            yield {"client": client, "factory": factory, "a": a, "b": b, "u": usuarios, "olas": olas}
    finally:
        app.dependency_overrides.clear()
        evidencias_service.reiniciar_repositorio_evidencias()
        async with factory() as s:
            for t in (a, b):
                await fijar_contexto_rls(s, t)
                for sentencia in (
                    "DELETE FROM roadmap_tasks WHERE tenant_id = :t",
                    "DELETE FROM hallazgos WHERE tenant_id = :t",
                    "DELETE FROM roadmap_waves WHERE tenant_id = :t",
                    "DELETE FROM roadmaps WHERE tenant_id = :t",
                    "DELETE FROM diagnostico_resultados WHERE tenant_id = :t",
                    "DELETE FROM diagnostico_respuestas WHERE tenant_id = :t",
                    "DELETE FROM audit_events WHERE tenant_id = :t",
                    "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
                ):
                    await s.execute(text(sentencia), {"t": t})
                await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t})
            await s.execute(text("DELETE FROM users WHERE id LIKE :p"), {"p": f"rm21-%-{sufijo}"})
            await s.commit()
        await engine.dispose()


def _como(ctx, clave):
    uid, tenant, rol = ctx["u"][clave]
    return _h(uid, tenant, rol)


async def _sellar_caso(ctx) -> None:
    """El DPO responde 3 controles con brecha crítica y 2 con brecha alta, y sella."""
    criticas, altas = _preguntas_del_caso()
    r = await ctx["client"].put(
        RESPUESTAS, headers=_como(ctx, "dpo"), json={"respuestas": [_respuesta(p) for p in criticas + altas]}
    )
    assert r.status_code == 200, r.text
    r = await ctx["client"].post(RESULTADOS, headers=_como(ctx, "dpo"), json={"perfil": {}})
    assert r.status_code == 201, r.text
    assert r.json()["indicadores"]["brechas_criticas"] >= 3


async def _registrar(ctx) -> dict:
    r = await ctx["client"].post(DESDE_DIAGNOSTICO, headers=_como(ctx, "impl"))
    assert r.status_code == 201, r.text
    return r.json()


async def _listar(ctx, clave="impl", **filtros) -> list[dict]:
    r = await ctx["client"].get(HALLAZGOS, headers=_como(ctx, clave), params=filtros)
    assert r.status_code == 200, r.text
    return r.json()["hallazgos"]


async def _convertir_ids(ctx, ids, clave="impl", tenant=None):
    roadmap_id, wave_id = ctx["olas"][tenant or ctx["a"]]
    return await ctx["client"].post(
        _convertir(roadmap_id), headers=_como(ctx, clave), json={"hallazgo_ids": ids, "wave_id": wave_id}
    )


async def _registrar_directo(ctx, **campos) -> str:
    """Registra por la compuerta (como lo hará un productor distinto del diagnóstico)."""
    from features.roadmap import roadmap_service

    uid, tenant, _ = ctx["u"]["impl"]
    async with ctx["factory"]() as s:
        hallazgo_id, creado = await roadmap_service.registrar_hallazgo(s, tenant, uid, **campos)
        await s.commit()
    assert creado
    return hallazgo_id


@pytest.mark.asyncio
async def test_registra_solo_brechas_criticas(ctx):
    await _sellar_caso(ctx)
    assert await _registrar(ctx) == {"creados": 3, "existentes": 0}
    hallazgos = await _listar(ctx)
    assert len(hallazgos) == 3
    criticas, _ = _preguntas_del_caso()
    assert {h["control_ref"] for h in hallazgos} == {f"P{p['id']}" for p in criticas}
    for h in hallazgos:
        assert (h["estado"], h["severidad"], h["origen"], h["tarea_id"]) == ("abierto", "critica", "diagnostico", None)
        assert h["origen_ref"].endswith(f":{h['control_ref']}")
        assert h["dimension"].startswith("D")


@pytest.mark.asyncio
async def test_registro_idempotente(ctx):
    await _sellar_caso(ctx)
    await _registrar(ctx)
    assert await _registrar(ctx) == {"creados": 0, "existentes": 3}
    assert len(await _listar(ctx)) == 3


@pytest.mark.asyncio
async def test_sin_resultado_sellado_responde_diag_sin_resultado(ctx):
    r = await ctx["client"].post(DESDE_DIAGNOSTICO, headers=_como(ctx, "impl_b"))
    assert r.status_code == 404
    assert r.json()["code"] == "DIAG_SIN_RESULTADO"


@pytest.mark.asyncio
async def test_conversion_crea_tareas_con_origen(ctx):
    await _sellar_caso(ctx)
    await _registrar(ctx)
    ids = [h["id"] for h in await _listar(ctx)]
    r = await _convertir_ids(ctx, ids)
    assert r.status_code == 201, r.text
    cuerpo = r.json()
    assert cuerpo["omitidos"] == [] and {t["hallazgo_id"] for t in cuerpo["tareas"]} == set(ids)

    async with ctx["factory"]() as s:
        tareas = (await s.execute(text(
            "SELECT t.hallazgo_id, t.status, t.priority, t.control_ref, t.wave_id, h.control_ref AS h_control "
            "FROM roadmap_tasks t JOIN hallazgos h ON h.id = t.hallazgo_id WHERE t.tenant_id = :t"
        ), {"t": ctx["a"]})).mappings().all()
        eventos = (await s.execute(text(
            "SELECT action, entity_id FROM audit_events WHERE tenant_id = :t AND entity_type = 'hallazgo'"
        ), {"t": ctx["a"]})).mappings().all()
    assert len(tareas) == 3
    for t in tareas:
        assert (t["status"], t["priority"], t["wave_id"]) == ("pendiente", "critica", ctx["olas"][ctx["a"]][1])
        assert t["control_ref"] == t["h_control"]
    assert sorted(e["entity_id"] for e in eventos if e["action"] == "convertido") == sorted(ids)
    assert len([e for e in eventos if e["action"] == "registrado"]) == 3
    assert {h["estado"] for h in await _listar(ctx)} == {"en_tratamiento"}
    assert {h["tarea_id"] for h in await _listar(ctx)} == {t["tarea_id"] for t in cuerpo["tareas"]}


@pytest.mark.asyncio
async def test_conversion_no_duplica(ctx):
    await _sellar_caso(ctx)
    await _registrar(ctx)
    ids = [h["id"] for h in await _listar(ctx)]
    assert (await _convertir_ids(ctx, ids[:1])).status_code == 201
    r = await _convertir_ids(ctx, ids + ids[:1])
    assert r.status_code == 201, r.text
    assert r.json()["omitidos"] == [{"hallazgo_id": ids[0], "motivo": "YA_CONVERTIDO"}]
    assert {t["hallazgo_id"] for t in r.json()["tareas"]} == set(ids[1:])
    async with ctx["factory"]() as s:
        por_hallazgo = (await s.execute(text(
            "SELECT hallazgo_id, count(*) AS n FROM roadmap_tasks WHERE tenant_id = :t GROUP BY hallazgo_id"
        ), {"t": ctx["a"]})).mappings().all()
    assert {f["hallazgo_id"]: f["n"] for f in por_hallazgo} == {i: 1 for i in ids}


@pytest.mark.parametrize("clave", ["dpo", "coord", "admin"])
@pytest.mark.asyncio
async def test_solo_el_implementador_registra_y_convierte(ctx, clave):
    await _sellar_caso(ctx)
    assert (await ctx["client"].post(DESDE_DIAGNOSTICO, headers=_como(ctx, clave))).status_code == 403
    await _registrar(ctx)
    ids = [h["id"] for h in await _listar(ctx)]
    assert (await _convertir_ids(ctx, ids, clave=clave)).status_code == 403
    assert len(await _listar(ctx, clave=clave)) == 3


@pytest.mark.asyncio
async def test_dpo_consulta_y_no_convierte(ctx):
    await _sellar_caso(ctx)
    await _registrar(ctx)
    ids = [h["id"] for h in await _listar(ctx, clave="dpo")]
    assert len(ids) == 3
    assert (await _convertir_ids(ctx, ids, clave="dpo")).status_code == 403
    assert {h["estado"] for h in await _listar(ctx, clave="dpo")} == {"abierto"}


@pytest.mark.asyncio
async def test_errores_de_conversion(ctx):
    hallazgo_id = await _registrar_directo(
        ctx, origen="auditoria", origen_ref="aud-1", severidad="alta", titulo="Hallazgo de auditoría", control_ref="P5"
    )
    roadmap_id, wave_id = ctx["olas"][ctx["a"]]
    _, ola_b = ctx["olas"][ctx["b"]]
    cliente, cab = ctx["client"], _como(ctx, "impl")

    r = await cliente.post(_convertir(roadmap_id), headers=cab, json={"hallazgo_ids": [hallazgo_id], "wave_id": ola_b})
    assert (r.status_code, r.json()["code"]) == (404, "ROADMAP_NO_ENCONTRADO")
    r = await cliente.post(_convertir("no-existe"), headers=cab, json={"hallazgo_ids": [hallazgo_id], "wave_id": wave_id})
    assert (r.status_code, r.json()["code"]) == (404, "ROADMAP_NO_ENCONTRADO")
    r = await cliente.post(
        _convertir(roadmap_id), headers=cab, json={"hallazgo_ids": [hallazgo_id, "no-existe"], "wave_id": wave_id}
    )
    assert (r.status_code, r.json()["code"]) == (404, "HALLAZGO_NO_ENCONTRADO")
    for cuerpo in (
        {"hallazgo_ids": [], "wave_id": wave_id},
        {"hallazgo_ids": [str(i) for i in range(101)], "wave_id": wave_id},
        {"hallazgo_ids": [hallazgo_id]},
    ):
        assert (await cliente.post(_convertir(roadmap_id), headers=cab, json=cuerpo)).status_code == 422
    # Todo o nada: el pedido con un id inexistente no convirtió el válido.
    assert {h["estado"] for h in await _listar(ctx)} == {"abierto"}

    async with ctx["factory"]() as s:
        await s.execute(text("UPDATE hallazgos SET estado = 'cerrado' WHERE id = :h"), {"h": hallazgo_id})
        await s.commit()
    r = await _convertir_ids(ctx, [hallazgo_id])
    assert (r.status_code, r.json()["code"]) == (409, "HALLAZGO_CERRADO")


@pytest.mark.asyncio
async def test_el_cuerpo_no_fija_organizacion_autor_ni_fechas(ctx):
    hallazgo_id = await _registrar_directo(
        ctx, origen="tercero", origen_ref="ter-1", severidad="media", titulo="Proveedor sin contrato", control_ref="P3"
    )
    roadmap_id, wave_id = ctx["olas"][ctx["a"]]
    for extra in ({"tenant_id": ctx["b"]}, {"creado_por": "otra-persona"}, {"estado": "cerrado"},
                  {"creado_en": "2020-01-01T00:00:00Z"}):
        r = await ctx["client"].post(
            _convertir(roadmap_id), headers=_como(ctx, "impl"),
            json={"hallazgo_ids": [hallazgo_id], "wave_id": wave_id, **extra},
        )
        assert r.status_code == 422, extra
    # Otra organización no ve ni convierte el hallazgo de A, aunque conozca su id.
    r = await _convertir_ids(ctx, [hallazgo_id], clave="impl_b", tenant=ctx["b"])
    assert (r.status_code, r.json()["code"]) == (404, "HALLAZGO_NO_ENCONTRADO")
    async with ctx["factory"]() as s:
        fila = (await s.execute(text("SELECT tenant_id, creado_por FROM hallazgos WHERE id = :h"),
                                {"h": hallazgo_id})).mappings().one()
    assert (fila["tenant_id"], fila["creado_por"]) == (ctx["a"], ctx["u"]["impl"][0])


@pytest.mark.asyncio
async def test_control_p74_p80_convertible(ctx):
    hallazgo_id = await _registrar_directo(
        ctx, origen="control_periodico", origen_ref="cp-78", severidad="alta",
        titulo="Control P78 vencido", control_ref="P78", dimension="D10",
    )
    r = await _convertir_ids(ctx, [hallazgo_id])
    assert r.status_code == 201, r.text
    async with ctx["factory"]() as s:
        control = (await s.execute(text("SELECT control_ref FROM roadmap_tasks WHERE hallazgo_id = :h"),
                                   {"h": hallazgo_id})).scalar_one()
        definicion = (await s.execute(text(
            "SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'ck_tasks_control_ref'"
        ))).scalar_one()
    assert control == "P78"
    assert "80" in definicion and "7[0-3]" not in definicion


async def _como_app(s: AsyncSession, tenant: str) -> None:
    from app_core.db.session import fijar_contexto_rls

    await s.execute(text("SET LOCAL ROLE lopdp_app"))
    await fijar_contexto_rls(s, tenant)


@pytest.mark.asyncio
async def test_rls_hallazgos(ctx):
    from features.roadmap import roadmap_service

    hallazgo_id = await _registrar_directo(
        ctx, origen="eipd", origen_ref="eipd-1", severidad="critica", titulo="EIPD sin medidas", control_ref="P40"
    )
    async with ctx["factory"]() as s:
        assert (await s.execute(text(
            "SELECT rolbypassrls FROM pg_roles WHERE rolname = 'lopdp_app'"
        ))).scalar_one() is False
        await _como_app(s, ctx["b"])
        assert (await s.execute(text("SELECT count(*) FROM hallazgos"))).scalar_one() == 0
        assert (await s.execute(text("SELECT count(*) FROM hallazgos WHERE id = :h"), {"h": hallazgo_id})).scalar_one() == 0
        await s.rollback()

        # Con lopdp_app y el contexto de A, la compuerta registra y convierte con los permisos mínimos.
        await _como_app(s, ctx["a"])
        assert (await s.execute(text("SELECT count(*) FROM hallazgos"))).scalar_one() == 1
        uid = ctx["u"]["impl"][0]
        roadmap_id, wave_id = ctx["olas"][ctx["a"]]
        _, creado = await roadmap_service.registrar_hallazgo(
            s, ctx["a"], uid, origen="eipd", origen_ref="eipd-2", severidad="media", titulo="Otro", control_ref="P41"
        )
        assert creado
        conversion = await roadmap_service.crear_tareas_desde_hallazgos(s, ctx["a"], uid, roadmap_id, wave_id, [hallazgo_id])
        assert len(conversion.tareas) == 1
        await s.commit()

    # Sin DELETE ni UPDATE de columnas distintas de estado/actualizado_en para la aplicación.
    for sentencia in ("DELETE FROM hallazgos WHERE id = :h", "UPDATE hallazgos SET titulo = 'x' WHERE id = :h"):
        async with ctx["factory"]() as s:
            await _como_app(s, ctx["a"])
            with pytest.raises(DBAPIError, match="permission denied"):
                await s.execute(text(sentencia), {"h": hallazgo_id})
            await s.rollback()
    # Insertar en nombre de otra organización lo rechaza WITH CHECK.
    async with ctx["factory"]() as s:
        await _como_app(s, ctx["a"])
        with pytest.raises(DBAPIError, match="row-level security"):
            await s.execute(text(
                "INSERT INTO hallazgos (id, tenant_id, origen, origen_ref, severidad, titulo, creado_por) "
                "VALUES (:i, :t, 'eipd', 'x', 'media', 'x', 'x')"
            ), {"i": str(uuid.uuid4()), "t": ctx["b"]})
        await s.rollback()


@pytest.mark.asyncio
async def test_inv_single_action_plan(ctx):
    """INV_LOPDP_SINGLE_ACTION_PLAN (R7): tras convertir, todo hallazgo fuera de `abierto` tiene
    exactamente una tarea con su origen y no queda ningún hallazgo abierto sin tarea."""
    await _sellar_caso(ctx)
    await _registrar(ctx)
    await _registrar_directo(
        ctx, origen="incidente", origen_ref="inc-1", severidad="alta", titulo="Vulneración", control_ref="P78"
    )
    abiertos = [h["id"] for h in await _listar(ctx, estado="abierto")]
    assert len(abiertos) == 4
    assert (await _convertir_ids(ctx, abiertos)).status_code == 201
    assert (await _convertir_ids(ctx, abiertos)).status_code == 201  # repetir no rompe el invariante

    async with ctx["factory"]() as s:
        violaciones = (await s.execute(text(
            "SELECT h.id, h.estado, count(t.id) AS tareas FROM hallazgos h "
            "LEFT JOIN roadmap_tasks t ON t.hallazgo_id = h.id "
            "WHERE h.tenant_id = :t GROUP BY h.id, h.estado "
            "HAVING (h.estado <> 'abierto' AND count(t.id) <> 1) OR (h.estado = 'abierto' AND count(t.id) = 0)"
        ), {"t": ctx["a"]})).mappings().all()
        sin_origen = (await s.execute(text(
            "SELECT count(*) FROM roadmap_tasks WHERE tenant_id = :t AND hallazgo_id IS NULL"
        ), {"t": ctx["a"]})).scalar_one()
    assert not violaciones, f"Hallazgos que violan R7: {[dict(v) for v in violaciones]}"
    assert sin_origen == 0
    assert await _listar(ctx, estado="abierto") == []
