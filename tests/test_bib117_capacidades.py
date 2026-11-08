# ¤seguridad ¤arbitro
# ¤¤qa-engineer
"""Árbitro BIB-117: conceder, revocar y reactivar capacidades de la Biblioteca por script, sin endpoint.

Persistencia sobre PostgreSQL 16 real (TEST_DATABASE_URL), en una transacción que se revierte, con usuarios
sintéticos y correos `.invalid`. Para que la RLS forzada actúe de verdad, el motor corre como un rol temporal
sin superusuario ni BYPASSRLS y miembro del dueño de las tablas: así se comporta el dueño en Cloud SQL. En el
CI el dueño es superusuario y, sin este rol, las políticas no se probarían.

Límite conocido: el disparador `bib_auditar_capacidad` es SECURITY DEFINER del dueño; donde el dueño es
superusuario no lo frena la RLS. Por eso la política de INSERT de la auditoría se comprueba en el catálogo
(`test_la_migracion_solo_abre_la_escritura_al_dueno`).

Mutaciones documentadas (ficha BIB-117):
- M1: quitar `bib_cap_sin_autoconcesion` de la migración hace fallar
  `test_autoconcesion_la_rechazan_el_motor_y_la_base` (el INSERT directo pasa).
- M2: que `motivo_de_rechazo` no llame a `apunta_a_produccion` hace fallar
  `test_guardia_no_conecta_con_produccion_ni_sin_confirmar[produccion]`.
- M3: revocar con DELETE hace fallar `test_conceder_revocar_y_reactivar_quedan_auditados` (la auditoría
  registra `baja`) y `test_no_existe_ninguna_ruta_de_borrado`.
"""
import ast
import os
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app_core.errors import ErrorNegocio
from app_core.huellas_produccion import HUELLA_HOST_PRODUCCION
from features.biblioteca import biblioteca_service as bib
from features.biblioteca.domain.editorial import Capacidad
from features.biblioteca.services.autorizacion import autorizar

RAIZ = Path(__file__).resolve().parent.parent
MOTOR = RAIZ / "features" / "biblioteca" / "services" / "capacidades_admin.py"
SCRIPT = RAIZ / "scripts" / "capacidades_biblioteca.py"


# ----------------------------------------------------------------------------- sin base

def _codigo(error: pytest.ExceptionInfo) -> str:
    return getattr(error.value, "code", None) or str(error.value)


def test_la_compuerta_expone_el_motor_y_no_hay_endpoint():
    assert {"conceder_capacidad", "revocar_capacidad", "listar_capacidades"} <= set(bib.__all__)
    rutas = "\n".join(p.read_text(encoding="utf-8") for p in (RAIZ / "api").rglob("*.py"))
    assert "conceder_capacidad" not in rutas and "revocar_capacidad" not in rutas and "capacidades_admin" not in rutas


def test_no_existe_ninguna_ruta_de_borrado():
    motor = MOTOR.read_text(encoding="utf-8")
    assert "DELETE" not in motor.upper().replace("DELETED_AT", "")
    script = SCRIPT.read_text(encoding="utf-8")
    assert "--baja" not in script and "--borrar" not in script and "DELETE" not in script.upper()


@pytest.fixture
def script(monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location("capacidades_biblioteca", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    async def no_conectar(*_):
        raise AssertionError("La guardia dejó abrir una conexión")
    monkeypatch.setattr(modulo, "_ejecutar", no_conectar)
    return modulo


@pytest.mark.parametrize("caso, url, confirmar", [
    ("sin_url", "", True),
    ("sin_confirmar", "postgresql://dueno:x@localhost:5432/rama", False),
    # Huella simulada que solo conoce apunta_a_produccion (no está en la lista de BIB-109): aísla M2.
    ("produccion", "postgresql://dueno:x@ep-huella-simulada-pooler.neon.invalid/db", True),
    ("cloud_sql_produccion", "postgresql://dueno:x@/evydentia_prod?host=/cloudsql/p:r:evydentia-production", True),
    ("rama_test_compartida", "postgresql://dueno:x@ep-soft-darkness-b5z454vp.neon.invalid/db", True),
])
def test_guardia_no_conecta_con_produccion_ni_sin_confirmar(script, monkeypatch, capsys, caso, url, confirmar):
    monkeypatch.setattr("app_core.huellas_produccion.HUELLA_HOST_PRODUCCION", "ep-huella-simulada")
    monkeypatch.setenv(script.VARIABLE_URL, url)
    argv = ["--conceder", "--usuario", "u", "--capacidad", "editor", "--otorgante", "o", "--motivo", "m"]
    assert script.main(argv + (["--confirmar-rama-desarrollo"] if confirmar else [])) == 2
    salida = capsys.readouterr().out
    assert url == "" or url not in salida


def test_guardia_lee_la_lista_de_hosts_de_bib109(script):
    arbol = ast.parse((RAIZ / "scripts" / "cargar_plantillas_pmv.py").read_text(encoding="utf-8"))
    assert "ep-soft-darkness-b5z454vp" in script.hosts_de_bib109()
    assert any(isinstance(n, ast.Assign) for n in arbol.body)


@pytest.mark.parametrize("capacidad, motivo, otorgante, codigo", [
    ("inventada", "m", "o", "BIB_CAPACIDAD_INVALIDA"),
    ("editor", "", "o", "BIB_MOTIVO_OBLIGATORIO"),
    ("editor", "   ", "o", "BIB_MOTIVO_OBLIGATORIO"),
    ("editor", "m", "u", "BIB_AUTOCONCESION"),
])
@pytest.mark.asyncio
async def test_validaciones_previas_no_tocan_la_base(capacidad, motivo, otorgante, codigo):
    class SinBase:
        async def execute(self, *_a, **_k):
            raise AssertionError("se consultó la base antes de validar")
    for accion in (bib.conceder_capacidad, bib.revocar_capacidad):
        with pytest.raises(ErrorNegocio) as error:
            await accion(SinBase(), "u", capacidad, otorgante, motivo)
        assert codigo in _codigo(error)


# ----------------------------------------------------------------------------- PostgreSQL real

def _url() -> str:
    url = os.environ.get("TEST_DATABASE_URL", "")
    if HUELLA_HOST_PRODUCCION in url.lower():
        pytest.fail("Host de producción prohibido; no se abrió conexión", pytrace=False)
    if not url:
        pytest.skip("BIB-117 sin acreditar: falta TEST_DATABASE_URL (PostgreSQL 16 local o del CI)")
    return url.replace("postgresql://", "postgresql+psycopg://", 1) if url.startswith("postgresql://") else url


@pytest_asyncio.fixture
async def mundo():
    engine = create_async_engine(_url(), echo=False, hide_parameters=True)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            # Rol temporal (se revierte con la transacción), miembro del dueño de las tablas. El nombre va
            # por parámetro y el DDL se arma en PostgreSQL con format(%I): ningún SQL interpolado en Python.
            rol = "bib117_" + uuid4().hex[:12]
            await conexion.execute(text("SELECT set_config('bib117.rol', :rol, true)"), {"rol": rol})
            await conexion.execute(text("""
                DO $$ BEGIN
                    EXECUTE format('CREATE ROLE %I NOLOGIN NOSUPERUSER NOBYPASSRLS INHERIT',
                                   current_setting('bib117.rol'));
                    EXECUTE format('GRANT %I TO %I',
                                   (SELECT tableowner FROM pg_tables WHERE tablename='biblioteca_capacidades'),
                                   current_setting('bib117.rol'));
                END $$"""))
            ids = {n: "bib117-" + uuid4().hex for n in ("ana", "beto", "inactiva")}
            for nombre, usuario in ids.items():
                await conexion.execute(text(
                    "INSERT INTO users(id,email,nombre,activo) VALUES (:id,:e,'Sintético',:a)"),
                    {"id": usuario, "e": usuario + "@correo.invalid", "a": nombre != "inactiva"})
            await conexion.execute(text("SELECT set_config('role', :rol, true)"), {"rol": rol})
            async with AsyncSession(bind=conexion, expire_on_commit=False,
                                    join_transaction_mode="create_savepoint") as sesion:
                yield conexion, sesion, ids, rol
        finally:
            await transaccion.rollback()
    await engine.dispose()


async def _como_app(conexion, rol: str, actor: str):
    await conexion.execute(text("RESET ROLE"))
    await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
    await conexion.execute(text("SELECT set_config('app.current_user_id', :a, true)"), {"a": actor})


async def _como_dueno(conexion, rol: str):
    await conexion.execute(text("RESET ROLE"))
    await conexion.execute(text("SELECT set_config('role', :rol, true)"), {"rol": rol})


@pytest.mark.asyncio
async def test_conceder_revocar_y_reactivar_quedan_auditados(mundo):
    conexion, sesion, ids, rol = mundo
    ana, beto = ids["ana"], ids["beto"]
    assert await bib.conceder_capacidad(sesion, ana, "editor", beto, "Alta de prueba") == "alta"
    assert await bib.conceder_capacidad(sesion, ana, "editor", beto, "Otra vez") == "vigente"
    vigentes = [c for c in await bib.listar_capacidades(sesion) if c.usuario_id == ana]
    assert [(c.capacidad, c.revocada_en) for c in vigentes] == [("editor", None)]

    await _como_app(conexion, rol, ana)
    assert "editor" in await autorizar(sesion, ana, Capacidad.EDITOR)
    await _como_dueno(conexion, rol)

    assert await bib.revocar_capacidad(sesion, ana, "editor", beto, "Revocación de prueba") == "revocacion"
    assert await bib.revocar_capacidad(sesion, ana, "editor", beto, "Ya revocada") == "sin_vigente"
    await _como_app(conexion, rol, ana)
    with pytest.raises(ErrorNegocio):
        await autorizar(sesion, ana, Capacidad.EDITOR)
    await _como_dueno(conexion, rol)

    assert await bib.conceder_capacidad(sesion, ana, "editor", beto, "Reactivación de prueba") == "reactivacion"
    await _como_app(conexion, rol, ana)
    assert "editor" in await autorizar(sesion, ana, Capacidad.EDITOR)

    await conexion.execute(text("RESET ROLE"))
    filas = (await conexion.execute(text(
        "SELECT accion, actor_id, motivo, rol_bd FROM biblioteca_auditoria_capacidades "
        "WHERE usuario_id=:u ORDER BY id"), {"u": ana})).all()
    assert [f.accion for f in filas] == ["alta", "revocacion", "reactivacion"]
    assert {f.actor_id for f in filas} == {beto}
    assert [f.motivo for f in filas] == ["Alta de prueba", "Revocación de prueba", "Reactivación de prueba"]
    assert all(f.rol_bd for f in filas)


@pytest.mark.asyncio
async def test_autoconcesion_la_rechazan_el_motor_y_la_base(mundo):
    conexion, sesion, ids, rol = mundo
    ana = ids["ana"]
    with pytest.raises(ErrorNegocio) as error:
        await bib.conceder_capacidad(sesion, ana, "editor", ana, "Autoconcesión")
    assert "BIB_AUTOCONCESION" in _codigo(error)
    # Saltando el motor, con el rol de mayor privilegio (sin RLS): solo el CHECK lo impide.
    await conexion.execute(text("RESET ROLE"))
    with pytest.raises(DBAPIError) as fallo:
        async with conexion.begin_nested():
            await conexion.execute(text(
                "INSERT INTO biblioteca_capacidades(usuario_id,capacidad,concedida_por,motivo) "
                "VALUES (:u,'editor',:u,'directo')"), {"u": ana})
    assert "bib_cap_sin_autoconcesion" in str(fallo.value)
    with pytest.raises(DBAPIError) as fallo:
        async with conexion.begin_nested():
            await conexion.execute(text(
                "INSERT INTO biblioteca_capacidades(usuario_id,capacidad,concedida_por,motivo,revocada_en,"
                "revocada_por,motivo_revocacion) VALUES (:u,'editor',:b,'directo',now(),:u,'auto')"),
                {"u": ana, "b": ids["beto"]})
    assert "bib_cap_sin_autorrevocacion" in str(fallo.value)


@pytest.mark.asyncio
async def test_persona_inactiva_no_otorga_ni_recibe(mundo):
    _, sesion, ids, _ = mundo
    for usuario, otorgante in ((ids["inactiva"], ids["beto"]), (ids["ana"], ids["inactiva"])):
        with pytest.raises(ErrorNegocio) as error:
            await bib.conceder_capacidad(sesion, usuario, "editor", otorgante, "m")
        assert "BIB_USUARIO_INACTIVO" in _codigo(error)


@pytest.mark.asyncio
async def test_lopdp_app_no_puede_escribir_capacidades(mundo):
    conexion, sesion, ids, rol = mundo
    ana, beto = ids["ana"], ids["beto"]
    await bib.conceder_capacidad(sesion, ana, "editor", beto, "Alta de prueba")
    await _como_app(conexion, rol, beto)
    for sql in ("INSERT INTO biblioteca_capacidades(usuario_id,capacidad,concedida_por,motivo) "
                "VALUES (:a,'publicador',:b,'app')",
                "UPDATE biblioteca_capacidades SET revocada_en=now(), revocada_por=:b, motivo_revocacion='app' "
                "WHERE usuario_id=:a",
                "DELETE FROM biblioteca_capacidades WHERE usuario_id=:a"):
        with pytest.raises(DBAPIError) as fallo:
            async with conexion.begin_nested():
                await conexion.execute(text(sql), {"a": ana, "b": beto})
        assert "permission denied" in str(fallo.value).lower()


@pytest.mark.asyncio
async def test_la_migracion_solo_abre_la_escritura_al_dueno(mundo):
    conexion, _, _, _ = mundo
    await conexion.execute(text("RESET ROLE"))
    filas = (await conexion.execute(text(
        "SELECT p.polname, c.relname, p.polcmd, "
        "ARRAY(SELECT CASE WHEN r=0 THEN 'public' ELSE pg_get_userbyid(r) END FROM unnest(p.polroles) r) AS roles, "
        "pg_get_userbyid(c.relowner) AS dueno "
        "FROM pg_policy p JOIN pg_class c ON c.oid=p.polrelid "
        "WHERE c.relname IN ('biblioteca_capacidades','biblioteca_auditoria_capacidades')"))).all()
    nuevas = {f.polname: f for f in filas if "propietario" in f.polname}
    assert set(nuevas) == {"bib_cap_propietario_lectura", "bib_cap_propietario_alta", "bib_cap_propietario_cambio",
                           "bib_audcap_propietario_lectura", "bib_audcap_propietario_alta"}
    for f in nuevas.values():
        assert list(f.roles) == [f.dueno], f.polname
    assert all(f.polcmd != "d" for f in filas), "ninguna política de DELETE"
    assert all("lopdp_app" not in f.roles for f in filas)
    privilegios = (await conexion.execute(text(
        "SELECT privilege_type FROM information_schema.role_table_grants "
        "WHERE grantee='lopdp_app' AND table_name='biblioteca_capacidades'"))).scalars().all()
    assert set(privilegios) == {"SELECT"}
