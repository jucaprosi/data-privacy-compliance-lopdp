# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤arbitro ¤seguridad
"""BIB-411: capacidades editoriales para operadores activos, concedidas por otro operador.

Dos capas. Sin base: el servicio y las rutas contra una sesión simulada que imita las funciones
`SECURITY DEFINER` de la migración, con el pasillo de plataforma sustituido. Con base (`test_db_*`): las
funciones y los CHECK en el PostgreSQL de pruebas, dentro de una transacción que se deshace; se omiten sin
`TEST_DATABASE_URL`. Cada mutación m1 a m11 de la especificación §5 tiene su prueba: la mutación aplicada
hace que la guardia dé rojo.
"""
import importlib.util
import os
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app_core.errors import ErrorNegocio
from features.biblioteca.services import autorizacion
from features.biblioteca.services import capacidades_admin as admin

RAIZ = Path(__file__).resolve().parents[1]
_ruta = RAIZ / "alembic" / "versions" / "20261125_bib411_operadores.py"
_spec = importlib.util.spec_from_file_location("_bib411_operadores", _ruta)
MIG = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(MIG)
MOTIVO = "Motivo de la prueba"


# --- Sesión simulada: las funciones de la migración, en memoria ---

class _Resultado:
    def __init__(self, filas=None, valor=None):
        self._filas, self._valor = filas or [], valor

    def scalars(self):
        return iter(self._valor or [])

    def scalar(self):
        return self._valor

    def all(self):
        return self._filas

    def mappings(self):
        return self


class Base:
    def __init__(self):
        self.operadores: dict[str, bool] = {}
        self.ha_entrado: dict[str, bool] = {}
        self.capacidades: dict[tuple[str, str], dict] = {}
        self.actor: str | None = None

    def operador(self, usuario_id, activo=True, ha_entrado=True):
        self.operadores[usuario_id] = activo
        self.ha_entrado[usuario_id] = ha_entrado
        return usuario_id

    @asynccontextmanager
    async def begin_nested(self):
        yield

    def _funcion(self, conceder: bool, destino, capacidad, motivo):
        if self.actor == destino:
            raise ErrorNegocio("BIB_AUTOCONCESION")
        fila = self.capacidades.get((destino, capacidad))
        if conceder:
            if fila is None:
                self.capacidades[(destino, capacidad)] = {"por": self.actor, "motivo": motivo, "revocada": False}
                return "alta"
            if not fila["revocada"]:
                return "vigente"
            fila.update(por=self.actor, motivo=motivo, revocada=False)
            return "reactivacion"
        if fila is None or fila["revocada"]:
            return "sin_vigente"
        fila.update(revocada=True, retirada_por=self.actor, motivo_retiro=motivo)
        return "revocacion"

    async def execute(self, sentencia, p=None):
        p = p or {}
        if sentencia is admin._ACTOR:
            self.actor = p["actor"]
            return _Resultado()
        if sentencia is admin._CONCEDER or sentencia is admin._RETIRAR:
            return _Resultado(valor=self._funcion(sentencia is admin._CONCEDER, p["u"], p["c"], p["m"]))
        sql = str(sentencia)
        if "set_config('app.current_user_id'" in sql:
            return _Resultado()
        if sql.startswith("SELECT capacidad FROM biblioteca_capacidades"):
            return _Resultado(valor=[c for (u, c), f in self.capacidades.items() if u == p["actor"] and not f["revocada"]])
        raise AssertionError(f"Sentencia no prevista: {sql[:80]}")


@pytest.fixture
def base(monkeypatch):
    from app_core.pasillo import plataforma as pasillo_plataforma

    base = Base()

    async def operador_activo(session, usuario_id):
        return base.operadores.get(usuario_id, False)
    monkeypatch.setattr(pasillo_plataforma, "operador_activo", operador_activo)
    return base


# --- Guardias ---

async def guardia_r1(base, capacidades) -> list[str]:
    org = "persona-de-organizacion"
    base.capacidades[(org, "publicador")] = {"por": "x", "motivo": MOTIVO, "revocada": False}
    return ["cuenta la capacidad de quien no es operador"] if await capacidades(base, org) else []


async def guardia_concede_sin_capacidades(base, conceder) -> list[str]:
    a, b = base.operador("op-a"), base.operador("op-b")
    if await conceder(base, b, "editor", a, MOTIVO) != "alta":
        return ["un operador sin capacidades no concede"]
    fila = base.capacidades[(b, "editor")]
    return [] if (fila["por"], fila["motivo"]) == (a, MOTIVO) else ["no queda quién ni el motivo"]


async def guardia_autoconcesion(base, conceder) -> list[str]:
    a = base.operador("op-a")
    fallos = []
    for destino, codigo in ((a, "BIB_AUTOCONCESION"), ("no-operador", "BIB_DESTINO_NO_OPERADOR")):
        try:
            await conceder(base, destino, "editor", a, MOTIVO)
            fallos.append(f"se acepta lo que debe dar {codigo}")
        except ErrorNegocio as exc:
            if exc.code != codigo:
                fallos.append(f"da {exc.code} en vez de {codigo}")
    return fallos


async def guardia_solo_operadores(base, exigir) -> list[str]:
    try:
        await exigir(base, "persona-de-organizacion")
    except ErrorNegocio as exc:
        return [] if exc.code == "BIB_SOLO_OPERADORES" else [f"da {exc.code}"]
    return ["un usuario de organización entra al equipo"]


async def guardia_baja(base, dar_de_baja) -> list[str]:
    b = base.operador("op-b")
    base.capacidades[(b, "revisor_tecnico")] = {"por": "op-a", "motivo": MOTIVO, "revocada": False}
    dar_de_baja(base, b)
    fallos = []
    if await autorizacion.capacidades(base, b):
        fallos.append("tras la baja conserva la capacidad")
    base.operadores[b] = True
    if await autorizacion.capacidades(base, b) != ["revisor_tecnico"]:
        fallos.append("al reactivarlo no recupera la capacidad")
    return fallos


async def guardia_sin_entrar(base, conceder) -> list[str]:
    a, c = base.operador("op-a"), base.operador("op-c", ha_entrado=False)
    try:
        resultado = await conceder(base, c, "publicador", a, MOTIVO)
    except ErrorNegocio as exc:
        return [f"no se concede a quien no ha entrado ({exc.code})"]
    return [] if resultado == "alta" else ["no se concede a quien no ha entrado"]


async def guardia_motivo(base, conceder) -> list[str]:
    a, b = base.operador("op-a"), base.operador("op-b")
    fallos = []
    try:
        await conceder(base, b, "editor", a, "  nueve car  ")
        fallos.append("se acepta un motivo de 9 caracteres")
    except ErrorNegocio as exc:
        if exc.code != "BIB_MOTIVO_OBLIGATORIO":
            fallos.append(f"da {exc.code}")
    if await conceder(base, b, "editor", a, "diez letra") != "alta" or \
            await conceder(base, b, "editor", a, "diez letra") != "vigente":
        fallos.append("repetir no da vigente")
    return fallos


# --- R1 y R4 ---

@pytest.mark.asyncio
async def test_r1_no_cuenta_la_capacidad_de_quien_no_es_operador(base):
    assert await guardia_r1(base, autorizacion.capacidades) == []


@pytest.mark.asyncio
async def test_m1_quitar_el_filtro_de_operador_da_rojo(base, monkeypatch):
    async def siempre(session, usuario_id):
        return True
    monkeypatch.setattr(autorizacion, "_operador_activo", siempre)
    assert "cuenta la capacidad de quien no es operador" in await guardia_r1(base, autorizacion.capacidades)


def _baja(base, usuario_id):
    base.operadores[usuario_id] = False


@pytest.mark.asyncio
async def test_r4_la_baja_quita_las_capacidades_sin_tocar_filas(base):
    assert await guardia_baja(base, _baja) == []


@pytest.mark.asyncio
async def test_m5_borrar_las_filas_en_la_baja_da_rojo(base):
    def baja_que_borra(base, usuario_id):
        _baja(base, usuario_id)
        for clave in [k for k in base.capacidades if k[0] == usuario_id]:
            del base.capacidades[clave]
    assert "al reactivarlo no recupera la capacidad" in await guardia_baja(base, baja_que_borra)


# --- R2, R2b, R3 y R5 ---

@pytest.mark.asyncio
async def test_r2_concede_un_operador_sin_capacidades_y_queda_quien_y_motivo(base):
    assert await guardia_concede_sin_capacidades(base, admin.conceder) == []


@pytest.mark.asyncio
async def test_m2_exigir_capacidades_al_que_concede_da_rojo(base):
    async def exigiendo(session, usuario_id, capacidad, otorgante, motivo):
        await autorizacion.autorizar(session, otorgante)
        return await admin.conceder(session, usuario_id, capacidad, otorgante, motivo)
    with pytest.raises(ErrorNegocio):
        assert await guardia_concede_sin_capacidades(base, exigiendo)


@pytest.mark.asyncio
async def test_r2_autoconcesion_y_destino_que_no_es_operador(base):
    assert await guardia_autoconcesion(base, admin.conceder) == []


@pytest.mark.asyncio
async def test_m3_aceptar_la_autoconcesion_da_rojo(base, monkeypatch):
    def sin_autoconcesion(usuario_id, capacidad, otorgante, motivo):
        return admin._capacidad(capacidad), admin._motivo(motivo)
    monkeypatch.setattr(admin, "_validar", sin_autoconcesion)
    base.actor = None

    async def conceder(session, destino, capacidad, otorgante, motivo):
        resultado = await admin.conceder(session, destino, capacidad, otorgante, motivo)
        return resultado
    original = base._funcion
    base._funcion = lambda c, d, cap, m: "alta"  # la base mutada tampoco lo revisa
    try:
        assert "se acepta lo que debe dar BIB_AUTOCONCESION" in await guardia_autoconcesion(base, conceder)
    finally:
        base._funcion = original


@pytest.mark.asyncio
async def test_r3_se_concede_a_quien_aun_no_ha_entrado(base):
    assert await guardia_sin_entrar(base, admin.conceder) == []


@pytest.mark.asyncio
async def test_m6_exigir_ha_entrado_da_rojo(base):
    async def exigiendo(session, usuario_id, capacidad, otorgante, motivo):
        if not base.ha_entrado.get(usuario_id):
            raise ErrorNegocio("BIB_DESTINO_NO_OPERADOR")
        return await admin.conceder(session, usuario_id, capacidad, otorgante, motivo)
    assert await guardia_sin_entrar(base, exigiendo) != []


@pytest.mark.asyncio
async def test_r2_motivo_de_diez_y_repetir_da_vigente(base):
    assert await guardia_motivo(base, admin.conceder) == []


@pytest.mark.asyncio
async def test_m8_aceptar_nueve_caracteres_da_rojo(base, monkeypatch):
    monkeypatch.setattr(admin, "MOTIVO_MINIMO", 9)
    assert "se acepta un motivo de 9 caracteres" in await guardia_motivo(base, admin.conceder)


@pytest.mark.asyncio
async def test_retirar_dos_veces_da_sin_vigente(base):
    a, b = base.operador("op-a"), base.operador("op-b")
    await admin.conceder(base, b, "editor", a, MOTIVO)
    assert await admin.revocar(base, b, "editor", a, MOTIVO) == "revocacion"
    assert await admin.revocar(base, b, "editor", a, MOTIVO) == "sin_vigente"


@pytest.mark.parametrize("capacidad", ["revisor_juridico", "inventada"])
@pytest.mark.asyncio
async def test_r6_solo_tres_capacidades(base, capacidad):
    a, b = base.operador("op-a"), base.operador("op-b")
    with pytest.raises(ErrorNegocio) as exc:
        await admin.conceder(base, b, capacidad, a, MOTIVO)
    assert exc.value.code == "BIB_CAPACIDAD_INVALIDA"


def test_r6_errores_y_enum():
    from app_core.errors import CATALOGO_ERRORES
    from features.biblioteca.domain import errores  # noqa: F401  registra los códigos
    from features.biblioteca.domain.editorial import Capacidad

    assert {c.value for c in Capacidad} == {"editor", "revisor_tecnico", "publicador"}
    esperado = {"BIB_SOLO_OPERADORES": 403, "BIB_AUTOCONCESION": 403, "BIB_DESTINO_NO_OPERADOR": 422,
                "BIB_MOTIVO_OBLIGATORIO": 422, "BIB_CAPACIDAD_INVALIDA": 422}
    for codigo, estado in esperado.items():
        assert CATALOGO_ERRORES[codigo].status_code == estado, codigo
    assert CATALOGO_ERRORES["BIB_CAPACIDAD_INVALIDA"].mensaje_defecto == "Elige una de las capacidades de la lista."
    assert "10 caracteres" in CATALOGO_ERRORES["BIB_MOTIVO_OBLIGATORIO"].mensaje_defecto


# --- §2 y R8: rutas ---

@pytest.fixture(autouse=True)
def _url_de_importacion(monkeypatch):
    """Las rutas importan `app_core.db.session`, que exige DATABASE_URL; el motor no abre conexión."""
    if not os.environ.get("DATABASE_URL"):
        monkeypatch.setenv("DATABASE_URL", "postgresql://prueba@127.0.0.1:5432/prueba")

@pytest.mark.asyncio
async def test_r2_el_equipo_es_solo_para_operadores(base):
    from api.routers import biblioteca_capacidades as rutas
    assert await guardia_solo_operadores(base, rutas.operador_activo) == []


@pytest.mark.asyncio
async def test_m4_abrir_el_equipo_a_cualquier_usuario_da_rojo(base):
    async def abierto(session, actor):
        return actor
    assert "un usuario de organización entra al equipo" in await guardia_solo_operadores(base, abierto)


def test_las_rutas_del_equipo_exigen_operador_activo():
    from api.routers import biblioteca_capacidades as rutas
    caminos = {r.path: r for r in rutas.router.routes}
    for camino in ("/biblioteca/capacidades/equipo", "/biblioteca/capacidades/equipo/{usuario_id}/conceder",
                   "/biblioteca/capacidades/equipo/{usuario_id}/retirar", "/biblioteca/capacidades/equipo/historial"):
        dependencias = {d.call for d in caminos[camino].dependant.dependencies}
        assert rutas.operador_activo in dependencias, camino


async def guardia_identidad(monkeypatch, dependencia) -> list[str]:
    from app_core import security
    from app_core.pasillo import plataforma as pasillo_plataforma

    monkeypatch.setenv("APP_ENV", "demo")
    monkeypatch.setattr(security, "modo_autenticacion", lambda: "oidc")

    async def token(_):
        return security.IdentidadVerificada(sub="sub-op", email="op@evydentia.test")
    monkeypatch.setattr(security, "verificar_token_google", token)

    async def resolutor(session, identidad):
        return "persona-ficticia-demo"
    monkeypatch.setattr(security, "_resolutor_identidad", resolutor, raising=False)

    async def usuario_de_operador(session, email, sub):
        return "usuario-del-operador" if (email, sub) == ("op@evydentia.test", "sub-op") else None
    monkeypatch.setattr(pasillo_plataforma, "usuario_de_operador", usuario_de_operador)
    actor = await dependencia("Bearer t", "", None)
    return [] if actor == "usuario-del-operador" else [f"identifica a {actor}"]


@pytest.mark.asyncio
async def test_r8_en_la_demo_el_operador_es_su_usuario(monkeypatch):
    from api.routers import biblioteca_capacidades as rutas
    assert await guardia_identidad(monkeypatch, rutas.operador_de_la_peticion) == []


@pytest.mark.asyncio
async def test_m9_usar_get_usuario_autenticado_da_rojo(monkeypatch):
    from app_core import security

    async def por_la_demo(authorization, x_user_id, session):
        identidad = await security.verificar_token_google(authorization)
        return await security._resolutor_identidad(session, identidad)
    assert await guardia_identidad(monkeypatch, por_la_demo) != []


def test_r8_las_rutas_editoriales_usan_la_identidad_del_operador():
    from api.routers import biblioteca_capacidades as rutas
    from api.routers import biblioteca_editorial as editorial

    fuente = (RAIZ / "api/routers/biblioteca_editorial.py").read_bytes().decode("utf-8")
    assert "get_usuario_autenticado" not in fuente
    for ruta in editorial.router.routes:
        llamadas = {d.call for d in ruta.dependant.dependencies}
        assert rutas.operador_identificado in llamadas, ruta.path


# --- Pasillo ---

@pytest.mark.asyncio
async def test_el_pasillo_ofrece_cambios_y_filtra_revisores(monkeypatch):
    from app_core.pasillo import biblioteca as pasillo
    from app_core.pasillo import plataforma as pasillo_plataforma

    class Sesion:
        async def execute(self, sentencia, p=None):
            return _Resultado(filas=[("op-vigente",), ("ya-no-es-operador",)])

    async def operador_activo(session, usuario_id):
        return usuario_id == "op-vigente"
    monkeypatch.setattr(pasillo_plataforma, "operador_activo", operador_activo)
    assert await pasillo.revisores_tecnicos(Sesion()) == ["op-vigente"]
    assert callable(pasillo.cambios_de_capacidades)


def test_la_migracion_cuelga_de_bib415_y_retira_lo_juridico():
    assert MIG.down_revision == "20261126_bib415_lectura_avisos" and MIG.branch_labels is None
    assert "CHECK (capacidad IN ('editor','revisor_tecnico','publicador'))" in MIG.TRES_CAPACIDADES
    assert "CHECK (tipo IN ('tecnica'))" in MIG.TRES_CAPACIDADES
    for sql in (MIG.CONCEDER, MIG.RETIRAR, MIG.EQUIPO, MIG.HISTORIAL, MIG.CAMBIOS):
        assert "SECURITY DEFINER SET search_path = pg_catalog, public" in sql
    for sql in (MIG.CONCEDER, MIG.RETIRAR):
        assert "plataforma_operador_activo(v_actor)" in sql and "plataforma_operador_activo(p_destino)" in sql
    assert "GRANT INSERT" not in MIG.PERMISOS and "ON biblioteca_capacidades " not in MIG.PERMISOS


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
            ids = {n: "bib411-" + n + "-" + uuid4().hex[:8] for n in ("a", "b", "org")}
            for nombre, usuario in ids.items():
                await conexion.execute(text("INSERT INTO users(id,email,nombre) VALUES (:id,:e,'Sintético')"),
                                       {"id": usuario, "e": usuario + "@correo.invalid"})
            for nombre in ("a", "b"):
                await conexion.execute(text(
                    "INSERT INTO operadores_plataforma (id, email, nombre, usuario_id) VALUES (:o, :e, 'Sintético', :u)"),
                    {"o": "op-" + ids[nombre], "e": ids[nombre] + "@correo.invalid", "u": ids[nombre]})
            yield conexion, ids
        finally:
            await transaccion.rollback()
    await engine.dispose()


async def _como_app(conexion, actor):
    await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
    await conexion.execute(text("SELECT set_config('app.current_user_id', :a, true)"), {"a": actor})


async def _conceder(conexion, destino, capacidad="editor", motivo=MOTIVO):
    async with conexion.begin_nested():
        return (await conexion.execute(text("SELECT biblioteca_conceder_capacidad(:u, :c, :m)"),
                                       {"u": destino, "c": capacidad, "m": motivo})).scalar()


async def guardia_db_juridica(conexion, ids) -> list[str]:
    try:
        async with conexion.begin_nested():
            await conexion.execute(text(
                "INSERT INTO biblioteca_capacidades(usuario_id,capacidad,concedida_por,motivo) "
                "VALUES (:u,'revisor_juridico',:o,'Motivo de prueba')"), {"u": ids["b"], "o": ids["a"]})
    except DBAPIError:
        return []
    return ["la base acepta revisor_juridico"]


@pytest.mark.asyncio
async def test_db_la_base_rechaza_lo_juridico(db):
    conexion, ids = db
    assert await guardia_db_juridica(conexion, ids) == []
    consulta = text("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname='biblioteca_revisiones_tipo_check'")
    assert "juridica" not in (await conexion.execute(consulta)).scalar()


@pytest.mark.asyncio
async def test_db_m7_dejar_juridica_en_el_check_da_rojo(db):
    conexion, ids = db
    await conexion.execute(text("ALTER TABLE biblioteca_capacidades DROP CONSTRAINT biblioteca_capacidades_capacidad_check"))
    await conexion.execute(text(
        "ALTER TABLE biblioteca_capacidades ADD CONSTRAINT biblioteca_capacidades_capacidad_check "
        "CHECK (capacidad IN ('editor','revisor_tecnico','revisor_juridico','publicador'))"))
    assert "la base acepta revisor_juridico" in await guardia_db_juridica(conexion, ids)


async def guardia_db_sin_escritura(conexion, ids) -> list[str]:
    privilegio = (await conexion.execute(text(
        "SELECT has_table_privilege('lopdp_app','biblioteca_capacidades','INSERT') "
        "OR has_table_privilege('lopdp_app','biblioteca_capacidades','UPDATE')"))).scalar()
    fallos = ["lopdp_app puede escribir en biblioteca_capacidades"] if privilegio else []
    await _como_app(conexion, ids["a"])
    try:
        await _conceder(conexion, ids["a"])
        fallos.append("la función acepta la autoconcesión")
    except DBAPIError as exc:
        if "BIB_AUTOCONCESION" not in str(exc.orig):
            fallos.append("la autoconcesión no da BIB_AUTOCONCESION")
    await conexion.execute(text("RESET ROLE"))
    return fallos


@pytest.mark.asyncio
async def test_db_lopdp_app_sin_escritura_y_sin_autoconcesion(db):
    conexion, ids = db
    assert await guardia_db_sin_escritura(conexion, ids) == []


@pytest.mark.asyncio
async def test_db_m10_dar_insert_a_lopdp_app_da_rojo(db):
    conexion, ids = db
    await conexion.execute(text("GRANT INSERT ON biblioteca_capacidades TO lopdp_app"))
    assert "lopdp_app puede escribir en biblioteca_capacidades" in await guardia_db_sin_escritura(conexion, ids)


async def guardia_db_operadores(conexion, ids) -> list[str]:
    fallos = []
    for actor, destino in ((ids["org"], ids["b"]), (ids["a"], ids["org"])):
        await _como_app(conexion, actor)
        try:
            await _conceder(conexion, destino)
            fallos.append("la base escribe sin dos operadores activos")
        except DBAPIError:
            pass
        await conexion.execute(text("RESET ROLE"))
    filas = (await conexion.execute(text(
        "SELECT count(*) FROM biblioteca_capacidades WHERE usuario_id IN (:b, :org)"),
        {"b": ids["b"], "org": ids["org"]})).scalar()
    if filas:
        fallos.append("quedó una fila escrita")
    return fallos


@pytest.mark.asyncio
async def test_db_la_funcion_exige_operadores_activos(db):
    conexion, ids = db
    assert await guardia_db_operadores(conexion, ids) == []


@pytest.mark.asyncio
async def test_db_m11_quitar_la_comprobacion_de_la_funcion_da_rojo(db):
    conexion, ids = db
    mutada = (MIG.CONCEDER
              .replace("IF NOT coalesce(public.plataforma_operador_activo(v_actor), false) THEN", "IF false THEN")
              .replace("IF NOT coalesce(public.plataforma_operador_activo(p_destino), false) THEN", "IF false THEN"))
    assert mutada.count("IF false THEN") == 2
    await conexion.execute(text(mutada))
    assert "la base escribe sin dos operadores activos" in await guardia_db_operadores(conexion, ids)


@pytest.mark.asyncio
async def test_db_conceder_retirar_e_historial_como_lopdp_app(db):
    conexion, ids = db
    await _como_app(conexion, ids["a"])
    assert await _conceder(conexion, ids["b"]) == "alta"
    assert await _conceder(conexion, ids["b"]) == "vigente"
    retiro = (await conexion.execute(text("SELECT biblioteca_retirar_capacidad(:u, 'editor', :m)"),
                                     {"u": ids["b"], "m": "Retiro de la prueba"})).scalar()
    assert retiro == "revocacion"
    historial = (await conexion.execute(text(
        "SELECT accion, por, motivo FROM biblioteca_historial_capacidades(:u) ORDER BY id"), {"u": ids["b"]})).all()
    assert [tuple(f) for f in historial] == [("concedida", ids["a"], MOTIVO), ("retirada", ids["a"], "Retiro de la prueba")]
    cambios = (await conexion.execute(text(
        "SELECT usuario_id, accion FROM biblioteca_cambios_capacidades(now() - interval '1 hour') "
        "WHERE usuario_id = :u"), {"u": ids["b"]})).all()
    assert [tuple(f) for f in cambios] == [(ids["b"], "concedida"), (ids["b"], "retirada")]
