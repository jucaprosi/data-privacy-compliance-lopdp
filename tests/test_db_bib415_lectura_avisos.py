# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤arbitro ¤seguridad
"""BIB-415: lectura de la biblioteca para la sincronización de avisos.

Corre contra el PostgreSQL de pruebas (`db_engine`: el PG16 del arnés o evydentia-pruebas, nunca producción),
dentro de una transacción que se deshace. Las filas se siembran con los disparadores apagados
(`session_replication_role = replica`); la lectura se hace como `lopdp_app` y con `app.current_user_id` de una
persona sin capacidades. Cada mutación m1 a m3 de la especificación §5 reescribe la función dentro de la
transacción y comprueba que la guardia da rojo.
"""
import importlib.util
import uuid
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.pasillo import biblioteca as pasillo

RAIZ = Path(__file__).resolve().parents[1]
_ruta = RAIZ / "alembic" / "versions" / "20261126_bib415_lectura_avisos.py"
_spec = importlib.util.spec_from_file_location("_bib415_lectura_avisos", _ruta)
MIG = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(MIG)

CAMPOS = {"id", "codigo", "titulo", "redactada_por", "origen_ia", "id_resolucion", "creada_en"}
PROHIBIDOS = {"cuerpo_md", "cuerpo", "texto", "motivo", "concedida_por", "motivo_revocacion", "revocada_por"}
_TODO = "SELECT * FROM biblioteca_versiones_en_revision()"


def _id(prefijo: str) -> str:
    return f"{prefijo}-{uuid.uuid4().hex[:10]}"


async def _usuario(s: AsyncSession) -> str:
    uid = _id("u")
    await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:i, :e, 'Persona ficticia')"),
                    {"i": uid, "e": f"{uid}@prueba.invalid"})
    return uid


async def _version(s: AsyncSession, codigo: str, version: str, estado: str, autor: str) -> str:
    vid = str(uuid.uuid4())
    await s.execute(text(
        "INSERT INTO biblioteca_versiones (id, codigo, version, formato, cuerpo_md, responsable_id, autores, "
        "estado, motivo) VALUES (:i, :c, :v, 'MD', '# Cuerpo ficticio', :u, CAST(:a AS jsonb), :e, 'Motivo ficticio')"),
        {"i": vid, "c": codigo, "v": version, "u": autor, "a": f'["{autor}"]', "e": estado})
    return vid


async def _capacidad(s: AsyncSession, usuario: str, otorgante: str, revocada: bool) -> None:
    if revocada:
        await s.execute(text(
            "INSERT INTO biblioteca_capacidades (usuario_id, capacidad, concedida_por, motivo, revocada_en, "
            "revocada_por, motivo_revocacion) VALUES (:u, 'revisor_tecnico', :o, 'Motivo ficticio', now(), :o, "
            "'Revocación ficticia')"), {"u": usuario, "o": otorgante})
    else:
        await s.execute(text(
            "INSERT INTO biblioteca_capacidades (usuario_id, capacidad, concedida_por, motivo) "
            "VALUES (:u, 'revisor_tecnico', :o, 'Motivo ficticio')"), {"u": usuario, "o": otorgante})


@pytest_asyncio.fixture
async def mundo(db_engine):
    async with AsyncSession(db_engine, expire_on_commit=False) as s:
        await s.begin()
        try:
            await s.execute(text("SET LOCAL session_replication_role = replica"))
            autor, otorgante, sin_capacidades = await _usuario(s), await _usuario(s), await _usuario(s)
            vigente, revocado = await _usuario(s), await _usuario(s)
            codigo = f"BIB-T{uuid.uuid4().hex[:6].upper()}"
            await s.execute(text("INSERT INTO biblioteca_catalogo (codigo, nombre) VALUES (:c, 'Plantilla ficticia')"),
                            {"c": codigo})
            en_revision = await _version(s, codigo, "0.2.0", "en_revision", autor)
            publicada = await _version(s, codigo, "0.1.0", "publicada", autor)
            await _capacidad(s, vigente, otorgante, False)
            await _capacidad(s, revocado, otorgante, True)
            await s.execute(text("SET LOCAL session_replication_role = origin"))
            yield {"s": s, "en_revision": en_revision, "publicada": publicada, "vigente": vigente,
                   "revocado": revocado, "sin_capacidades": sin_capacidades}
        finally:
            await s.rollback()


async def _como_app(m) -> None:
    await m["s"].execute(text("SET LOCAL ROLE lopdp_app"))
    await m["s"].execute(text("SELECT set_config('app.current_user_id', :u, true)"), {"u": m["sin_capacidades"]})


async def _mutar_versiones(m, sql: str) -> None:
    await m["s"].execute(text("DROP FUNCTION IF EXISTS biblioteca_versiones_en_revision()"))
    await m["s"].execute(text(sql))
    await m["s"].execute(text(MIG.PERMISOS))


# --- Guardias ---

async def guardia_versiones(m, lectura=None) -> list[str]:
    await _como_app(m)
    if lectura is None:
        filas = await pasillo.versiones_en_revision(m["s"])
    else:
        filas = [dict(f) for f in (await m["s"].execute(text(lectura))).mappings().all()]
    mias = [f for f in filas if f["id"] in {m["en_revision"], m["publicada"]}]
    fallos = []
    if [f["id"] for f in mias] != [m["en_revision"]]:
        fallos.append("no se ve solo la versión en_revision")
    if any(set(f) & PROHIBIDOS or set(f) - CAMPOS for f in filas):
        fallos.append("la salida trae campos fuera de R1")
    if mias and mias[0]["titulo"] != "Plantilla ficticia":
        fallos.append("la versión no trae el título de su plantilla")
    return fallos


async def guardia_revisores(m) -> list[str]:
    await _como_app(m)
    ids = set(await pasillo.revisores_tecnicos(m["s"]))
    fallos = []
    if m["vigente"] not in ids:
        fallos.append("falta el revisor vigente")
    if m["revocado"] in ids:
        fallos.append("aparece el revisor revocado")
    return fallos


# --- R1 y R2 con base ---

@pytest.mark.asyncio
async def test_db_sin_capacidades_ve_solo_la_version_en_revision(mundo):
    assert await guardia_versiones(mundo) == []


@pytest.mark.asyncio
async def test_db_m1_security_invoker_da_rojo(mundo):
    await _mutar_versiones(mundo, MIG.VERSIONES_EN_REVISION.replace("SECURITY DEFINER", "SECURITY INVOKER"))
    assert "no se ve solo la versión en_revision" in await guardia_versiones(mundo)


@pytest.mark.asyncio
async def test_db_m3_devolver_el_motivo_da_rojo(mundo):
    mutada = (MIG.VERSIONES_EN_REVISION
              .replace("creada_en timestamptz)", "creada_en timestamptz, motivo text)")
              .replace("v.id_resolucion, v.creada_en", "v.id_resolucion, v.creada_en, v.motivo"))
    assert "motivo text" in mutada and "v.motivo" in mutada
    await _mutar_versiones(mundo, mutada)
    assert "la salida trae campos fuera de R1" in await guardia_versiones(mundo, _TODO)


@pytest.mark.asyncio
async def test_db_la_funcion_original_no_trae_campos_fuera_de_r1(mundo):
    assert await guardia_versiones(mundo, _TODO) == []


@pytest.mark.asyncio
async def test_db_solo_el_revisor_vigente(mundo):
    assert await guardia_revisores(mundo) == []


@pytest.mark.asyncio
async def test_db_m2_incluir_la_revocada_da_rojo(mundo):
    await mundo["s"].execute(text(MIG.REVISORES_TECNICOS.replace(" AND k.revocada_en IS NULL", "")))
    assert "aparece el revisor revocado" in await guardia_revisores(mundo)


@pytest.mark.asyncio
async def test_db_las_funciones_son_estables_definer_y_solo_las_ejecuta_lopdp_app(mundo):
    filas = (await mundo["s"].execute(text(
        "SELECT p.proname, p.provolatile, p.prosecdef, array_to_string(p.proconfig, ';') AS config, "
        "has_function_privilege('public', p.oid, 'EXECUTE') AS publico, "
        "has_function_privilege('lopdp_app', p.oid, 'EXECUTE') AS app "
        "FROM pg_proc p WHERE p.proname IN ('biblioteca_versiones_en_revision', 'biblioteca_revisores_tecnicos')"
    ))).mappings().all()
    assert len(filas) == 2
    for f in filas:
        assert f["provolatile"] == "s" and f["prosecdef"] is True
        assert "search_path=pg_catalog, public" in f["config"]
        assert f["app"] is True and f["publico"] is False


# --- Sin base ---

def test_la_migracion_solo_lee_y_cuelga_de_bib406():
    assert MIG.revision == "20261126_bib415_lectura_avisos"
    assert MIG.down_revision == "20261125_bib406_propuestas_ia" and MIG.branch_labels is None
    for sql in (MIG.VERSIONES_EN_REVISION, MIG.REVISORES_TECNICOS):
        assert "STABLE SECURITY DEFINER SET search_path = pg_catalog, public" in sql
        cuerpo = sql.split("$$")[1].upper()
        assert not any(p in cuerpo for p in ("INSERT", "UPDATE", "DELETE")), "R2: solo leen"
    assert "cuerpo_md" not in MIG.VERSIONES_EN_REVISION and "motivo" not in MIG.VERSIONES_EN_REVISION
    assert "concedida_por" not in MIG.REVISORES_TECNICOS
    assert "TO lopdp_app" in MIG.PERMISOS and "FROM PUBLIC" in MIG.PERMISOS


def test_el_pasillo_expone_las_dos_lecturas():
    assert callable(pasillo.versiones_en_revision) and callable(pasillo.revisores_tecnicos)
