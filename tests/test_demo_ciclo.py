# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤demo ¤seguridad-tenant
"""DEMO-02: ciclo de sesión demo (entrar, tope, reemplazo, terminar, vencimiento y orquestador de la copia).

Corren contra PostgreSQL real (`db_engine`: el PG16 del arnés o evydentia-pruebas, nunca producción). Solo
valores simulados y correos `.invalid`.

Mutaciones documentadas (cada una hace fallar la prueba indicada):
  - no comprobar la lista `DEMO_VENDEDORES` en `entrar`: test_correo_fuera_de_la_lista_da_403_y_no_crea_nada;
  - quitar el tope (`>= TOPE`) o contar antes de vencer a la previa: test_la_entrada_21_da_409 y
    test_con_20_activas_la_segunda_entrada_del_mismo_vendedor_reemplaza;
  - no vencer a la demo previa del vendedor: test_segunda_entrada_del_vendedor_vence_la_primera_por_reemplazo
    (el índice único parcial lo convertiría en un 503);
  - quitar el SAVEPOINT de `entrar`: test_falla_en_una_sala_da_503_sin_filas_a_medias;
  - no omitir la sala sin clon (lanzar en vez de omitir): test_una_sala_sin_clon_se_omite_y_el_evento_la_nombra;
  - que `terminar` borre filas: test_terminar_marca_vencida_y_no_borra_nada;
  - vencer a los 61 minutos en vez de a los 60: test_vencer_inactivas_59_no_60_si.
"""
from __future__ import annotations

import asyncio
import hashlib
import importlib
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import String, cast, column, create_engine, delete, table, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app_core.security import IdentidadVerificada
from features.demo.domain import vendedores
from features.demo.domain.contrato import CAMPOS_ESTADO, CAMPOS_ORGANIZACION, CAMPOS_PERSONA
from features.demo.domain.errores import DEMO_NO_AUTORIZADO, DEMO_NO_DISPONIBLE, DEMO_OCUPADA, ErrorDemo
from features.demo.domain.plantilla import ORDEN_DE_SALAS, PLANTILLA_TENANT_ID
from features.demo.domain.sesion import TOPE
from features.demo.services import cierre_engine, entrada_engine
from scripts.demo import sembrar_plantilla as siembra

AHORA = datetime(2026, 11, 12, 10, 0, tzinfo=timezone.utc)


# --- Montaje DEMO-12: el catálogo que nombra la plantilla ------------------------------------------
# La siembra de biblioteca falla cerrado sin la versión publicada de cada código (DEMO-12 R3). El montaje
# publica las que falten, con los disparadores de `biblioteca_versiones` desactivados solo durante la
# inserción (el flujo editorial no es el objeto de esta prueba, como en test_demo05d), y al terminar retira
# solo lo que creó.
_CODIGOS_DEMO = [d["plantilla"] for d in siembra.cargar_plantilla()["salas"]["biblioteca"]["documentos"]]


async def _publicar_catalogo_demo(db_engine) -> dict:
    montaje: dict = {"versiones": [], "catalogo": [], "usuario": f"u-montaje-{uuid.uuid4().hex[:10]}"}
    raiz = Path(__file__).resolve().parents[1] / "data" / "biblioteca" / "pmv"
    async with AsyncSession(db_engine, expire_on_commit=False) as s:
        await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:i, :e, 'Montaje ficticio')"),
                        {"i": montaje["usuario"], "e": f"{montaje['usuario']}@prueba.invalid"})
        for codigo in _CODIGOS_DEMO:
            if (await s.execute(text("SELECT 1 FROM biblioteca_versiones WHERE codigo=:c AND estado='publicada' "
                                     "AND formato='MD'"), {"c": codigo})).first():
                continue
            if (await s.execute(text("INSERT INTO biblioteca_catalogo (codigo, nombre, formato) VALUES (:c, :c, 'MD') "
                                     "ON CONFLICT (codigo) DO NOTHING RETURNING codigo"), {"c": codigo})).first():
                montaje["catalogo"].append(codigo)
            cuerpo = (raiz / f"{codigo}.md").read_text(encoding="utf-8")
            version = str(uuid.uuid4())
            await s.execute(text("ALTER TABLE biblioteca_versiones DISABLE TRIGGER USER"))
            await s.execute(text(
                "INSERT INTO biblioteca_versiones (id, codigo, version, formato, responsable_id, autores, estado, "
                "cuerpo_md, sha256) VALUES (:i, :c, '0.0.1', 'MD', :a, CAST(:au AS jsonb), 'publicada', :cu, :h)"),
                {"i": version, "c": codigo, "a": montaje["usuario"], "au": f'["{montaje["usuario"]}"]', "cu": cuerpo,
                 "h": hashlib.sha256(cuerpo.encode("utf-8")).hexdigest()})
            await s.execute(text("ALTER TABLE biblioteca_versiones ENABLE TRIGGER USER"))
            montaje["versiones"].append(version)
        await s.commit()
    return montaje


async def _retirar_catalogo_demo(db_engine, montaje: dict) -> None:
    async with AsyncSession(db_engine, expire_on_commit=False) as s:
        if not montaje["versiones"]:  # el catálogo ya estaba publicado: no se retira nada sembrado
            await s.execute(text("DELETE FROM users WHERE id=:u"), {"u": montaje["usuario"]})
            await s.commit()
            return
        await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": PLANTILLA_TENANT_ID})
        sembrados = "SELECT id FROM biblioteca_documentos WHERE tenant_id=:t AND codigo = ANY(:c)"
        await s.execute(text("ALTER TABLE biblioteca_documentos_historial DISABLE TRIGGER USER"))
        await s.execute(text(f"DELETE FROM biblioteca_documentos_historial WHERE documento_id IN ({sembrados})"),
                        {"t": PLANTILLA_TENANT_ID, "c": _CODIGOS_DEMO})
        await s.execute(text("ALTER TABLE biblioteca_documentos_historial ENABLE TRIGGER USER"))
        await s.execute(text(f"DELETE FROM biblioteca_documentos WHERE id IN ({sembrados})"),
                        {"t": PLANTILLA_TENANT_ID, "c": _CODIGOS_DEMO})
        await s.execute(text("ALTER TABLE biblioteca_versiones DISABLE TRIGGER USER"))
        await s.execute(text("DELETE FROM biblioteca_versiones WHERE id = ANY(:v)"), {"v": montaje["versiones"]})
        await s.execute(text("ALTER TABLE biblioteca_versiones ENABLE TRIGGER USER"))
        await s.execute(text("DELETE FROM biblioteca_catalogo WHERE codigo = ANY(:c)"), {"c": montaje["catalogo"]})
        await s.execute(text("DELETE FROM users WHERE id=:u"), {"u": montaje["usuario"]})
        await s.commit()


def _fabrica(db_engine):
    return async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)


_SQL_TABLAS_CON_TENANT = (
    "SELECT c.table_name FROM information_schema.columns c JOIN information_schema.tables t "
    "ON t.table_schema = c.table_schema AND t.table_name = c.table_name WHERE c.table_schema = 'public' "
    "AND c.column_name = 'tenant_id' AND t.table_type = 'BASE TABLE' AND c.table_name <> 'demo_sesiones'"
)


def _borrar_organizacion(con, tenant_id):
    """Limpieza de la prueba (no es la purga: la hace el job DEMO-05). Sin disparar triggers ni claves foráneas."""
    con.execute(text("SET LOCAL session_replication_role = replica"))
    personas = [f[0] for f in con.execute(
        text("SELECT user_id FROM user_tenant_roles WHERE tenant_id = :t"), {"t": tenant_id})]
    for (tabla,) in con.execute(text(_SQL_TABLAS_CON_TENANT)).all():
        con.execute(delete(table(tabla)).where(cast(column("tenant_id"), String) == tenant_id))
    con.execute(text("UPDATE demo_sesiones SET tenant_id = NULL, persona_usuario_id = NULL WHERE tenant_id = :t"),
                {"t": tenant_id})
    con.execute(delete(table("tenants")).where(column("id") == tenant_id))
    for uid in personas:
        con.execute(delete(table("users")).where(column("id") == uid))


class Corrida:
    """Subs y correos de una prueba; al terminar purga las organizaciones que dejó."""

    def __init__(self, db_engine):
        self.s = uuid.uuid4().hex[:8]
        self.db_engine = db_engine
        self.fabrica = _fabrica(db_engine)

    def sub(self, n=1):
        return f"sub-ciclo-{self.s}-{n}"

    def correo(self, n=1):
        return f"vendedor{n}-{self.s}@vendedores.invalid"

    async def entrar(self, n=1, ahora=AHORA):
        """Una petición completa: sesión propia y commit al final, como `get_session`."""
        async with self.fabrica() as session:
            try:
                estado = await entrada_engine.entrar(session, self.sub(n), self.correo(n), ahora)
                await session.commit()
                return estado
            except Exception:
                await session.rollback()
                raise

    async def uno(self, sql, **p):
        async with self.fabrica() as session:
            return (await session.execute(text(sql), p)).all()

    async def sesiones(self):
        return await self.uno(
            "SELECT vendedor_sub, tenant_id, estado, motivo_fin FROM demo_sesiones WHERE vendedor_sub LIKE :p "
            "ORDER BY iniciada_en, vendedor_sub", p=f"sub-ciclo-{self.s}-%")

    async def contar(self, sql):
        return (await self.uno(sql))[0][0]

    async def limpiar(self):
        filas = await self.uno("SELECT tenant_id FROM demo_sesiones WHERE vendedor_sub LIKE :p AND tenant_id IS NOT NULL",
                               p=f"sub-ciclo-{self.s}-%")
        url = str(self.db_engine.url.set(drivername="postgresql+psycopg").render_as_string(hide_password=False))
        motor = create_engine(url)
        try:
            with motor.begin() as con:
                for (tenant,) in filas:
                    _borrar_organizacion(con, tenant)
                con.execute(text("DELETE FROM demo_sesiones WHERE vendedor_sub LIKE :p"), {"p": f"sub-ciclo-{self.s}-%"})
                con.execute(text("DELETE FROM demo_sesiones WHERE id LIKE :p"), {"p": f"zz-relleno-{self.s}-%"})
        finally:
            motor.dispose()


@pytest_asyncio.fixture
async def corrida(db_engine, monkeypatch):
    c = Corrida(db_engine)
    monkeypatch.setenv("DEMO_VENDEDORES", ", ".join(c.correo(n) for n in range(1, 4)))
    montaje = await _publicar_catalogo_demo(db_engine)
    async with c.fabrica() as session:
        await siembra.sembrar(session)
        await session.commit()
    yield c
    await c.limpiar()
    await _retirar_catalogo_demo(db_engine, montaje)


# --- Lista de vendedores -----------------------------------------------------------------------------


def test_la_lista_se_normaliza():
    lista = vendedores.normalizar(" Ana@Ventas.INVALID;\nbeto@ventas.invalid , ,CARLA@ventas.invalid ")
    assert lista == {"ana@ventas.invalid", "beto@ventas.invalid", "carla@ventas.invalid"}
    assert vendedores.normalizar(None) == frozenset() == vendedores.normalizar("  ")


def test_sin_secreto_nadie_entra(monkeypatch):
    monkeypatch.delenv("DEMO_VENDEDORES", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    assert not vendedores.es_autorizado("ana@ventas.invalid")
    monkeypatch.setenv("DEMO_VENDEDORES", "ana@ventas.invalid")
    assert vendedores.es_autorizado("  ANA@ventas.invalid ") and not vendedores.es_autorizado("")


# --- Entrada ------------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_la_entrada_crea_la_demo_con_el_administrador_y_el_evento(corrida):
    estado = await corrida.entrar()

    assert estado.tenant_id.startswith("demo-") and estado.tenant_id != PLANTILLA_TENANT_ID
    assert estado.persona_activa.rol == "admin_organizacion"
    assert estado.vence_en == AHORA + timedelta(minutes=60)
    assert {p.rol for p in estado.personas} >= {"admin_organizacion", "dpo", "coordinador", "implementador",
                                                "responsable_area"}
    sesion = (await corrida.sesiones())[0]
    assert sesion[1:] == (estado.tenant_id, "activa", None)
    persona = (await corrida.uno("SELECT persona_usuario_id FROM demo_sesiones WHERE vendedor_sub = :s",
                                 s=corrida.sub()))[0][0]
    assert persona == estado.persona_activa.usuario_id
    (evento,) = await corrida.uno(
        "SELECT action, user_id, payload ->> 'vendedor_email' FROM audit_events WHERE tenant_id = :t "
        "AND action = 'DEMO_INICIADA'", t=estado.tenant_id)
    assert evento == ("DEMO_INICIADA", persona, corrida.correo())
    # La organización demo es ficticia: todas las personas .invalid y es_demo.
    assert (await corrida.uno("SELECT es_demo FROM tenants WHERE id = :t", t=estado.tenant_id))[0][0] is True
    assert all(c.endswith(".invalid") for (c,) in await corrida.uno(
        "SELECT u.email FROM users u JOIN user_tenant_roles r ON r.user_id = u.id WHERE r.tenant_id = :t",
        t=estado.tenant_id))


@pytest.mark.asyncio
async def test_correo_fuera_de_la_lista_da_403_y_no_crea_nada(corrida):
    antes = (await corrida.contar("SELECT count(*) FROM tenants"), await corrida.contar("SELECT count(*) FROM demo_sesiones"))
    async with corrida.fabrica() as session:
        with pytest.raises(ErrorDemo) as e:
            await entrada_engine.entrar(session, corrida.sub(9), f"intruso-{corrida.s}@vendedores.invalid", AHORA)
        await session.commit()
    assert e.value.codigo == DEMO_NO_AUTORIZADO and e.value.status_code == 403
    assert e.value.cuerpo() == {"codigo": "DEMO_NO_AUTORIZADO", "mensaje": "No autorizado para la demo"}
    assert antes == (await corrida.contar("SELECT count(*) FROM tenants"),
                     await corrida.contar("SELECT count(*) FROM demo_sesiones"))


async def _llenar_hasta(corrida, cuantas):
    """Inserta sesiones activas de relleno (sin tenant) hasta que haya `cuantas` en todo el entorno."""
    existentes = await corrida.contar("SELECT count(*) FROM demo_sesiones WHERE estado = 'activa'")
    async with corrida.fabrica() as session:
        for i in range(cuantas - existentes):
            await session.execute(
                text("INSERT INTO demo_sesiones (id, vendedor_sub, vendedor_email) VALUES (:i, :s, :e)"),
                {"i": f"zz-relleno-{corrida.s}-{i}", "s": f"sub-ciclo-{corrida.s}-r{i}", "e": f"relleno{i}@ventas.invalid"})
        await session.commit()


@pytest.mark.asyncio
async def test_la_entrada_21_da_409(corrida):
    await _llenar_hasta(corrida, TOPE)
    antes = await corrida.contar("SELECT count(*) FROM tenants")
    with pytest.raises(ErrorDemo) as e:
        await corrida.entrar(2)
    assert e.value.codigo == DEMO_OCUPADA and e.value.status_code == 409
    assert e.value.cuerpo()["mensaje"] == "Demo ocupada, intenta en unos minutos"
    assert await corrida.contar("SELECT count(*) FROM demo_sesiones WHERE estado = 'activa'") == TOPE
    assert await corrida.contar("SELECT count(*) FROM tenants") == antes


@pytest.mark.asyncio
async def test_segunda_entrada_del_vendedor_vence_la_primera_por_reemplazo(corrida):
    primera = await corrida.entrar()
    segunda = await corrida.entrar(ahora=AHORA + timedelta(minutes=5))

    assert primera.tenant_id != segunda.tenant_id
    primera_fila, segunda_fila = await corrida.sesiones()
    assert primera_fila[1:] == (primera.tenant_id, "vencida", "reemplazada")
    assert segunda_fila[1:] == (segunda.tenant_id, "activa", None)
    assert await corrida.contar(
        f"SELECT count(*) FROM tenants WHERE id = '{primera.tenant_id}'") == 1, "la aplicación no borra"
    assert await corrida.contar(
        f"SELECT count(*) FROM audit_events WHERE tenant_id = '{primera.tenant_id}' AND action = 'DEMO_VENCIDA'") == 1


@pytest.mark.asyncio
async def test_con_20_activas_la_segunda_entrada_del_mismo_vendedor_reemplaza(corrida):
    await corrida.entrar()
    await _llenar_hasta(corrida, TOPE)  # la demo del vendedor ocupa uno de los 20
    segunda = await corrida.entrar(ahora=AHORA + timedelta(minutes=1))  # reemplaza: no ocupa cupo
    assert segunda.tenant_id
    assert await corrida.contar("SELECT count(*) FROM demo_sesiones WHERE estado = 'activa'") == TOPE


@pytest.mark.asyncio
async def test_falla_en_una_sala_da_503_sin_filas_a_medias(corrida, monkeypatch):
    previa = await corrida.entrar()
    from app_core.pasillo import diagnostico

    async def falla(session, origen, destino, mapa_ids):
        await session.execute(text("SELECT 1"))
        raise RuntimeError("falla simulada del clon")

    monkeypatch.setattr(diagnostico, "clonar_desde_plantilla", falla)
    cuentas = ("SELECT count(*) FROM tenants", "SELECT count(*) FROM users", "SELECT count(*) FROM user_tenant_roles",
               "SELECT count(*) FROM audit_events", "SELECT count(*) FROM demo_sesiones")
    antes = [await corrida.contar(c) for c in cuentas]
    async with corrida.fabrica() as session:  # como el router: devuelve el error y `get_session` confirma
        with pytest.raises(ErrorDemo) as e:
            await entrada_engine.entrar(session, corrida.sub(), corrida.correo(), AHORA + timedelta(minutes=2))
        await session.commit()
    assert e.value.codigo == DEMO_NO_DISPONIBLE and e.value.status_code == 503
    assert e.value.cuerpo()["mensaje"] == "No pudimos preparar la demo; intenta de nuevo"
    assert [await corrida.contar(c) for c in cuentas] == antes
    # La demo anterior sigue activa: el reemplazo se deshizo con la copia.
    assert (await corrida.sesiones())[0][1:] == (previa.tenant_id, "activa", None)


@pytest.mark.asyncio
async def test_una_sala_sin_clon_se_omite_y_el_evento_la_nombra(corrida, monkeypatch):
    monkeypatch.setattr("features.demo.services.entrada_engine.ORDEN_DE_SALAS", (*ORDEN_DE_SALAS, "sala_futura_sin_clon"))
    estado = await corrida.entrar()
    omitidas = [s for s in (*ORDEN_DE_SALAS, "sala_futura_sin_clon") if entrada_engine._clonador(s) is None]
    assert omitidas
    ((payload,),) = await corrida.uno(
        "SELECT payload::text FROM audit_events WHERE tenant_id = :t AND action = 'DEMO_INICIADA'", t=estado.tenant_id)
    assert all(sala in payload for sala in omitidas)
    assert (await corrida.sesiones())[0][2] == "activa"


@pytest.mark.asyncio
async def test_el_orquestador_llama_a_cada_sala_registrada_en_orden(corrida, monkeypatch):
    llamadas = []
    reales = {}
    for sala in ORDEN_DE_SALAS:
        clon = entrada_engine._clonador(sala)
        if clon is None:
            continue
        reales[sala] = clon

        def espia(sala=sala, clon=clon):
            async def _f(session, origen, destino, mapa_ids):
                llamadas.append((sala, origen, bool(mapa_ids)))
                return await clon(session, origen, destino, mapa_ids)
            return _f

        modulo = importlib.import_module(f"app_core.pasillo.{sala}")
        monkeypatch.setattr(modulo, "clonar_desde_plantilla", espia())
    await corrida.entrar()
    assert [s for s, *_ in llamadas] == [s for s in ORDEN_DE_SALAS if s in reales]
    assert all(origen == PLANTILLA_TENANT_ID for _s, origen, _m in llamadas)
    assert llamadas[0][2] is False and all(m for _s, _o, m in llamadas[1:]), "el mapa de organización llega a las demás"


# --- Terminar y vencer --------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_terminar_marca_vencida_y_no_borra_nada(corrida):
    estado = await corrida.entrar()
    cuentas = (f"SELECT count(*) FROM tenants WHERE id = '{estado.tenant_id}'",
               f"SELECT count(*) FROM user_tenant_roles WHERE tenant_id = '{estado.tenant_id}'",
               f"SELECT count(*) FROM areas WHERE tenant_id = '{estado.tenant_id}'",
               f"SELECT count(*) FROM audit_events WHERE tenant_id = '{estado.tenant_id}'")
    antes = [await corrida.contar(c) for c in cuentas]
    for _ in range(2):  # idempotente
        async with corrida.fabrica() as session:
            await cierre_engine.terminar(session, corrida.sub(), AHORA + timedelta(minutes=10))
            await session.commit()
    assert (await corrida.sesiones())[0][1:] == (estado.tenant_id, "vencida", "terminar")
    despues = [await corrida.contar(c) for c in cuentas]
    assert despues[:3] == antes[:3] and despues[3] == antes[3] + 1
    assert await corrida.contar(
        f"SELECT count(*) FROM audit_events WHERE tenant_id = '{estado.tenant_id}' AND action = 'DEMO_TERMINADA'") == 1


@pytest.mark.asyncio
async def test_vencer_inactivas_59_no_60_si(corrida):
    estado = await corrida.entrar()

    async def vencer(minutos):
        async with corrida.fabrica() as session:
            await cierre_engine.vencer_inactivas(session, AHORA + timedelta(minutes=minutos))
            await session.commit()
        return (await corrida.sesiones())[0][2:]

    assert await vencer(59) == ("activa", None)
    assert await vencer(60) == ("vencida", "inactividad")
    assert await corrida.contar(
        f"SELECT count(*) FROM audit_events WHERE tenant_id = '{estado.tenant_id}' AND action = 'DEMO_VENCIDA'") == 1


@pytest.mark.asyncio
async def test_una_demo_vencida_no_ocupa_cupo(corrida):
    await corrida.entrar()
    async with corrida.fabrica() as session:
        await cierre_engine.terminar(session, corrida.sub(), AHORA)
        await session.commit()
    await _llenar_hasta(corrida, TOPE - 1)
    await corrida.entrar(2, AHORA + timedelta(minutes=1))


# --- Ruta HTTP -----------------------------------------------------------------------------------------


@pytest_asyncio.fixture
async def cliente(corrida, monkeypatch):
    from api.routers import demo_sesion
    from app_core.db.session import get_session

    app = FastAPI()
    app.include_router(demo_sesion.router, prefix="/api/v1")

    async def sesion():
        async with corrida.fabrica() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    quien = {"n": 1}
    app.dependency_overrides[get_session] = sesion
    app.dependency_overrides[demo_sesion.identidad_del_vendedor] = lambda: IdentidadVerificada(
        corrida.sub(quien["n"]), corrida.correo(quien["n"]))
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://demo") as c:
        c.quien = quien
        yield c


@pytest.mark.asyncio
async def test_post_entrar_devuelve_201_con_la_forma_congelada_y_sin_datos_del_vendedor(cliente, corrida):
    r = await cliente.post("/api/v1/demo/entrar")
    assert r.status_code == 201
    cuerpo = r.json()
    assert tuple(cuerpo) == CAMPOS_ESTADO and cuerpo["demo"] is True
    assert tuple(cuerpo["organizacion"]) == CAMPOS_ORGANIZACION
    assert tuple(cuerpo["persona_activa"]) == CAMPOS_PERSONA and cuerpo["persona_activa"]["rol"] == "admin_organizacion"
    assert len(cuerpo["personas"]) >= 5
    assert corrida.correo() not in r.text and corrida.sub() not in r.text


@pytest.mark.asyncio
async def test_los_errores_llevan_el_cuerpo_congelado(cliente, corrida, monkeypatch):
    cliente.quien["n"] = 7  # correo fuera de la lista
    r = await cliente.post("/api/v1/demo/entrar")
    assert (r.status_code, r.json()) == (403, {"codigo": "DEMO_NO_AUTORIZADO", "mensaje": "No autorizado para la demo"})
    cliente.quien["n"] = 2
    await _llenar_hasta(corrida, TOPE)
    r = await cliente.post("/api/v1/demo/entrar")
    assert (r.status_code, r.json()["codigo"]) == (409, "DEMO_OCUPADA")


@pytest.mark.asyncio
async def test_post_terminar_da_204_y_deja_la_sesion_vencida(cliente, corrida):
    await cliente.post("/api/v1/demo/entrar")
    r = await cliente.post("/api/v1/demo/terminar")
    assert r.status_code == 204 and r.content == b""
    assert (await corrida.sesiones())[0][2:] == ("vencida", "terminar")


@pytest.mark.asyncio
async def test_get_estado_va_por_la_compuerta(cliente, monkeypatch):
    from features.demo import demo_service

    visto = {}

    async def estado(session, sub):
        visto["sub"] = sub
        raise NotImplementedError("Pendiente de DEMO-01")

    monkeypatch.setattr(demo_service, "estado", estado)
    r = await cliente.get("/api/v1/demo/estado")
    assert r.status_code == 503 and r.json()["codigo"] == "DEMO_NO_DISPONIBLE" and visto["sub"]


def test_el_router_solo_se_registra_con_app_env_demo(monkeypatch):
    from api.routers import demo_sesion

    try:
        monkeypatch.setenv("APP_ENV", "development")
        assert importlib.reload(demo_sesion).AUTO_REGISTRO is False
        monkeypatch.setenv("APP_ENV", "demo")
        assert importlib.reload(demo_sesion).AUTO_REGISTRO is True
    finally:
        monkeypatch.undo()
        importlib.reload(demo_sesion)


def test_ningun_motor_importa_otra_sala_ni_borra():
    import ast
    from pathlib import Path

    raiz = Path(__file__).resolve().parents[1] / "features" / "demo"
    for ruta in [*(raiz / "services").glob("*.py"), raiz / "domain" / "vendedores.py"]:
        fuente = ruta.read_text(encoding="utf-8")
        assert "DELETE" not in fuente.upper().split('"""')[-1] or "DELETE" not in fuente, ruta
        for nodo in ast.walk(ast.parse(fuente)):
            if isinstance(nodo, ast.ImportFrom) and (nodo.module or "").startswith("features."):
                assert (nodo.module or "").startswith("features.demo"), (ruta.name, nodo.module)
