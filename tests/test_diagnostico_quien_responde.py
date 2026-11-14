# ¤diagnostico ¤dpo-independencia ¤rbac-tenant ¤arbitro
"""DIAG-07: quién responde, quién objeta y cuándo se puede sellar.

Recorrido real contra PostgreSQL 16. Sin TEST_DATABASE_URL las pruebas se omiten. Solo valores generados y
correos `.invalid`. Cubre las objeciones (motor y RLS), quién escribe (R1), el bloqueo del sello con
objeciones abiertas (R3), la concurrencia del candado advisory compartido con el sello y la inmutabilidad
del sello para `lopdp_app`. Cada prueba documenta la mutación que la pone en rojo.
"""
import asyncio
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


# --- API: objetar y sellar ---------------------------------------------------------------------

OBJECIONES = "/api/v1/diagnostico/objeciones"
RESPUESTAS = "/api/v1/diagnostico/respuestas"
RESULTADOS = "/api/v1/diagnostico/resultados"


def _h(user: str, tenant: str, role: str) -> dict[str, str]:
    return {"X-User-ID": user, "X-Tenant-ID": tenant, "X-Role": role}


def _respuesta(pregunta_id: int, dimension: str = "D01") -> dict:
    return {
        "pregunta_id": pregunta_id, "control": "Control del banco", "dimension": dimension, "nivel_asignado": 4,
        "nivel_evidencia": 2, "criticidad": 3, "es_critica": False, "riesgo_base": 5,
    }


@pytest_asyncio.fixture
async def api(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    from httpx import ASGITransport, AsyncClient

    from app_core.db.session import get_session
    from main import app

    engine = create_async_engine(_url(), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    a = f"obj-api-{sufijo}"
    usuarios = {
        "dpo": (f"obj-dpo-{sufijo}", a, "dpo"),
        "admin": (f"obj-admin-{sufijo}", a, "admin_organizacion"),
        "impl": (f"obj-impl-{sufijo}", a, "implementador"),
        "coord": (f"obj-coord-{sufijo}", a, "coordinador"),
        "resp": (f"obj-resp-{sufijo}", a, "responsable_area"),
    }
    async with factory() as s:
        await s.execute(text(
            "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
            "VALUES (:t, :t, :t, :t, 'mediana')"
        ), {"t": a})
        for uid, tenant, rol in usuarios.values():
            await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :u)"),
                            {"u": uid, "e": f"{uid}@example.invalid"})
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
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield {"client": client, "a": a, "u": usuarios, "factory": factory}
    app.dependency_overrides.clear()
    async with factory() as s:
        await fijar_contexto_rls(s, a)
        for sentencia in (
            "DELETE FROM diagnostico_objeciones WHERE tenant_id = :t",
            "DELETE FROM diagnostico_resultados WHERE tenant_id = :t",
            "DELETE FROM diagnostico_respuestas WHERE tenant_id = :t",
            "DELETE FROM diagnostico_asignaciones WHERE tenant_id = :t",
            "DELETE FROM audit_events WHERE tenant_id = :t",
            "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
        ):
            await s.execute(text(sentencia), {"t": a})
        await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": a})
        await s.execute(text("DELETE FROM users WHERE id LIKE :p"), {"p": f"obj-%-{sufijo}"})
        await s.commit()
    await engine.dispose()


def _como(api, clave):
    uid, tenant, rol = api["u"][clave]
    return _h(uid, tenant, rol)


@pytest.mark.parametrize("clave", ["admin", "impl", "coord", "resp"])
async def test_solo_el_dpo_objeta(api, clave):
    r = await api["client"].post(OBJECIONES, headers=_como(api, clave), json={"pregunta_id": 12, "motivo": MOTIVO})
    assert r.status_code == 403


async def test_objetar_y_listar_por_api(api):
    c = api["client"]
    dpo = _como(api, "dpo")
    corto = await c.post(OBJECIONES, headers=dpo, json={"pregunta_id": 12, "motivo": "corto"})
    assert corto.status_code == 422
    r = await c.post(OBJECIONES, headers=dpo, json={"pregunta_id": 12, "motivo": MOTIVO})
    assert r.status_code == 201 and r.json()["resuelta_en"] is None
    repetida = await c.post(OBJECIONES, headers=dpo, json={"pregunta_id": 12, "motivo": MOTIVO})
    assert repetida.status_code == 409 and repetida.json()["code"] == "OBJECION_DUPLICADA"
    for lector in ("dpo", "admin", "impl", "coord", "resp"):
        filas = (await c.get(f"{OBJECIONES}?abiertas=true", headers=_como(api, lector))).json()["objeciones"]
        assert [f["pregunta_id"] for f in filas] == [12]


async def _asignar(api, dimension: str, clave: str) -> None:
    async with api["factory"]() as s:
        await fijar_contexto_rls(s, api["a"])
        await s.execute(text(
            "INSERT INTO diagnostico_asignaciones (id, tenant_id, dimension, responsable_user_id, asignado_por) "
            "VALUES (:i, :t, :d, :r, :p)"
        ), {"i": str(uuid.uuid4()), "t": api["a"], "d": dimension, "r": api["u"][clave][0],
            "p": api["u"]["admin"][0]})
        await s.commit()


# --- R1 · Quién escribe -------------------------------------------------------------------------

async def test_dpo_no_responde(api):
    """El dpo recibe 403 al guardar; el administrador guarda en cualquier dimensión.

    Mutación: dejar que `_escritura` acepte al `dpo` y quitar su rechazo en el motor → el 403 pasa a 200.
    """
    c = api["client"]
    r = await c.put(RESPUESTAS, headers=_como(api, "dpo"), json={"respuestas": [_respuesta(12)]})
    assert r.status_code == 403
    lote = [_respuesta(12, "D01"), _respuesta(30, "D04"), _respuesta(70, "D10")]
    r = await c.put(RESPUESTAS, headers=_como(api, "admin"), json={"respuestas": lote})
    assert r.status_code == 200, r.text


@pytest.mark.parametrize("clave", ["impl", "coord"])
async def test_sin_asignacion_no_responde(api, clave):
    """Un rol vigente sin dimensión asignada no guarda (403 del motor).

    Mutación: que `exigir_puede_escribir` devuelva sin comprobar → 200.
    """
    r = await api["client"].put(RESPUESTAS, headers=_como(api, clave), json={"respuestas": [_respuesta(12)]})
    assert r.status_code == 403 and r.json()["code"] == "RESPUESTA_FUERA_DE_ASIGNACION"


async def test_encargado_solo_su_dimension(api):
    """Un implementador asignado a D04 guarda en D04 y recibe 403 en D07.

    Mutación: quitar la comprobación `dimensiones <= propias` → el 403 de D07 pasa a 200.
    """
    await _asignar(api, "D04", "impl")
    c, impl = api["client"], _como(api, "impl")
    propia = await c.put(RESPUESTAS, headers=impl, json={"respuestas": [_respuesta(30, "D04")]})
    assert propia.status_code == 200, propia.text
    ajena = await c.put(RESPUESTAS, headers=impl, json={"respuestas": [_respuesta(55, "D07")]})
    assert ajena.status_code == 403 and ajena.json()["code"] == "RESPUESTA_FUERA_DE_ASIGNACION"


async def test_lote_mixto_se_rechaza_entero(api):
    """Un lote con una dimensión propia y una ajena no guarda ninguna.

    Mutación: comprobar solo la primera dimensión del lote, o guardar antes de comprobar → la 31 queda guardada.
    """
    await _asignar(api, "D04", "impl")
    c = api["client"]
    lote = [_respuesta(31, "D04"), _respuesta(55, "D07")]
    r = await c.put(RESPUESTAS, headers=_como(api, "impl"), json={"respuestas": lote})
    assert r.status_code == 403
    guardadas = (await c.get(RESPUESTAS, headers=_como(api, "admin"))).json()["respuestas"]
    assert all(g["pregunta_id"] != 31 for g in guardadas)


# --- R3 · Sello sin objeciones abiertas ---------------------------------------------------------

async def test_sello_sin_objeciones(api):
    """Con la 12 objetada el sello da 409; el administrador la vuelve a guardar y el DPO sella.

    Mutación: quitar la llamada a `objeciones_abiertas` en `sellar` → el primer sello da 201.
    """
    c = api["client"]
    dpo, admin = _como(api, "dpo"), _como(api, "admin")
    assert (await c.put(RESPUESTAS, headers=admin, json={"respuestas": [_respuesta(12)]})).status_code == 200
    assert (await c.post(OBJECIONES, headers=dpo, json={"pregunta_id": 12, "motivo": MOTIVO})).status_code == 201

    bloqueado = await c.post(RESULTADOS, headers=dpo, json={"perfil": {}})
    assert bloqueado.status_code == 409 and bloqueado.json()["code"] == "OBJECIONES_ABIERTAS", bloqueado.text

    assert (await c.put(RESPUESTAS, headers=admin, json={"respuestas": [_respuesta(12)]})).status_code == 200
    assert (await c.get(f"{OBJECIONES}?abiertas=true", headers=dpo)).json()["objeciones"] == []
    sellado = await c.post(RESULTADOS, headers=dpo, json={"perfil": {}})
    assert sellado.status_code == 201, sellado.text


# --- Concurrencia: el candado advisory del sello --------------------------------------------------

ESPERA = 0.6


async def _retener_candado(api) -> AsyncSession:
    """Una sesión aparte toma el candado del sello y lo retiene, como una transacción en vuelo."""
    s = api["factory"]()
    await fijar_contexto_rls(s, api["a"])
    await s.execute(text("SELECT pg_advisory_xact_lock(hashtext(:c))"),
                    {"c": objeciones_engine.clave_candado_sello(api["a"])})
    return s


async def test_dos_sellos_simultaneos_solo_uno_gana(api):
    """Con un sello ya hecho, dos sellos a la vez: uno crea el eslabón 2 y el otro recibe 409 DIAG_SELLOS_AGOTADOS.

    Mutación: quitar el `pg_advisory_xact_lock` del sello → ambos leen la secuencia 1, chocan en la
    restricción única y el perdedor sale con un error de integridad, no con 409.
    """
    c = api["client"]
    dpo, admin = _como(api, "dpo"), _como(api, "admin")
    assert (await c.put(RESPUESTAS, headers=admin, json={"respuestas": [_respuesta(12)]})).status_code == 200
    assert (await c.post(RESULTADOS, headers=dpo, json={"perfil": {}})).status_code == 201

    retenida = await _retener_candado(api)
    uno = asyncio.create_task(c.post(RESULTADOS, headers=dpo, json={"perfil": {}}))
    dos = asyncio.create_task(c.post(RESULTADOS, headers=dpo, json={"perfil": {}}))
    await asyncio.sleep(ESPERA)
    assert not uno.done() and not dos.done()  # los dos esperan el candado
    await retenida.rollback()
    await retenida.close()
    respuestas = [await uno, await dos]
    assert sorted(r.status_code for r in respuestas) == [201, 409]
    perdedor = next(r for r in respuestas if r.status_code == 409)
    assert perdedor.json()["code"] == "DIAG_SELLOS_AGOTADOS"
    async with api["factory"]() as s:
        await fijar_contexto_rls(s, api["a"])
        filas = (await s.execute(text(
            "SELECT secuencia, huella, huella_anterior FROM diagnostico_resultados "
            "WHERE tenant_id = :t ORDER BY secuencia"), {"t": api["a"]})).all()
    assert [f.secuencia for f in filas] == [1, 2] and filas[1].huella_anterior == filas[0].huella


async def test_objecion_en_vuelo_bloquea_el_sello(api):
    """Una objeción en vuelo (sin confirmar) retiene el candado; el sello espera, la ve y da 409.

    Mutación: quitar el candado de `exigir_sin_objeciones_abiertas` → la comprobación no espera, no ve la
    objeción sin confirmar y el sello termina en 201.
    """
    c = api["client"]
    dpo, admin = _como(api, "dpo"), _como(api, "admin")
    assert (await c.put(RESPUESTAS, headers=admin, json={"respuestas": [_respuesta(12)]})).status_code == 200
    en_vuelo = api["factory"]()
    await objeciones_engine.crear_objecion(en_vuelo, api["a"], api["u"]["dpo"][0], 12, MOTIVO)
    sello = asyncio.create_task(c.post(RESULTADOS, headers=dpo, json={"perfil": {}}))
    await asyncio.sleep(ESPERA)
    assert not sello.done()
    await en_vuelo.commit()
    await en_vuelo.close()
    r = await sello
    assert r.status_code == 409 and r.json()["code"] == "OBJECIONES_ABIERTAS", r.text


async def test_sello_en_vuelo_retiene_la_objecion(api):
    """Inversa: con un sello en vuelo (candado retenido), objetar espera a que termine.

    Mutación: quitar el candado de `crear_objecion` → la objeción entra mientras el sello está en vuelo.
    """
    c = api["client"]
    retenida = await _retener_candado(api)
    objecion = asyncio.create_task(
        c.post(OBJECIONES, headers=_como(api, "dpo"), json={"pregunta_id": 12, "motivo": MOTIVO})
    )
    await asyncio.sleep(ESPERA)
    assert not objecion.done()
    await retenida.commit()
    await retenida.close()
    assert (await objecion).status_code == 201


# --- Sello inmutable -----------------------------------------------------------------------------

async def test_sello_inmutable_para_lopdp_app(api):
    """`lopdp_app` no puede modificar ni borrar un sello.

    Mutación: `GRANT UPDATE, DELETE ON diagnostico_resultados TO lopdp_app` → las sentencias pasan.
    """
    c = api["client"]
    admin, dpo = _como(api, "admin"), _como(api, "dpo")
    assert (await c.put(RESPUESTAS, headers=admin, json={"respuestas": [_respuesta(12)]})).status_code == 200
    assert (await c.post(RESULTADOS, headers=dpo, json={"perfil": {}})).status_code == 201
    for sentencia in (
        "UPDATE diagnostico_resultados SET sellado_por = 'otro' WHERE tenant_id = :t",
        "DELETE FROM diagnostico_resultados WHERE tenant_id = :t",
    ):
        async with api["factory"]() as s:
            await s.execute(text("SET LOCAL ROLE lopdp_app"))
            await fijar_contexto_rls(s, api["a"])
            with pytest.raises(Exception, match="permission denied"):
                await s.execute(text(sentencia), {"t": api["a"]})
