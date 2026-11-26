# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤arbitro ¤seguridad
"""OPE-01: cada operador de la plataforma tiene su usuario.

Dos capas. Las reglas corren contra una base simulada en memoria (operadores, usuarios y roles) que
responde a las sentencias del motor. Las pruebas `test_db_*` abren el PostgreSQL 16 de pruebas
(`TEST_DATABASE_URL` y `exigir_base_de_pruebas()`) y se omiten sin él. Cada mutación m1 a m4 de la
especificación §5 tiene su prueba: la mutación aplicada hace fallar la guardia que la vigila.
"""
import argparse
import os
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from features.plataforma.services import operador_engine as motor


class _Resultado:
    def __init__(self, filas=None, valor=None):
        self._filas, self._valor = filas or [], valor

    def mappings(self):
        return self

    def first(self):
        return self._filas[0] if self._filas else None

    def all(self):
        return self._filas

    def scalar(self):
        return self._valor


class BaseSimulada:
    """Tablas mínimas: operadores_plataforma, users y user_tenant_roles (que nadie debe llenar)."""

    def __init__(self):
        self.operadores: list[dict] = []
        self.usuarios: dict[str, dict] = {}
        self.roles: list[dict] = []

    def operador(self, email, activo=True, google_sub=None, usuario_id=None, nombre="Operador"):
        fila = {"id": str(uuid4()), "email": email, "nombre": nombre, "activo": activo,
                "google_sub": google_sub, "usuario_id": usuario_id}
        self.operadores.append(fila)
        return fila

    async def execute(self, sentencia, p=None):
        p = p or {}
        if sentencia is motor._OPERADOR_POR_ID:
            return _Resultado([dict(o) for o in self.operadores if o["id"] == p["id"]])
        if sentencia is motor._GUARDAR_USUARIO:
            for o in self.operadores:
                if o["id"] == p["id"] and o["usuario_id"] is None:
                    o["usuario_id"] = p["u"]
            return _Resultado()
        if sentencia is motor._SIN_USUARIO:
            return _Resultado([dict(o) for o in self.operadores if o["activo"] and o["usuario_id"] is None])
        if sentencia is motor._ACTIVO:
            fila = next((o for o in self.operadores if o["usuario_id"] == p["u"]), None)
            return _Resultado(valor=fila["activo"] if fila else None)
        if sentencia is motor._OPERADOR_DE_IDENTIDAD:
            return _Resultado([dict(o) for o in self.operadores if o["activo"] and (
                o["email"].lower() == p["email"] or (o["google_sub"] and o["google_sub"] == p["sub"]))])
        if sentencia is motor._VINCULAR_SUB:
            for o in self.operadores:
                if o["id"] == p["id"] and o["google_sub"] is None:
                    o["google_sub"] = p["sub"]
            return _Resultado()
        if sentencia is motor._ACTIVOS:
            return _Resultado([{"usuario_id": o["usuario_id"], "nombre": o["nombre"], "email": o["email"],
                                "ha_entrado": bool(self.usuarios.get(o["usuario_id"], {}).get("google_sub"))}
                               for o in self.operadores if o["activo"]])
        sql = str(sentencia)
        if sql.startswith("UPDATE operadores_plataforma SET activo = FALSE"):
            filas = [o for o in self.operadores if o["email"] == p["e"]]
            for o in filas:
                o["activo"] = False
            return _Resultado([(o["id"],) for o in filas])
        if sql.startswith("UPDATE operadores_plataforma SET activo = TRUE"):
            filas = [o for o in self.operadores if o["email"] == p["e"]]
            for o in filas:
                o["activo"], o["nombre"] = True, p["n"]
            return _Resultado([(o["id"],) for o in filas])
        if sql.startswith("INSERT INTO operadores_plataforma"):
            self.operadores.append({"id": p["id"], "email": p["e"], "nombre": p["n"], "activo": True,
                                    "google_sub": None, "usuario_id": None})
            return _Resultado()
        raise AssertionError(f"Sentencia no prevista: {sql[:80]}")


@pytest.fixture
def base(monkeypatch):
    base = BaseSimulada()

    async def crear_o_recuperar_usuario(session, email, nombre):
        existente = next((u for u in base.usuarios.values() if u["email"] == email.lower()), None)
        if existente:
            return {"id": existente["id"], "email": email, "creado": False}
        nuevo = {"id": str(uuid4()), "email": email.lower(), "nombre": nombre, "google_sub": None}
        base.usuarios[nuevo["id"]] = nuevo
        return {"id": nuevo["id"], "email": email, "creado": True}

    monkeypatch.setattr(motor.organizacion, "crear_o_recuperar_usuario", crear_o_recuperar_usuario)
    return base


async def _orden(base, *argv):
    from features.plataforma import administrar_operadores as cli
    await cli.ejecutar(base, cli._argumentos(list(argv)))


# --- Guardias ---

def guardia_alta(base, correo) -> list[str]:
    operador = next((o for o in base.operadores if o["email"] == correo), None)
    if operador is None or not operador["activo"]:
        return ["no hay operador activo"]
    if not operador["usuario_id"]:
        return ["el operador no guarda usuario_id"]
    usuario = base.usuarios.get(operador["usuario_id"])
    fallos = []
    if usuario is None or usuario["email"] != correo:
        fallos.append("el usuario no tiene el correo del operador")
    if any(r["user_id"] == operador["usuario_id"] for r in base.roles):
        fallos.append("el usuario tiene membresía en un tenant")
    return fallos


async def guardia_vincular(base, vincular) -> list[str]:
    base.operador("a@evydentia.test")
    base.operador("b@evydentia.test")
    await vincular(base)
    usuarios = len(base.usuarios)
    await vincular(base)
    fallos = []
    if any(o["usuario_id"] is None for o in base.operadores if o["activo"]):
        fallos.append("queda un operador activo sin usuario")
    if usuarios != 2 or len(base.usuarios) != 2:
        fallos.append("repetir vincular crea filas")
    return fallos


async def guardia_baja(base, activo) -> list[str]:
    usuario = await motor.enlazar_usuario(base, base.operador("c@evydentia.test")["id"])
    if not await activo(base, usuario):
        return ["el operador activo no se ve activo"]
    await _orden(base, "baja", "c@evydentia.test")
    return ["tras la baja sigue activo"] if await activo(base, usuario) else []


async def guardia_identidad(base, resolver) -> list[str]:
    usuario = await motor.enlazar_usuario(base, base.operador("d@evydentia.test", google_sub="sub-d")["id"])
    fallos = []
    if await resolver(base, "d@evydentia.test", "sub-otro") is not None:
        fallos.append("un sub distinto del vinculado identifica")
    if await resolver(base, "d@evydentia.test", "sub-d") != usuario:
        fallos.append("el operador no se identifica con su usuario_id")
    return fallos


# --- R1: alta y vincular ---

@pytest.mark.asyncio
async def test_r1_alta_crea_el_usuario_sin_membresia_y_guarda_usuario_id(base):
    await _orden(base, "alta", "Nueva@Evydentia.test", "Operadora nueva")
    assert guardia_alta(base, "nueva@evydentia.test") == []


@pytest.mark.asyncio
async def test_m1_no_guardar_usuario_id_da_rojo(base, monkeypatch):
    async def sin_guardar(session, operador_id):
        return "x"
    monkeypatch.setattr(motor, "enlazar_usuario", sin_guardar)
    await _orden(base, "alta", "m1@evydentia.test", "M1")
    assert "el operador no guarda usuario_id" in guardia_alta(base, "m1@evydentia.test")


@pytest.mark.asyncio
async def test_r1_vincular_enlaza_a_todos_y_se_repite_sin_efecto(base):
    assert await guardia_vincular(base, motor.vincular_operadores) == []


@pytest.mark.asyncio
async def test_m2_crear_un_usuario_por_cada_ejecucion_da_rojo(base):
    async def siempre_crea(session):
        for o in base.operadores:
            if o["activo"]:
                nuevo = str(uuid4())
                base.usuarios[nuevo] = {"id": nuevo, "email": o["email"], "google_sub": None}
                o["usuario_id"] = nuevo
        return []
    assert "repetir vincular crea filas" in await guardia_vincular(base, siempre_crea)


@pytest.mark.asyncio
async def test_vincular_por_la_linea_de_ordenes_lista_los_enlazados(base, capsys):
    base.operador("e@evydentia.test")
    await _orden(base, "vincular")
    assert "e@evydentia.test  usuario=sí" in capsys.readouterr().out


# --- R3: baja inmediata ---

@pytest.mark.asyncio
async def test_r3_tras_la_baja_ya_no_esta_activo(base):
    assert await guardia_baja(base, motor.operador_activo) == []


@pytest.mark.asyncio
async def test_m3_una_cache_de_la_respuesta_da_rojo(base):
    cache: dict[str, bool] = {}

    async def con_cache(session, usuario_id):
        if usuario_id not in cache:
            cache[usuario_id] = await motor.operador_activo(session, usuario_id)
        return cache[usuario_id]
    assert "tras la baja sigue activo" in await guardia_baja(base, con_cache)


# --- R2: identidad del operador, igual en la demo ---

@pytest.mark.asyncio
async def test_r2_otro_sub_no_identifica_y_el_vinculado_si(base):
    assert await guardia_identidad(base, motor.usuario_de_operador) == []


@pytest.mark.asyncio
async def test_r2_el_primer_sub_se_vincula(base):
    usuario = await motor.enlazar_usuario(base, base.operador("f@evydentia.test")["id"])
    assert await motor.usuario_de_operador(base, "f@evydentia.test", "sub-f") == usuario
    assert base.operadores[-1]["google_sub"] == "sub-f"
    assert await motor.usuario_de_operador(base, "f@evydentia.test", "sub-otro") is None


@pytest.mark.asyncio
async def test_r2_con_app_env_demo_no_pasa_por_el_resolutor(base, monkeypatch):
    from app_core import security
    monkeypatch.setenv("APP_ENV", "demo")

    async def resolutor(session, identidad):
        return "persona-ficticia-demo"
    monkeypatch.setattr(security, "_resolutor_identidad", resolutor)
    assert await guardia_identidad(base, motor.usuario_de_operador) == []


@pytest.mark.asyncio
async def test_m4_resolver_por_el_resolutor_de_la_demo_da_rojo(base, monkeypatch):
    from app_core import security
    monkeypatch.setenv("APP_ENV", "demo")

    async def resolutor(session, identidad):
        return "persona-ficticia-demo"
    monkeypatch.setattr(security, "_resolutor_identidad", resolutor)

    async def por_resolutor(session, email, sub):
        return await security._resolutor_identidad(session, {"email": email, "sub": sub})
    assert "el operador no se identifica con su usuario_id" in await guardia_identidad(base, por_resolutor)


@pytest.mark.asyncio
async def test_sin_usuario_id_no_identifica(base):
    base.operador("g@evydentia.test")
    assert await motor.usuario_de_operador(base, "g@evydentia.test", "sub-g") is None


@pytest.mark.asyncio
async def test_listar_operadores_activos_dice_quien_ha_entrado(base):
    usuario = await motor.enlazar_usuario(base, base.operador("h@evydentia.test", nombre="Hache")["id"])
    base.usuarios[usuario]["google_sub"] = "sub-h"
    base.operador("i@evydentia.test", activo=False)
    filas = await motor.listar_operadores_activos(base)
    assert filas == [{"usuario_id": usuario, "nombre": "Hache", "email": "h@evydentia.test", "ha_entrado": True}]


def test_el_pasillo_expone_las_tres_funciones():
    from app_core.pasillo import plataforma as pasillo
    for nombre in ("operador_activo", "usuario_de_operador", "listar_operadores_activos"):
        assert callable(getattr(pasillo, nombre))


def test_verificar_operador_no_cambia():
    import inspect
    fuente = inspect.getsource(motor.verificar_operador)
    assert "usuario_id" not in fuente and "OPERADOR_NO_AUTORIZADO" in fuente


# --- Base de pruebas (se omiten sin TEST_DATABASE_URL) ---

@pytest_asyncio.fixture
async def db():
    from conftest import exigir_base_de_pruebas

    url = os.environ.get("TEST_DATABASE_URL", "")
    if not url:
        pytest.skip("Persistencia pendiente: falta TEST_DATABASE_URL")
    exigir_base_de_pruebas()
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_async_engine(url, echo=False, hide_parameters=True)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            if not (await conexion.execute(text(
                    "SELECT 1 FROM information_schema.columns WHERE table_name='operadores_plataforma' "
                    "AND column_name='usuario_id'"))).scalar():
                pytest.fail("Aplicar la migración de OPE-01 en la base de pruebas antes de este árbitro", pytrace=False)
            async with AsyncSession(bind=conexion, expire_on_commit=False,
                                    join_transaction_mode="create_savepoint") as sesion:
                yield sesion
        finally:
            await transaccion.rollback()
    await engine.dispose()


@pytest.mark.asyncio
async def test_db_alta_y_vincular_enlazan_sin_membresia(db):
    from features.plataforma import administrar_operadores as cli
    correo = f"ope01-{uuid4().hex[:8]}@evydentia.test"
    await cli.ejecutar(db, argparse.Namespace(accion="alta", correo=correo, nombre="Operadora sintética"))
    fila = (await db.execute(text(
        "SELECT o.usuario_id, u.email FROM operadores_plataforma o JOIN users u ON u.id=o.usuario_id "
        "WHERE o.email=:e"), {"e": correo})).mappings().first()
    assert fila and fila["email"] == correo
    roles = (await db.execute(text("SELECT count(*) FROM user_tenant_roles WHERE user_id=:u"),
                              {"u": fila["usuario_id"]})).scalar()
    assert roles == 0
    await cli.ejecutar(db, argparse.Namespace(accion="vincular"))
    tras_la_primera = (await db.execute(text("SELECT count(*) FROM users"))).scalar()
    await cli.ejecutar(db, argparse.Namespace(accion="vincular"))
    sin_usuario = (await db.execute(text(
        "SELECT count(*) FROM operadores_plataforma WHERE activo AND usuario_id IS NULL"))).scalar()
    assert sin_usuario == 0
    assert (await db.execute(text("SELECT count(*) FROM users"))).scalar() == tras_la_primera
    await cli.ejecutar(db, argparse.Namespace(accion="baja", correo=correo))
    assert await motor.operador_activo(db, fila["usuario_id"]) is False


@pytest.mark.asyncio
async def test_db_usuario_unico_por_operador(db):
    from sqlalchemy.exc import IntegrityError
    correo = f"ope01-{uuid4().hex[:8]}@evydentia.test"
    usuario = str(uuid4())
    await db.execute(text("INSERT INTO users(id,email,nombre) VALUES (:id,:e,'u')"), {"id": usuario, "e": correo})
    for n in range(2):
        with pytest.raises(IntegrityError) if n else _nada():
            async with db.begin_nested():
                await db.execute(text(
                    "INSERT INTO operadores_plataforma (id, email, nombre, activo, usuario_id) "
                    "VALUES (:id, :e, 'o', TRUE, :u)"), {"id": str(uuid4()), "e": f"{n}{correo}", "u": usuario})


class _nada:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False
