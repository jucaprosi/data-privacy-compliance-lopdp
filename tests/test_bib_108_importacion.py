# ¤adpa
# ¤¤developer-architect
"""Árbitro BIB-108: manifiesto reproducible, verificación sin escritura e importación idempotente.

Las pruebas DB son opt-in en la rama Neon propia (TEST_DATABASE_URL y BIB108_RAMA_PROPIA=1);
los skips no acreditan persistencia ni RLS. Datos sintéticos con rollback.
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from uuid import uuid4
import pytest
import pytest_asyncio
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from api.errores import ErrorNegocio
from features.biblioteca import biblioteca_service as bib

ROOT = Path(__file__).resolve().parents[1]
OCHO = {"INV-01", "INV-02", "RAT-01", "LEG-01", "PLA-01", "EIPD-00", "AVI-01", "PRO-01"}


# ¤adpa
@pytest.fixture
def kit(tmp_path):
    """Copia aislada del kit y del manifiesto para alterarlos sin tocar los originales."""
    shutil.copytree(ROOT / "data/biblioteca/kit_v1", tmp_path / "data/biblioteca/kit_v1")
    shutil.copy(ROOT / "data/biblioteca/manifiesto_inicial.json", tmp_path / "data/biblioteca/manifiesto_inicial.json")
    return tmp_path


# ¤adpa
def test_manifiesto_versionado_es_reproducible_desde_el_kit():
    assert bib.cargar_manifiesto(ROOT) == bib.construir_manifiesto(ROOT)


# ¤adpa
def test_cincuenta_codigos_conservados_y_repartidos():
    manifiesto = bib.cargar_manifiesto(ROOT)
    especificacion = json.loads((ROOT / "data/biblioteca/kit_v1/especificacion/especificacion_biblioteca.json").read_text())
    codigos = [e["codigo"] for e in manifiesto["entradas"]]
    assert sorted(codigos) == sorted(t["codigo"] for t in especificacion["templates"])
    assert len(set(codigos)) == 50
    por = {d: {e["codigo"] for e in manifiesto["entradas"] if e["disponibilidad"] == d}
           for d in ("con_archivo", "salida_por_mapear", "planificada")}
    assert por["con_archivo"] == OCHO
    assert por["salida_por_mapear"] == {"DIA-01", "DIA-02"}
    assert len(por["planificada"]) == 40
    assert all(e["version"] == "0.1" for e in manifiesto["entradas"])


# ¤adpa
def test_rutas_heredadas_resueltas_sin_tocar_originales():
    for entrada in bib.cargar_manifiesto(ROOT)["entradas"]:
        if entrada["archivo"]:
            assert entrada["archivo"]["ruta_kit"].startswith("02_Plantillas/")
            assert entrada["archivo"]["ruta"].startswith("data/biblioteca/kit_v1/plantillas/v0.1/")
            assert (ROOT / entrada["archivo"]["ruta"]).is_file()
    with pytest.raises(ErrorNegocio):
        from features.biblioteca.services.importacion import resolver_ruta
        resolver_ruta("../fuera/INV-01.xlsx")


# ¤adpa
def test_manifiesto_sin_secretos_ni_datos_de_clientes():
    contenido = (ROOT / "data/biblioteca/manifiesto_inicial.json").read_text()
    assert not re.search(r"postgres(ql)?://|@[a-z0-9-]+\.[a-z]{2,}|neon\.tech|api[_-]?key|secret", contenido, re.I)
    assert "tenant_id" not in contenido and "organization_id\":" not in contenido


# ¤adpa
def test_verificacion_sin_escritura_del_kit_real():
    """Aceptación: los ocho maestros abren, con checksum, tipo y tamaño."""
    informe = bib.verificar_manifiesto(bib.cargar_manifiesto(ROOT), ROOT)
    assert informe["errores"] == []
    assert {a["codigo"] for a in informe["archivos"]} == OCHO
    assert all(a["apertura"] == "ok" and a["tamano"] > 0 and len(a["sha256"]) == 64 for a in informe["archivos"])
    assert [(d["codigo"], d["version"], d["apertura"]) for d in informe["derivados"]] == [("EIPD-00", "0.2", "ok")]


# ¤adpa
def test_eipd00_v02_aparte_sin_tocar_manifiesto_del_kit():
    """Opción B: la v0.2 aprobada lleva su huella en el manifiesto inicial, no en MANIFIESTO.sha256."""
    kit_sha = (ROOT / "data/biblioteca/kit_v1/MANIFIESTO.sha256").read_text().splitlines()
    assert len([l for l in kit_sha if l.strip()]) == 15 and not any("v0.2" in l for l in kit_sha)
    derivados = bib.cargar_manifiesto(ROOT)["derivados"]
    assert derivados == [{"codigo": "EIPD-00", "version": "0.2", "clave": "EIPD-00@0.2",
                          "aprobacion": "governance/apoyo/BIBLIOTECA_ESTADO.md §9.4",
                          "archivo": {"ruta": "data/biblioteca/kit_v1/plantillas/v0.2/EIPD-00.docx",
                                      "sha256": "f9f1378f5fcaa434acefbae549cd61ab269615354fbe5b7a499273b9f960a77f"}}]


# ¤adpa
def _variables_docx(ruta):
    with zipfile.ZipFile(ruta) as docx:
        xml = "".join(docx.read(n).decode("utf-8") for n in docx.namelist() if n.startswith("word/") and n.endswith(".xml"))
    return set(re.findall(r"\{\{\s*([A-Z0-9_]+)\s*\}\}", re.sub(r"<[^>]+>", "", xml)))


# ¤adpa
def test_desviaciones_aprobadas_de_eipd00_aplicadas_al_catalogo():
    """§10: fuentes ampliadas y variables de la v0.2 vigente; los demás códigos conservan el kit."""
    entradas = {e["codigo"]: e for e in bib.cargar_manifiesto(ROOT)["entradas"]}
    eipd = entradas["EIPD-00"]
    assert eipd["fuentes"] == "N01;N02;N03;N09;N11"
    assert eipd["metadatos"]["desviaciones"] == "governance/apoyo/BIBLIOTECA_ESTADO.md §10"
    v02 = _variables_docx(ROOT / "data/biblioteca/kit_v1/plantillas/v0.2/EIPD-00.docx")
    assert len(v02) == 52 and set(eipd["metadatos"]["campos_template"]) == v02
    assert not {"CATEGORIAS_ESPECIALES_GRAN_ESCALA", "REQUERIMIENTO_O_NO_IDENTIFICADO", "SI_NO"} & v02
    assert all("desviaciones" not in e["metadatos"] for c, e in entradas.items() if c != "EIPD-00")


# ¤adpa
def test_derivado_alterado_o_sin_aprobacion_se_detecta(kit):
    ruta = kit / "data/biblioteca/kit_v1/plantillas/v0.2/EIPD-00.docx"
    ruta.write_bytes(ruta.read_bytes() + b"\0")
    errores = bib.verificar_manifiesto(bib.cargar_manifiesto(kit), kit)["errores"]
    assert any(e.startswith("EIPD-00 0.2: SHA-256") for e in errores)
    manifiesto = bib.cargar_manifiesto(ROOT)
    manifiesto["derivados"][0]["version"] = "0.3"
    assert any("sin aprobación registrada" in e for e in bib.verificar_manifiesto(manifiesto, ROOT)["errores"])


# ¤adpa
def test_original_alterado_se_detecta(kit):
    ruta = kit / "data/biblioteca/kit_v1/plantillas/v0.1/AVI-01.docx"
    ruta.write_bytes(ruta.read_bytes() + b"\0")
    errores = bib.verificar_manifiesto(bib.cargar_manifiesto(kit), kit)["errores"]
    assert any(e.startswith("AVI-01 0.1: SHA-256") for e in errores)


# ¤adpa
def test_archivo_faltante_se_detecta(kit):
    (kit / "data/biblioteca/kit_v1/plantillas/v0.1/PRO-01.docx").unlink()
    errores = bib.verificar_manifiesto(bib.cargar_manifiesto(kit), kit)["errores"]
    assert any(e.startswith("PRO-01: archivo inexistente") for e in errores)


# ¤adpa
@pytest.mark.parametrize("alteracion", ["quitar", "duplicar", "planificada_con_archivo", "ruta_fuera"])
def test_manifiesto_manipulado_rechazado(kit, alteracion):
    manifiesto = bib.cargar_manifiesto(kit)
    entradas = manifiesto["entradas"]
    if alteracion == "quitar":
        entradas.pop()
    elif alteracion == "duplicar":
        entradas.append(dict(entradas[0]))
    elif alteracion == "planificada_con_archivo":
        planificada = next(e for e in entradas if e["disponibilidad"] == "planificada")
        planificada["archivo"] = dict(next(e for e in entradas if e["archivo"])["archivo"])
    else:
        next(e for e in entradas if e["codigo"] == "AVI-01")["archivo"]["ruta"] = "data/biblioteca/manifiesto_inicial.json"
    assert bib.verificar_manifiesto(manifiesto, kit)["errores"]


# ¤adpa
def test_script_verificar_sin_base_de_datos():
    entorno = {k: v for k, v in os.environ.items() if "DATABASE_URL" not in k}
    salida = subprocess.run([sys.executable, "scripts/importar_catalogo_biblioteca.py", "--verificar"],
                            cwd=ROOT, env=entorno, capture_output=True, text=True, timeout=60)
    assert "50 entradas = 8 con archivo + 2 por mapear + 40 planificadas" in salida.stdout
    assert salida.returncode == 0, salida.stdout + salida.stderr


# ¤adpa
def _script():
    spec = importlib.util.spec_from_file_location("importar_catalogo", ROOT / "scripts/importar_catalogo_biblioteca.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


# ¤adpa
@pytest.mark.parametrize("url, args", [
    ("", ["--importar", "--actor", "u", "--confirmar-rama-desarrollo"]),
    ("postgresql://x@rama-dev/db", ["--importar", "--actor", "u"]),
    ("postgresql://x@rama-dev/db", ["--importar", "--confirmar-rama-desarrollo"]),
    ("postgresql://x@ep-late-hall-b50bpbk5.neon/db", ["--importar", "--actor", "u", "--confirmar-rama-desarrollo"]),
])
def test_script_importar_exige_rama_de_desarrollo_explicita(monkeypatch, capsys, url, args):
    monkeypatch.setenv("BIB108_DATABASE_URL", url)
    assert _script().main(args) == 2
    assert url[:12] not in capsys.readouterr().out or not url


# ¤adpa
def test_migracion_catalogo_encadenada_y_minima():
    ruta = ROOT / "alembic/versions/20261026_biblioteca_catalogo.py"
    spec = importlib.util.spec_from_file_location("bib108_migracion", ruta)
    migracion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migracion)
    assert len(migracion.revision) <= 32
    # Sin exigir que sea la última (INC-01 y otras se encadenan después, como en BIB-105): la
    # historia es lineal, con una sola cabeza, y el catálogo está en ella colgando de una revisión
    # existente, con a lo sumo una migración siguiente.
    configuracion = Config(str(ROOT / "alembic.ini"))
    configuracion.set_main_option("script_location", str(ROOT / "alembic"))
    guion = ScriptDirectory.from_config(configuracion)
    cabezas = guion.get_heads()
    assert len(cabezas) == 1, "Debe existir una sola cabeza"
    assert migracion.revision in {r.revision for r in guion.iterate_revisions(cabezas[0], "base")}
    assert isinstance(migracion.down_revision, str)
    assert guion.get_revision(migracion.down_revision) is not None
    assert len(guion.get_revision(migracion.revision).nextrev) <= 1
    texto = ruta.read_text()
    assert "tenant_id" not in texto
    assert "FORCE ROW LEVEL SECURITY" in texto
    assert "GRANT SELECT, INSERT ON biblioteca_importaciones TO lopdp_app" in texto
    assert not re.search(r"GRANT[^;]*(UPDATE|DELETE)[^;]*biblioteca_importaciones", texto)


# --------------------------------------------------------------------------- persistencia opt-in

# ¤adpa
@pytest_asyncio.fixture
async def db_bib():
    url = os.environ.get("TEST_DATABASE_URL", "")
    if "ep-late-hall-b50bpbk5" in url.lower():
        pytest.fail("Host de producción prohibido; no se abrió conexión", pytrace=False)
    if not url or os.environ.get("BIB108_RAMA_PROPIA") != "1":
        pytest.skip("Persistencia pendiente: falta rama Neon propia (TEST_DATABASE_URL y BIB108_RAMA_PROPIA=1)")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_async_engine(url, echo=False, hide_parameters=True)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            if not (await conexion.execute(text("SELECT to_regclass('public.biblioteca_importaciones')"))).scalar():
                pytest.fail("Aplicar migración BIB-108 solo en la rama propia antes de este árbitro", pytrace=False)
            ids = {rol: "bib108-test-" + uuid4().hex for rol in ("editor", "sin_permiso")}
            for rol, usuario in ids.items():
                await conexion.execute(text("INSERT INTO users(id,email,nombre) VALUES (:id,:email,:nombre)"),
                    {"id": usuario, "email": usuario + "@example.test", "nombre": rol})
            await conexion.execute(text("INSERT INTO biblioteca_capacidades(usuario_id,capacidad,concedida_por,motivo) "
                "VALUES (:id,'editor',:id,'Fixture sintética rollback')"), {"id": ids["editor"]})
            await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
            async with AsyncSession(bind=conexion, expire_on_commit=False, join_transaction_mode="create_savepoint") as sesion:
                yield sesion, ids
        except DBAPIError:
            pytest.fail("Fallo DB BIB-108 (detalles de conexión omitidos); comprobar migración y permisos", pytrace=False)
        finally:
            await transaccion.rollback()
    await engine.dispose()


# ¤adpa
async def _conteos(sesion, clave):
    return {
        "catalogo": (await sesion.execute(text("SELECT count(*) FROM biblioteca_catalogo"))).scalar(),
        "versiones": (await sesion.execute(text("SELECT count(*) FROM biblioteca_versiones"))).scalar(),
        "importaciones": (await sesion.execute(text(
            "SELECT count(*) FROM biblioteca_importaciones WHERE clave=:k"), {"k": clave})).scalar(),
    }


# ¤adpa
@pytest.mark.asyncio
async def test_db_importa_cincuenta_y_ocho_en_revision(db_bib):
    sesion, ids = db_bib
    clave = "prueba-" + uuid4().hex[:12]
    await bib.importar(sesion, ids["editor"], bib.cargar_manifiesto(ROOT), ROOT, clave)
    filas = (await sesion.execute(text(
        "SELECT disponibilidad, count(*) FROM biblioteca_catalogo c JOIN biblioteca_importaciones i USING (codigo) "
        "WHERE i.clave=:k GROUP BY disponibilidad"), {"k": clave})).all()
    assert dict(filas) == {"con_archivo": 8, "salida_por_mapear": 2, "planificada": 40}
    versiones = (await sesion.execute(text(
        "SELECT v.codigo, v.estado, v.sha256, i.sha256 AS importado, i.apertura FROM biblioteca_importaciones i "
        "JOIN biblioteca_versiones v ON v.id=i.version_id WHERE i.clave=:k"), {"k": clave})).mappings().all()
    assert {v["codigo"] for v in versiones} == OCHO
    assert all(v["estado"] == "en_revision" and v["sha256"] == v["importado"] and v["apertura"] == "ok" for v in versiones)
    eipd = (await sesion.execute(text(
        "SELECT v.version, v.estado, v.sha256, i.clave FROM biblioteca_versiones v "
        "JOIN biblioteca_importaciones i ON i.version_id=v.id WHERE v.codigo='EIPD-00' ORDER BY v.version"))).all()
    assert [(f.version, f.estado) for f in eipd] == [("0.1", "en_revision"), ("0.2", "en_revision")]
    assert eipd[1].clave == "EIPD-00@0.2" and eipd[1].sha256.startswith("f9f1378f")


# ¤adpa
@pytest.mark.asyncio
async def test_db_segunda_ejecucion_misma_clave_no_duplica(db_bib):
    sesion, ids = db_bib
    clave = "prueba-" + uuid4().hex[:12]
    manifiesto = bib.cargar_manifiesto(ROOT)
    await bib.importar(sesion, ids["editor"], manifiesto, ROOT, clave)
    antes = await _conteos(sesion, clave)
    segunda = await bib.importar(sesion, ids["editor"], manifiesto, ROOT, clave)
    assert segunda == {"clave": clave, "catalogo_creadas": 0, "versiones_creadas": 0, "importaciones_creadas": 0}
    assert await _conteos(sesion, clave) == antes


# ¤adpa
@pytest.mark.asyncio
async def test_db_hash_distinto_es_conflicto_sin_escritura(db_bib):
    sesion, ids = db_bib
    clave = "prueba-" + uuid4().hex[:12]
    await bib.importar(sesion, ids["editor"], bib.cargar_manifiesto(ROOT), ROOT, clave)
    # Otra clave con metadatos distintos para códigos ya importados: conflicto, nunca reemplazo silencioso.
    otra = "prueba-" + uuid4().hex[:12]
    manifiesto = bib.cargar_manifiesto(ROOT)
    antes = await _conteos(sesion, otra)
    from features.biblioteca.services import importacion
    original = importacion._fila_catalogo
    importacion._fila_catalogo = lambda e: {**original(e), "nombre": original(e)["nombre"] + " (otro)"}
    try:
        with pytest.raises(ErrorNegocio) as error:
            async with sesion.begin_nested():
                await bib.importar(sesion, ids["editor"], manifiesto, ROOT, otra)
        assert error.value.code == "BIB_CONFLICTO_VERSION"
    finally:
        importacion._fila_catalogo = original
    assert await _conteos(sesion, otra) == antes


# ¤adpa
@pytest.mark.asyncio
async def test_db_sin_capacidad_editor_denegado(db_bib):
    sesion, ids = db_bib
    with pytest.raises(ErrorNegocio) as error:
        await bib.importar(sesion, ids["sin_permiso"], bib.cargar_manifiesto(ROOT), ROOT, "prueba-" + uuid4().hex[:12])
    assert error.value.code == "BIB_SIN_CAPACIDAD"


# ¤adpa
@pytest.mark.asyncio
async def test_db_registro_de_importacion_append_only(db_bib):
    sesion, ids = db_bib
    clave = "prueba-" + uuid4().hex[:12]
    await bib.importar(sesion, ids["editor"], bib.cargar_manifiesto(ROOT), ROOT, clave)
    for sql in ("UPDATE biblioteca_importaciones SET apertura='ok' WHERE clave=:k",
                "DELETE FROM biblioteca_importaciones WHERE clave=:k"):
        with pytest.raises(DBAPIError):
            async with sesion.begin_nested():
                await sesion.execute(text(sql), {"k": clave})
