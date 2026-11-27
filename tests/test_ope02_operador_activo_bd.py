# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤arbitro ¤seguridad
"""OPE-02: la plataforma expone en la base si alguien es operador activo.

Las pruebas `test_db_*` corren contra el PostgreSQL de pruebas (`db_engine`: el PG16 del arnés o evydentia-pruebas,
nunca producción), dentro de una transacción que se deshace; las filas se siembran con los disparadores apagados.
Las pruebas sin base leen la migración. Mutaciones de la especificación §5:
  - m1: ignorar `activo` -> test_db_m1_ignorar_activo_da_rojo.
  - m2: declararla `SECURITY INVOKER` -> test_db_m2_security_invoker_da_rojo.
  - m3: dejar `EXECUTE` a `PUBLIC` -> test_db_m3_execute_a_public_da_rojo.
"""
import importlib.util
import uuid
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

RAIZ = Path(__file__).resolve().parents[1]
_ruta = RAIZ / "alembic" / "versions" / "20261126_ope02_operador_activo_bd.py"
_spec = importlib.util.spec_from_file_location("_ope02_operador_activo_bd", _ruta)
MIG = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(MIG)

LLAMADA = "SELECT plataforma_operador_activo(:u)"


def _id(prefijo: str) -> str:
    return f"{prefijo}-{uuid.uuid4().hex[:10]}"


async def _usuario(s: AsyncSession) -> str:
    uid = _id("u")
    await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:i, :e, 'Persona ficticia')"),
                    {"i": uid, "e": f"{uid}@prueba.invalid"})
    return uid


async def _operador(s: AsyncSession, usuario: str, activo: bool) -> None:
    oid = _id("op")
    await s.execute(text(
        "INSERT INTO operadores_plataforma (id, email, nombre, activo, usuario_id) "
        "VALUES (:i, :e, 'Operador ficticio', :a, :u)"),
        {"i": oid, "e": f"{oid}@prueba.invalid", "a": activo, "u": usuario})


@pytest_asyncio.fixture
async def mundo(db_engine):
    async with AsyncSession(db_engine, expire_on_commit=False) as s:
        await s.begin()
        try:
            await s.execute(text("SET LOCAL session_replication_role = replica"))
            activo, de_baja, ajeno = await _usuario(s), await _usuario(s), await _usuario(s)
            await _operador(s, activo, True)
            await _operador(s, de_baja, False)
            await s.execute(text("SET LOCAL session_replication_role = origin"))
            yield {"s": s, "activo": activo, "de_baja": de_baja, "ajeno": ajeno}
        finally:
            await s.rollback()


async def _respuesta(m, usuario) -> object:
    return (await m["s"].execute(text(LLAMADA), {"u": usuario})).scalar()


async def _como_app(m) -> None:
    await m["s"].execute(text("SET LOCAL ROLE lopdp_app"))


async def _reemplazar(m, sql: str) -> None:
    await m["s"].execute(text("DROP FUNCTION IF EXISTS plataforma_operador_activo(varchar)"))
    await m["s"].execute(text(sql))
    await m["s"].execute(text(MIG.PERMISOS))


async def guardia_respuestas(m) -> list[str]:
    fallos = []
    if await _respuesta(m, m["activo"]) is not True:
        fallos.append("el operador activo no da verdadero")
    if await _respuesta(m, m["de_baja"]) is not False:
        fallos.append("el operador dado de baja no da falso")
    if await _respuesta(m, m["ajeno"]) is not False:
        fallos.append("quien no es operador no da falso")
    if await _respuesta(m, None) is not False:
        fallos.append("NULL no da falso")
    return fallos


# --- Con base ---

@pytest.mark.asyncio
async def test_db_verdadero_falso_falso_y_null_falso(mundo):
    assert await guardia_respuestas(mundo) == []


@pytest.mark.asyncio
async def test_db_m1_ignorar_activo_da_rojo(mundo):
    await _reemplazar(mundo, MIG.FUNCION.replace(" AND o.activo", ""))
    assert "el operador dado de baja no da falso" in await guardia_respuestas(mundo)


@pytest.mark.asyncio
async def test_db_lopdp_app_sin_privilegios_sobre_la_tabla_responde_igual(mundo):
    await mundo["s"].execute(text("REVOKE ALL ON operadores_plataforma FROM lopdp_app"))
    await _como_app(mundo)
    assert await guardia_respuestas(mundo) == []


@pytest.mark.asyncio
async def test_db_m2_security_invoker_da_rojo(mundo):
    await _reemplazar(mundo, MIG.FUNCION.replace("SECURITY DEFINER", "SECURITY INVOKER"))
    await mundo["s"].execute(text("REVOKE ALL ON operadores_plataforma FROM lopdp_app"))
    await _como_app(mundo)
    with pytest.raises(Exception, match="permission denied|permiso"):
        await guardia_respuestas(mundo)


async def guardia_catalogo(m) -> list[str]:
    f = (await m["s"].execute(text(
        "SELECT p.provolatile, p.prosecdef, array_to_string(p.proconfig, ';') AS config, "
        "has_function_privilege('public', p.oid, 'EXECUTE') AS publico, "
        "has_function_privilege('lopdp_app', p.oid, 'EXECUTE') AS app, "
        "pg_get_function_result(p.oid) AS devuelve "
        "FROM pg_proc p WHERE p.proname = 'plataforma_operador_activo'"))).mappings().one()
    fallos = []
    if not (f["provolatile"] == "s" and f["prosecdef"] is True and f["devuelve"] == "boolean"):
        fallos.append("no es STABLE SECURITY DEFINER que devuelve boolean")
    if "search_path=pg_catalog, public" not in f["config"]:
        fallos.append("falta el search_path fijo")
    if f["app"] is not True:
        fallos.append("lopdp_app no ejecuta")
    if f["publico"] is not False:
        fallos.append("PUBLIC tiene EXECUTE")
    return fallos


@pytest.mark.asyncio
async def test_db_catalogo_estable_definer_y_solo_lopdp_app_ejecuta(mundo):
    assert await guardia_catalogo(mundo) == []


@pytest.mark.asyncio
async def test_db_m3_execute_a_public_da_rojo(mundo):
    await mundo["s"].execute(text("GRANT EXECUTE ON FUNCTION plataforma_operador_activo(varchar) TO PUBLIC"))
    assert "PUBLIC tiene EXECUTE" in await guardia_catalogo(mundo)


# --- Sin base ---

def test_la_migracion_cuelga_de_ope01_y_deja_una_cabeza_de_plataforma():
    assert MIG.revision == "20261126_ope02_operador_activo_bd"
    assert MIG.down_revision == "20261125_ope01_operador_usuario" and MIG.branch_labels is None
    otras = [p for p in (RAIZ / "alembic" / "versions").glob("*.py")
             if p != _ruta and "down_revision" in p.read_text(encoding="utf-8")
             and '"20261125_ope01_operador_usuario"' in p.read_text(encoding="utf-8").split("down_revision", 1)[1].split("\n", 1)[0]]
    assert otras == [], "otra migración cuelga de la cabeza anterior: plataforma tendría dos cabezas"


def test_la_funcion_es_literal_estable_definer_y_devuelve_un_booleano():
    sql = MIG.FUNCION
    assert "plataforma_operador_activo(usuario_id varchar)" in sql and "RETURNS boolean" in sql
    assert "LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = pg_catalog, public" in sql
    cuerpo = sql.split("$$")[1]
    assert "operadores_plataforma" in cuerpo and "o.activo" in cuerpo and "o.usuario_id" in cuerpo
    assert "o.email" not in cuerpo and "o.nombre" not in cuerpo  # R2: ni email ni nombre
    assert "EXECUTE" not in cuerpo.upper() and "||" not in cuerpo  # SQL literal, sin dinámico
    assert "FROM PUBLIC" in MIG.PERMISOS and "TO lopdp_app" in MIG.PERMISOS
