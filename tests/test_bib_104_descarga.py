# ¤adpa ¤rbac-tenant ¤arbitro
# ¤¤qa-engineer
"""Árbitro BIB-104: descarga controlada de plantillas Word/Excel.

Reglas puras, contratos, rutas y migración siempre. La persistencia y la RLS con `lopdp_app`
corren contra el arnés local (ARNES_BASE=postgresql_local) o una rama propia con
BIB104_RAMA_PROPIA=1; sin ellas se omiten y no se acreditan. Todo ocurre en una transacción
que se revierte, con datos sintéticos.

Mutación decisiva (BIB-104.md): permitir la descarga de una versión retirada (modificando la
comprobación en features/biblioteca/services/descarga.py) debe hacer fallar la prueba de
retirada y permisos: `test_descarga_version_retirada_denegada`.
"""
import io
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4
import jwt
import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from api.errores import ErrorNegocio
from app_core.errors import CATALOGO_ERRORES
from features.biblioteca import biblioteca_service as bib
from features.biblioteca.services import archivos as servicio_archivos
from features.biblioteca.services import descarga as servicio_descarga
from main import app

ROOT = Path(__file__).resolve().parents[1]
MIGRACION = next((ROOT / "alembic/versions").glob("*_biblioteca_descargas.py"), None)
PRODUCCION, COMPARTIDA = "ep-late-hall-b50bpbk5", "ep-soft-darkness-b5z454vp"


# ---------------------------------------------------------------------------- reglas puras (sin BD)

# ¤adpa
def test_formatos_y_tipos_mime_permitidos():
    assert servicio_archivos.tipo_mime("DOCX") == (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert servicio_archivos.tipo_mime("XLSX") == (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert servicio_archivos.tipo_mime(" docx ") == (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    for invalido in ("PDF", "MD", "TXT", "EXE", ""):
        with pytest.raises(ErrorNegocio) as exc:
            servicio_archivos.tipo_mime(invalido)
        assert exc.value.code == "BIB_PLANTILLA_NO_DESCARGABLE"


# ¤adpa
def test_nombre_descarga_incluye_codigo_version_y_extension():
    assert servicio_archivos.nombre_descarga("BIB-001", "1.0.0", "DOCX") == "BIB-001_v1.0.0.docx"
    assert servicio_archivos.nombre_descarga("BIB-002", "2.1", "XLSX") == "BIB-002_v2.1.xlsx"
    assert (
        servicio_archivos.nombre_descarga("BIB-001", "1.0.0", "DOCX", "politica privacidad.docx")
        == "BIB-001_v1.0.0_politica_privacidad.docx"
    )
    with pytest.raises(ErrorNegocio):
        servicio_archivos.nombre_descarga("BIB-001", "1.0.0", "PDF")


# ¤adpa
def test_tokens_temporales_firmados_vigencia_y_manipulacion():
    tenant = "org-1"
    usuario = "user-1"
    plantilla = "plan-1"
    version = "1.0.0"

    token = servicio_archivos.generar_token_descarga(
        tenant_id=tenant, usuario_id=usuario, plantilla_id=plantilla, version=version, expira_segundos=60
    )
    datos = servicio_archivos.verificar_token_descarga(token)
    assert datos["tid"] == tenant
    assert datos["sub"] == usuario
    assert datos["pid"] == plantilla
    assert datos["ver"] == version
    assert datos["aud"] == "biblioteca_descargas"

    # Token caducado
    token_expirado = servicio_archivos.generar_token_descarga(
        tenant_id=tenant, usuario_id=usuario, plantilla_id=plantilla, version=version, expira_segundos=-10
    )
    with pytest.raises(ErrorNegocio) as exc_exp:
        servicio_archivos.verificar_token_descarga(token_expirado)
    assert exc_exp.value.code == "BIB_TOKEN_DESCARGA_INVALIDO"

    # Token alterado
    with pytest.raises(ErrorNegocio) as exc_alt:
        servicio_archivos.verificar_token_descarga(token + "corrupto")
    assert exc_alt.value.code == "BIB_TOKEN_DESCARGA_INVALIDO"


# ¤adpa
def test_cabeceras_descarga_segura():
    cabeceras = servicio_archivos.cabeceras_descarga(
        nombre_archivo="BIB-001_v1.0.docx",
        tamano=1024,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    assert 'attachment; filename="BIB-001_v1.0.docx"' in cabeceras["Content-Disposition"]
    assert cabeceras["Content-Length"] == "1024"
    assert cabeceras["X-Content-Type-Options"] == "nosniff"
    assert "no-store" in cabeceras["Cache-Control"]


# ¤adpa
def test_contrato_objeto_archivo_maestro_para_analisis():
    objeto = bib.ObjetoArchivoMaestro(
        plantilla_id="p-1",
        codigo="BIB-001",
        version="1.0.0",
        formato="DOCX",
        nombre_archivo="BIB-001_v1.0.0.docx",
        sha256="a" * 64,
        tamano_bytes=2048,
        estado_analisis="limpio",
    )
    assert objeto.plantilla_id == "p-1"
    assert objeto.formato == "DOCX"
    assert objeto.estado_analisis == "limpio"


# ¤adpa
def test_compuerta_expone_lo_de_bib_104_y_catalogo_registra_errores():
    for nombre in (
        "EnlaceDescarga",
        "ObjetoArchivoMaestro",
        "cabeceras_descarga",
        "ejecutar_descarga",
        "generar_enlace_descarga",
        "generar_token_descarga",
        "nombre_descarga",
        "registrar_auditoria_descarga",
        "tipo_mime",
        "verificar_token_descarga",
    ):
        assert nombre in bib.__all__ and hasattr(bib, nombre)

    for codigo in (
        "BIB_DESCARGA_DENEGADA",
        "BIB_PLANTILLA_NO_DESCARGABLE",
        "BIB_ARCHIVO_NO_DISPONIBLE",
        "BIB_TOKEN_DESCARGA_INVALIDO",
    ):
        assert codigo in CATALOGO_ERRORES
        assert CATALOGO_ERRORES[codigo].codigo == codigo


# ¤adpa
def test_secciones_de_la_ficha_una_vez_y_archivos_dentro_del_tope():
    for relativa in ("features/biblioteca/biblioteca_service.py", "features/biblioteca/domain/errores.py"):
        texto = (ROOT / relativa).read_text(encoding="utf-8")
        assert texto.count("# === BIB-104 ===") == 1 and texto.count("# === fin BIB-104 ===") == 1

    vistas_ts = (ROOT / "frontend/src/components/biblioteca/vistas/index.ts").read_text(encoding="utf-8")
    assert vistas_ts.count("// === BIB-104 ===") == 1 and vistas_ts.count("// === fin BIB-104 ===") == 1

    for relativa in (
        "features/biblioteca/services/archivos.py",
        "features/biblioteca/services/descarga.py",
        "api/routers/biblioteca_descargas.py",
    ):
        lineas = (ROOT / relativa).read_text(encoding="utf-8").splitlines()
        assert len(lineas) <= 500, f"{relativa} supera 500 líneas: {len(lineas)}"


# ¤adpa
def test_rutas_router_descargas():
    from api.routers import biblioteca_descargas as router
    assert router.AUTO_REGISTRO is True
    rutas = [(sorted(r.methods)[0], r.path) for r in router.router.routes]
    base_descargar = "/biblioteca/plantillas/{plantilla_id}/descargar"
    base_archivo = "/biblioteca/descargas/{plantilla_id}/archivo"

    assert ("POST", base_descargar) in rutas
    assert ("GET", base_descargar) in rutas
    assert ("GET", base_archivo) in rutas

    publicadas = app.openapi()["paths"]
    assert "/api/v1" + base_descargar in publicadas
    assert "/api/v1" + base_archivo in publicadas


# ¤adpa
def test_migracion_una_cabeza_rls_forzada_y_permisos_minimos():
    import importlib.util
    assert MIGRACION is not None, "falta alembic/versions/*_biblioteca_descargas.py"
    spec = importlib.util.spec_from_file_location("bib104_migracion", MIGRACION)
    migracion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migracion)
    assert len(migracion.revision) <= 32

    configuracion = Config(str(ROOT / "alembic.ini"))
    configuracion.set_main_option("script_location", str(ROOT / "alembic"))
    guion = ScriptDirectory.from_config(configuracion)
    cabezas = guion.get_heads()
    assert len(cabezas) == 1
    assert migracion.revision in {r.revision for r in guion.iterate_revisions(cabezas[0], "base")}
    assert guion.get_revision(migracion.down_revision) is not None

    sql = []
    class Operaciones:
        def execute(self, consulta):
            sql.append(consulta)
    migracion.op = Operaciones()
    migracion.upgrade()
    texto = "\n".join(sql)

    assert "CREATE TABLE biblioteca_descargas" in texto
    assert "ALTER TABLE biblioteca_descargas ENABLE ROW LEVEL SECURITY" in texto
    assert "ALTER TABLE biblioteca_descargas FORCE ROW LEVEL SECURITY" in texto
    assert "CREATE POLICY tenant_isolation_biblioteca_descargas ON biblioteca_descargas" in texto
    assert "USING (tenant_id::text = current_setting('app.current_tenant_id', true))" in texto
    assert "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true)" in texto
    assert "GRANT SELECT, INSERT ON biblioteca_descargas TO lopdp_app" in texto
    assert "DELETE" not in texto.replace("BEFORE UPDATE OR DELETE", "")
    assert "GRANT ALL" not in texto


# ¤adpa
def test_descarga_version_retirada_denegada():
    """Mutación decisiva: descargar una versión retirada o no publicada debe denegarse."""
    version_retirada = {
        "id": "v-retirada",
        "codigo": "BIB-001",
        "version": "1.0.0",
        "formato": "DOCX",
        "estado": "retirada",
        "nombre_archivo": "test.docx",
        "sha256": "a" * 64,
        "archivo": b"PK\x03\x04...",
    }
    with pytest.raises(ErrorNegocio) as exc:
        servicio_descarga._validar_descargable(version_retirada)
    assert exc.value.code == "BIB_DESCARGA_DENEGADA"

    version_en_revision = dict(version_retirada, estado="en_revision")
    with pytest.raises(ErrorNegocio) as exc2:
        servicio_descarga._validar_descargable(version_en_revision)
    assert exc2.value.code == "BIB_DESCARGA_DENEGADA"

    version_publicada = dict(version_retirada, estado="publicada")
    # No lanza excepción si es publicada
    servicio_descarga._validar_descargable(version_publicada)


# --------------------------------------------------------------------------- persistencia (arnés local)

# ¤adpa
def _url_de_pruebas() -> str:
    url = os.environ.get("TEST_DATABASE_URL", "")
    if PRODUCCION in url.lower():
        pytest.fail("Host de producción prohibido; no se abrió conexión", pytrace=False)
    if not url or not (os.environ.get("ARNES_BASE") == "postgresql_local" or os.environ.get("BIB104_RAMA_PROPIA") == "1"):
        pytest.skip("Persistencia/RLS no acreditadas: falta el arnés local o rama propia (BIB104_RAMA_PROPIA=1)")
    if COMPARTIDA in url.lower():
        pytest.fail("La rama test compartida no es una rama propia; no se abrió conexión", pytrace=False)
    return url.replace("postgresql://", "postgresql+psycopg://", 1) if url.startswith("postgresql://") else url


# ¤adpa ¤rbac-tenant
@pytest.mark.asyncio
async def test_db_aislamiento_rls_auditoria_descargas():
    url = _url_de_pruebas()
    engine = create_async_engine(url, echo=False, hide_parameters=True)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            # Fixture sintética
            u1, u2 = f"u1-{uuid4().hex[:8]}", f"u2-{uuid4().hex[:8]}"
            t1, t2 = f"t1-{uuid4().hex[:8]}", f"t2-{uuid4().hex[:8]}"
            p_id = str(uuid4())

            await conexion.execute(text("INSERT INTO users(id, email, nombre) VALUES (:id, :e, 'Test')"),
                                   [{"id": u1, "e": f"{u1}@test.com"}, {"id": u2, "e": f"{u2}@test.com"}])
            await conexion.execute(text("INSERT INTO tenants(id, nombre_comercial, razon_social, ruc_identificacion) "
                                        "VALUES (:id, 'Org', 'Org SA', :ruc)"),
                                   [{"id": t1, "ruc": f"179{uuid4().int % 10**10:010d}"}, {"id": t2, "ruc": f"179{uuid4().int % 10**10:010d}"}])
            await conexion.execute(text("INSERT INTO user_tenant_roles(id, user_id, tenant_id, role) "
                                        "VALUES (:id, :u, :t, 'implementador')"),
                                   [{"id": str(uuid4()), "u": u1, "t": t1}, {"id": str(uuid4()), "u": u2, "t": t2}])

            # La descarga referencia una versión real: se crea aquí (dentro de la transacción que se revierte).
            await conexion.execute(text("SELECT set_config('app.current_user_id', :u, true)"), {"u": u1})
            await conexion.execute(text(
                "INSERT INTO biblioteca_capacidades(usuario_id,capacidad,concedida_por,motivo) "
                "VALUES (:u,'editor',:u,'prueba')"), {"u": u1})
            codigo = f"TEST-{uuid4().hex[:8].upper()}"
            await conexion.execute(text("INSERT INTO biblioteca_catalogo(codigo) VALUES (:c)"), {"c": codigo})
            await conexion.execute(text(
                "INSERT INTO biblioteca_versiones(id,codigo,version,formato,responsable_id,autores) "
                "VALUES (:id,:c,'1.0.0','DOCX',:u,CAST(:a AS jsonb))"),
                {"id": p_id, "c": codigo, "u": u1, "a": f'["{u1}"]'})
            await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
            async with AsyncSession(bind=conexion, expire_on_commit=False, join_transaction_mode="create_savepoint") as sesion:
                # Fijar tenant 1
                await sesion.execute(text("SELECT set_config('app.current_tenant_id', :t, true), "
                                          "set_config('app.current_user_id', :u, true)"), {"t": t1, "u": u1})
                await servicio_descarga.registrar_auditoria_descarga(sesion, t1, u1, p_id, "1.0.0")

                # Comprobar que en tenant 1 se lee
                filas_t1 = (await sesion.execute(text("SELECT id, tenant_id FROM biblioteca_descargas"))).fetchall()
                assert len(filas_t1) == 1 and filas_t1[0][1] == t1

                # Fijar tenant 2: no debe ver el registro de tenant 1
                await sesion.execute(text("SELECT set_config('app.current_tenant_id', :t, true), "
                                          "set_config('app.current_user_id', :u, true)"), {"t": t2, "u": u2})
                filas_t2 = (await sesion.execute(text("SELECT id, tenant_id FROM biblioteca_descargas"))).fetchall()
                assert len(filas_t2) == 0
        finally:
            await transaccion.rollback()
    await engine.dispose()
