# ¤regulation-code
# ¤paquete-normativo
# ¤arbitro
"""Árbitro de REG-01: paquete normativo como dato, editable solo por el operador de la plataforma.

Corre contra un PostgreSQL 16 local (TEST_DATABASE_URL), nunca contra producción. Escenarios de
governance/especificaciones/REG-01.md §5 más las condiciones de Seguridad y del Arquitecto (2026-11-13):

- test_publicar_exige_verificados: publicar con un parámetro sin verificar → 409 PARAMETRO_NO_VERIFICADO.
- test_plazo_con_unidad: un plazo_* sin unidad → 422 UNIDAD_REQUERIDA (API y función de la base).
- test_version_inmutable: editar un publicado → 409 PAQUETE_NO_BORRADOR; una versión nueva copia los parámetros.
- test_solo_operador_escribe: un usuario de organización que escribe → 403 NO_ES_OPERADOR; puede leer.
- lopdp_app: INSERT/UPDATE/DELETE directos → permission denied, aun con app.current_operador_id fijado.
- Funciones: operador inexistente o inactivo → error; SECURITY DEFINER con search_path fijo en pg_catalog.
- Concurrencia: dos publicaciones simultáneas del mismo borrador → la segunda da PAQUETE_NO_BORRADOR.

Mutaciones documentadas (cada una pone esta suite en rojo; INV_LOPDP_REGULATION_AS_CODE_DIFF):
1. Quitar de reg01_publicar la comprobación de «NOT x.verificado» → test_publicar_exige_verificados
   y test_funcion_no_activa_valor_sin_verificar fallan.
2. Conceder UPDATE en parametros_normativos a lopdp_app → test_lopdp_app_no_escribe_directo falla.
3. Dejar que un usuario de organización edite: operador_paquetes sin require_operador y
   reg01_operador_activo sin comprobar la tabla → test_solo_operador_escribe falla. Quitar solo la
   capa de la API no basta para ponerla en rojo: la base rechaza igual (defensa en profundidad).
4. Quitar de reg01_fijar_parametro la comprobación de estado → test_version_inmutable falla.
"""
from __future__ import annotations

import asyncio
import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/plataforma/paquetes"
FUENTE = "https://www.finanzaspopulares.gob.ec/wp-content/uploads/2021/07/ley_organica_de_proteccion_de_datos_personales.pdf"


def _async_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine(_async_url(), echo=False)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def conn(engine):
    async with engine.connect() as connection:
        trans = await connection.begin()
        yield connection
        await trans.rollback()


async def _crear_operador(conn, activo: bool = True) -> tuple[str, str]:
    op_id = f"op-{uuid.uuid4().hex[:10]}"
    email = f"{op_id}@operador.test"
    await conn.execute(
        text(
            "INSERT INTO operadores_plataforma (id, email, nombre, activo) VALUES (:id, :e, 'Operadora Prueba', :a)"
        ),
        {"id": op_id, "e": email, "a": activo},
    )
    return op_id, email


async def _crear_paquete(conn, codigo: str | None = None) -> tuple[str, str]:
    """Paquete propio de la prueba en borrador con dos parámetros sin verificar (lo inserta el dueño)."""
    codigo = codigo or f"T{uuid.uuid4().hex[:8].upper()}"
    pid = f"pqn-{uuid.uuid4().hex[:12]}"
    await conn.execute(
        text(
            "INSERT INTO paquetes_normativos (id, codigo, nombre, version, estado, creado_por) "
            "VALUES (:id, :c, 'Paquete de prueba', '1.0', 'borrador', 'prueba')"
        ),
        {"id": pid, "c": codigo},
    )
    for clave, unidad in (("plazo_derechos_dias", "calendario"), ("autoridad", None)):
        await conn.execute(
            text(
                "INSERT INTO parametros_normativos (id, paquete_id, clave, valor, unidad, actualizado_por) "
                "VALUES (:id, :p, :k, '15', :u, 'prueba')"
            ),
            {"id": f"pmn-{uuid.uuid4().hex[:12]}", "p": pid, "k": clave, "u": unidad},
        )
    return pid, codigo


@pytest_asyncio.fixture
async def cliente(conn, monkeypatch):
    """Cliente HTTP cuya sesión corre como lopdp_app dentro de la transacción de la prueba."""
    from app_core.db.session import get_session
    from main import app

    monkeypatch.setenv("AUTH_MODE", "headers")

    async def _override():
        maker = async_sessionmaker(
            bind=conn, class_=AsyncSession, expire_on_commit=False, join_transaction_mode="create_savepoint"
        )
        async with maker() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    app.dependency_overrides[get_session] = _override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(get_session, None)


async def _como_app(conn) -> None:
    await conn.execute(text("SET LOCAL ROLE lopdp_app"))


def _op(email: str) -> dict:
    return {"X-User-Email": email, "X-User-ID": f"sub-{email}"}


def _verificado(valor: str = "15", unidad: str | None = "calendario") -> dict:
    return {"valor": valor, "unidad": unidad, "termino_legal": "plazo", "articulo": "LOPDP art. 13",
            "fuente_url": FUENTE, "verificado": True}


async def _verificar_todo(cliente, email, pid) -> None:
    for clave, unidad in (("plazo_derechos_dias", "calendario"), ("autoridad", None)):
        r = await cliente.put(f"{BASE}/{pid}/parametros/{clave}", json=_verificado(unidad=unidad), headers=_op(email))
        assert r.status_code == 200, r.text


async def test_publicar_exige_verificados(conn, cliente):
    _, email = await _crear_operador(conn)
    pid, _ = await _crear_paquete(conn)
    await _como_app(conn)

    r = await cliente.post(f"{BASE}/{pid}/publicar", headers=_op(email))
    assert r.status_code == 409 and r.json()["code"] == "PARAMETRO_NO_VERIFICADO", r.text

    await _verificar_todo(cliente, email, pid)
    r = await cliente.post(f"{BASE}/{pid}/publicar", headers=_op(email))
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["paquete"]["estado"] == "publicado"
    assert cuerpo["paquete"]["publicado_por"]
    # R3: lo no medido se dice; nunca un impacto nulo.
    assert cuerpo["impacto"]["plantillas_pendiente"] is True
    assert cuerpo["impacto"]["organizaciones_pendiente"] is True


async def test_verificar_deja_autor_y_fecha(conn, cliente):
    op_id, email = await _crear_operador(conn)
    pid, _ = await _crear_paquete(conn)
    await _como_app(conn)
    r = await cliente.put(f"{BASE}/{pid}/parametros/plazo_derechos_dias", json=_verificado(), headers=_op(email))
    assert r.status_code == 200, r.text
    p = r.json()
    assert p["verificado_por"] == op_id and p["verificado_por_nombre"] == "Operadora Prueba"
    assert p["verificado_en"] and p["actualizado_por"] == op_id


async def test_plazo_con_unidad(conn, cliente):
    op_id, email = await _crear_operador(conn)
    pid, _ = await _crear_paquete(conn)
    await _como_app(conn)
    r = await cliente.put(
        f"{BASE}/{pid}/parametros/plazo_derechos_dias", json=_verificado(unidad=None), headers=_op(email)
    )
    assert r.status_code == 422 and r.json()["code"] == "UNIDAD_REQUERIDA", r.text

    # La base lo guarda también, aunque se salte la API.
    with pytest.raises(DBAPIError, match="REG01:UNIDAD_REQUERIDA"):
        async with conn.begin_nested():
            await conn.execute(
                text("SELECT reg01_fijar_parametro(:o, :p, 'plazo_x_dias', '3', NULL, NULL, '', '', FALSE)"),
                {"o": op_id, "p": pid},
            )


async def test_version_inmutable(conn, cliente):
    _, email = await _crear_operador(conn)
    pid, codigo = await _crear_paquete(conn)
    await _como_app(conn)
    await _verificar_todo(cliente, email, pid)
    assert (await cliente.post(f"{BASE}/{pid}/publicar", headers=_op(email))).status_code == 200

    r = await cliente.put(f"{BASE}/{pid}/parametros/autoridad", json=_verificado(unidad=None), headers=_op(email))
    assert r.status_code == 409 and r.json()["code"] == "PAQUETE_NO_BORRADOR", r.text
    r = await cliente.post(f"{BASE}/{pid}/publicar", headers=_op(email))
    assert r.status_code == 409 and r.json()["code"] == "PAQUETE_NO_BORRADOR", r.text

    r = await cliente.post(f"{BASE}/{codigo}/versiones", json={"version": "2.0"}, headers=_op(email))
    assert r.status_code == 201, r.text
    nuevo = r.json()
    assert nuevo["estado"] == "borrador" and nuevo["version"] == "2.0"
    detalle = (await cliente.get(f"{BASE}/{nuevo['id']}", headers=_op(email))).json()
    assert {p["clave"] for p in detalle["parametros"]} == {"plazo_derechos_dias", "autoridad"}

    # Publicar la 2.0 retira la 1.0 (R2).
    assert (await cliente.post(f"{BASE}/{nuevo['id']}/publicar", headers=_op(email))).status_code == 200
    estados = {p["version"]: p["estado"] for p in (await cliente.get(BASE, headers=_op(email))).json()["paquetes"]
               if p["codigo"] == codigo}
    assert estados == {"1.0": "retirado", "2.0": "publicado"}
    r = await cliente.get(f"{BASE}/{codigo}/parametros", headers=_op(email))
    assert r.status_code == 200 and len(r.json()["parametros"]) == 2


async def test_solo_operador_escribe(conn, cliente):
    pid, codigo = await _crear_paquete(conn)
    await _como_app(conn)
    usuario = {"X-User-Email": "admin@organizacion.test", "X-User-ID": "usuario-organizacion"}

    for metodo, ruta, cuerpo in (
        ("PUT", f"{BASE}/{pid}/parametros/autoridad", _verificado(unidad=None)),
        ("POST", f"{BASE}/{pid}/publicar", None),
        ("POST", f"{BASE}/{codigo}/versiones", {"version": "9.9"}),
    ):
        r = await cliente.request(metodo, ruta, json=cuerpo, headers=usuario)
        assert r.status_code == 403 and r.json()["code"] == "NO_ES_OPERADOR", (metodo, ruta, r.text)

    r = await cliente.get(BASE, headers=usuario)
    assert r.status_code == 200 and any(p["id"] == pid for p in r.json()["paquetes"])
    r = await cliente.get(f"{BASE}/{pid}", headers=usuario)
    assert r.status_code == 200


async def test_lectura_exige_autenticacion(cliente):
    r = await cliente.get(BASE)
    assert r.status_code in (401, 422), r.text


async def test_lopdp_app_no_escribe_directo(conn):
    op_id, _ = await _crear_operador(conn)
    pid, _ = await _crear_paquete(conn)
    await _como_app(conn)
    # Ni con el GUC del operador fijado: la base no confía en él.
    await conn.execute(text("SELECT set_config('app.current_operador_id', :o, true)"), {"o": op_id})
    for sql in (
        "UPDATE parametros_normativos SET verificado = TRUE WHERE paquete_id = :p",
        "UPDATE paquetes_normativos SET estado = 'publicado' WHERE id = :p",
        "INSERT INTO paquetes_normativos (id, codigo, nombre, version, creado_por) VALUES ('x', 'X', 'x', '1', 'x')",
        "DELETE FROM parametros_normativos WHERE paquete_id = :p",
    ):
        with pytest.raises(DBAPIError, match="permission denied"):
            async with conn.begin_nested():
                await conn.execute(text(sql), {"p": pid})


async def test_funcion_rechaza_operador_inexistente_o_inactivo(conn):
    inactivo, _ = await _crear_operador(conn, activo=False)
    pid, _ = await _crear_paquete(conn)
    await _como_app(conn)
    for operador in ("op-que-no-existe", inactivo):
        with pytest.raises(DBAPIError, match="REG01:NO_ES_OPERADOR"):
            async with conn.begin_nested():
                await conn.execute(text("SELECT reg01_publicar(:o, :p)"), {"o": operador, "p": pid})


async def test_funcion_no_activa_valor_sin_verificar(conn):
    op_id, _ = await _crear_operador(conn)
    pid, _ = await _crear_paquete(conn)
    await _como_app(conn)
    with pytest.raises(DBAPIError, match="REG01:PARAMETRO_NO_VERIFICADO"):
        async with conn.begin_nested():
            await conn.execute(text("SELECT reg01_publicar(:o, :p)"), {"o": op_id, "p": pid})


async def test_funciones_security_definer_con_search_path(conn):
    filas = (
        await conn.execute(
            text(
                "SELECT p.proname, p.prosecdef, p.proconfig, has_function_privilege('public', p.oid, 'EXECUTE') "
                "AS publico, has_function_privilege('lopdp_app', p.oid, 'EXECUTE') AS app "
                "FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
                "WHERE n.nspname = 'public' AND p.proname LIKE 'reg01\\_%'"
            )
        )
    ).mappings().all()
    assert {f["proname"] for f in filas} == {
        "reg01_operador_activo", "reg01_crear_version", "reg01_fijar_parametro", "reg01_publicar"
    }
    for f in filas:
        assert f["prosecdef"], f["proname"]
        assert "search_path=pg_catalog, public" in (f["proconfig"] or []), f
        assert f["app"] and not f["publico"], f


async def test_lopdp_app_solo_select_en_tablas(conn):
    filas = (
        await conn.execute(
            text(
                "SELECT table_name, privilege_type FROM information_schema.role_table_grants "
                "WHERE grantee = 'lopdp_app' AND table_name IN ('paquetes_normativos', 'parametros_normativos', "
                "'requisitos_normativos', 'controles_comunes', 'requisito_control')"
            )
        )
    ).all()
    assert {p for _, p in filas} == {"SELECT"}
    assert len({t for t, _ in filas}) == 5


async def test_siembra_lopdp_sin_verificar(conn):
    filas = (
        await conn.execute(
            text(
                "SELECT x.clave, x.verificado, p.estado FROM parametros_normativos x "
                "JOIN paquetes_normativos p ON p.id = x.paquete_id WHERE p.id = 'pqn-lopdp-1-0'"
            )
        )
    ).all()
    assert {c for c, _, _ in filas} >= {
        "plazo_derechos_dias", "plazo_vulneracion_encargado_dias", "plazo_vulneracion_autoridad_dias",
        "plazo_vulneracion_titulares_dias", "autoridad", "canal_notificacion",
    }
    assert all(not v and e == "borrador" for _, v, e in filas)


async def test_publicaciones_simultaneas_la_segunda_da_409(engine):
    """Dos transacciones reales publican el mismo borrador: el candado ordena y la segunda falla."""
    async with engine.begin() as c:
        op_id, _ = await _crear_operador(c)
        pid, codigo = await _crear_paquete(c)
        await c.execute(text("UPDATE parametros_normativos SET verificado = TRUE, verificado_por = :o, "
                             "verificado_en = NOW() WHERE paquete_id = :p"), {"o": op_id, "p": pid})
    try:
        a = await engine.connect()
        b = await engine.connect()
        ta = await a.begin()
        tb = await b.begin()
        await a.execute(text("SET LOCAL ROLE lopdp_app"))
        await b.execute(text("SET LOCAL ROLE lopdp_app"))
        await a.execute(text("SELECT reg01_publicar(:o, :p)"), {"o": op_id, "p": pid})

        segunda = asyncio.create_task(b.execute(text("SELECT reg01_publicar(:o, :p)"), {"o": op_id, "p": pid}))
        await asyncio.sleep(0.5)
        assert not segunda.done(), "la segunda publicación debió esperar el candado"
        await ta.commit()
        with pytest.raises(DBAPIError, match="REG01:PAQUETE_NO_BORRADOR"):
            await segunda
        await tb.rollback()
        await a.close()
        await b.close()

        async with engine.connect() as c:
            publicados = (await c.execute(
                text("SELECT count(*) FROM paquetes_normativos WHERE codigo = :c AND estado = 'publicado'"),
                {"c": codigo},
            )).scalar()
        assert publicados == 1
    finally:
        async with engine.begin() as c:
            await c.execute(text("DELETE FROM parametros_normativos WHERE paquete_id = :p"), {"p": pid})
            await c.execute(text("DELETE FROM paquetes_normativos WHERE codigo = :c"), {"c": codigo})
            await c.execute(text("DELETE FROM operadores_plataforma WHERE id = :o"), {"o": op_id})
