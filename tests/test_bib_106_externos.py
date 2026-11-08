# ¤adpa ¤rbac-tenant ¤arbitro
# ¤¤qa-engineer
"""Árbitro BIB-106: documentos externos del cliente con análisis y cuarentena.

Reglas puras, migración y rutas siempre. Persistencia y RLS con `lopdp_app` solo contra PostgreSQL 16 local
(ARNES_BASE=postgresql_local y TEST_DATABASE_URL); sin ellas se omiten y no se acreditan. Todo ocurre en una
transacción que se revierte, con datos y archivos sintéticos. El escáner es un doble: no acredita escaneo operativo.

Mutación decisiva (BIB-106.md): en `descargar_carga` (features/biblioteca/services/carga_externa.py) cambiar
`if fila["estado_analisis"] != "limpio":` por `if fila["estado_analisis"] == "infectado":` libera para descarga un
archivo con análisis pendiente o fallido y hace fallar `test_db_cuarentena_pendiente_o_fallido_no_se_descarga`.
"""
import io
import os
import zipfile
from pathlib import Path
from uuid import uuid4
import pytest
import pytest_asyncio
from alembic.config import Config
from alembic.script import ScriptDirectory
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app_core.errors import CATALOGO_ERRORES, ErrorNegocio
from features.biblioteca import biblioteca_service as bib
from features.biblioteca.services import analisis_archivos as analisis
from main import app

ROOT = Path(__file__).resolve().parents[1]
MIGRACION = ROOT / "alembic/versions/20261119_bib106_cargas.py"
PRODUCCION = "ep-late-hall-b50bpbk5"
FICHA = {"nombre": "Plantilla sintética", "objetivo": "Probar", "fuentes": "Fuente de prueba",
         "fecha_revision": "2026-10-28", "instrucciones": "Revisar", "dependencias": "Ninguna",
         "restricciones": "Solo pruebas"}


# ¤adpa
def ooxml(formato: str = "DOCX", *, extra: dict[str, bytes] | None = None, tipos: bytes = b"<Types/>",
          rels: bytes = b"<Relationships/>") -> bytes:
    """Paquete OOXML mínimo sintético; no es un documento real, solo su estructura."""
    principal = "word/document.xml" if formato == "DOCX" else "xl/workbook.xml"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", tipos)
        z.writestr("_rels/.rels", rels)
        z.writestr(principal, b"<x>contenido sintetico</x>")
        for nombre, datos in (extra or {}).items():
            z.writestr(nombre, datos)
    return buffer.getvalue()


# ---------------------------------------------------------------------------- reglas puras (sin BD)

# ¤adpa
def test_ooxml_valido_pasa_y_lo_que_no_es_ooxml_o_del_otro_formato_no():
    analisis.inspeccionar(ooxml("DOCX"), "DOCX")
    analisis.inspeccionar(ooxml("XLSX"), "XLSX")
    for contenido, formato in ((b"%PDF-1.4 falso", "DOCX"), (ooxml("XLSX"), "DOCX"), (b"", "DOCX")):
        with pytest.raises(ErrorNegocio) as exc:
            analisis.inspeccionar(contenido, formato)
        assert exc.value.code in ("BIB_CARGA_FORMATO_INVALIDO", "BIB_CARGA_TAMANO_INVALIDO")
    with pytest.raises(ErrorNegocio):
        analisis.exigir_extension("informe.pdf", "DOCX")
    analisis.exigir_extension("Informe.DOCX", "DOCX")


# ¤adpa
def test_macros_enlaces_externos_y_zip_peligroso_se_rechazan():
    casos = {
        "BIB_CARGA_MACROS": ooxml(extra={"word/vbaProject.bin": b"vba"}),
        "BIB_CARGA_ENLACE_EXTERNO": ooxml(rels=b'<Relationships><Relationship Id="r1" Type="http://x/relationships/'
                                          b'attachedTemplate" Target="https://x.invalid/t.dotm" TargetMode="External"/>'
                                          b'</Relationships>'),
        "BIB_CARGA_ZIP_PELIGROSO": ooxml(extra={"../fuera.xml": b"x"}),
    }
    for codigo, contenido in casos.items():
        with pytest.raises(ErrorNegocio) as exc:
            analisis.inspeccionar(contenido, "DOCX")
        assert exc.value.code == codigo
    bomba = ooxml(extra={"word/relleno.xml": b"0" * (5 * 1024 * 1024)})
    with pytest.raises(ErrorNegocio) as exc:
        analisis.inspeccionar(bomba, "DOCX")
    assert exc.value.code == "BIB_CARGA_ZIP_PELIGROSO"
    hipervinculo = ooxml(rels=b'<Relationships><Relationship Id="r1" Type="http://x/relationships/hyperlink" '
                              b'Target="https://x.invalid" TargetMode="External"/></Relationships>')
    analisis.inspeccionar(hipervinculo, "DOCX")


# ¤adpa
def test_sin_escaner_queda_pendiente_y_un_escaner_que_falla_es_error(monkeypatch):
    monkeypatch.setattr(analisis, "_analizador", None)
    assert analisis.analizar(b"x", "a.docx") == "pendiente"

    class Roto:
        def analizar(self, contenido, nombre):
            raise RuntimeError("caído")
    analisis.registrar_analizador(Roto())
    assert analisis.analizar(b"x", "a.docx") == "error"
    analisis.registrar_analizador(None)


# ¤adpa
def test_contrato_sin_tenant_y_con_limites():
    base = {"titulo": "T", "codigo": "POL-01", "version_propia": "1", "formato": "DOCX",
            "nombre_archivo": "a.docx", "tamano_bytes": 10}
    bib.ReservarCarga(**base)
    for malo in ({"tenant_id": "otra"}, {"tamano_bytes": analisis.TAMANO_MAXIMO + 1}, {"formato": "PDF"},
                 {"codigo": "../x"}):
        with pytest.raises(ValidationError):
            bib.ReservarCarga(**{**base, **malo})


# ¤adpa
def test_compuerta_errores_secciones_y_tope_de_lineas():
    for nombre in ("reservar_carga", "subir_archivo", "finalizar_carga", "descargar_carga", "listar_cargas",
                   "obtener_carga", "registrar_analizador", "Carga", "ReservarCarga"):
        assert nombre in bib.__all__ and hasattr(bib, nombre)
    for codigo in ("BIB_CARGA_NO_ENCONTRADA", "BIB_CARGA_EN_CUARENTENA", "BIB_CARGA_MACROS"):
        assert codigo in CATALOGO_ERRORES
    for relativa in ("features/biblioteca/biblioteca_service.py", "features/biblioteca/domain/errores.py"):
        texto = (ROOT / relativa).read_text(encoding="utf-8")
        assert texto.count("# === BIB-106 ===") == 1 and texto.count("# === fin BIB-106 ===") == 1
    for relativa in ("features/biblioteca/services/carga_externa.py", "features/biblioteca/services/analisis_archivos.py",
                     "api/routers/biblioteca_cargas.py"):
        assert len((ROOT / relativa).read_text(encoding="utf-8").splitlines()) <= 500


# ¤adpa
def test_rutas_publicadas():
    from api.routers import biblioteca_cargas as router
    assert router.AUTO_REGISTRO is True
    rutas = app.openapi()["paths"]
    base = "/api/v1/biblioteca/cargas"
    assert set(rutas[base]) == {"get", "post"}
    assert set(rutas[base + "/{carga_id}/archivo"]) == {"get", "put"}
    assert "post" in rutas[base + "/{carga_id}/finalizar"]


# ¤adpa
def test_migracion_una_cabeza_rls_forzada_y_permisos_minimos():
    import importlib.util
    spec = importlib.util.spec_from_file_location("bib106_migracion", MIGRACION)
    migracion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migracion)
    assert len(migracion.revision) <= 32
    configuracion = Config(str(ROOT / "alembic.ini"))
    configuracion.set_main_option("script_location", str(ROOT / "alembic"))
    guion = ScriptDirectory.from_config(configuracion)
    assert len(guion.get_heads()) == 1
    sql = []

    class Operaciones:
        def execute(self, consulta):
            sql.append(consulta)
    migracion.op = Operaciones()
    migracion.upgrade()
    texto = "\n".join(sql)
    assert "ALTER TABLE biblioteca_cargas ENABLE ROW LEVEL SECURITY" in texto
    assert "ALTER TABLE biblioteca_cargas FORCE ROW LEVEL SECURITY" in texto
    assert "WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))" in texto
    assert "GRANT SELECT, INSERT ON biblioteca_cargas TO lopdp_app" in texto
    assert "GRANT ALL" not in texto and "GRANT DELETE" not in texto


# --------------------------------------------------------------------------- persistencia (PostgreSQL local)

# ¤adpa
def _url() -> str:
    url = os.environ.get("TEST_DATABASE_URL", "")
    if PRODUCCION in url.lower():
        pytest.fail("Host de producción prohibido; no se abrió conexión", pytrace=False)
    if not url or os.environ.get("ARNES_BASE") != "postgresql_local":
        pytest.skip("Persistencia/RLS BIB-106 no acreditadas: falta PostgreSQL local (ARNES_BASE=postgresql_local)")
    return url.replace("postgresql://", "postgresql+psycopg://", 1) if url.startswith("postgresql://") else url


class Escaner:
    def __init__(self):
        self.resultado = "limpio"

    def analizar(self, contenido, nombre):
        return self.resultado


class Mundo:
    def __init__(self, conexion, sesion, ids, ta, tb, maestra_id, escaner):
        self.conexion, self.sesion, self.ids, self.ta, self.tb = conexion, sesion, ids, ta, tb
        self.maestra_id, self.escaner = maestra_id, escaner


# ¤adpa
@pytest_asyncio.fixture
async def mundo():
    engine = create_async_engine(_url(), echo=False, hide_parameters=True)
    escaner = Escaner()
    bib.registrar_analizador(escaner)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            if not (await conexion.execute(text("SELECT to_regclass('public.biblioteca_cargas')"))).scalar():
                pytest.fail("Aplicar la migración de BIB-106 solo en la base local", pytrace=False)
            ids = {rol: "bib106-" + uuid4().hex for rol in
                   ("editor", "tecnico", "juridico", "publicador", "redactor_a", "otro_a", "redactor_b")}
            ta, tb = "bib106-org-" + uuid4().hex, "bib106-org-" + uuid4().hex
            for rol, usuario in ids.items():
                await conexion.execute(text("INSERT INTO users(id,email,nombre) VALUES (:id,:e,:n)"),
                                       {"id": usuario, "e": usuario + "@correo.invalid", "n": rol})
            for tid in (ta, tb):
                await conexion.execute(text(
                    "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                    "VALUES (:id, 'Org sintética', 'Org sintética S.A.', :ruc)"), {"id": tid, "ruc": str(uuid4().int)[:13]})
            for usuario, tid in ((ids["redactor_a"], ta), (ids["otro_a"], ta), (ids["redactor_b"], tb)):
                await conexion.execute(text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) "
                                            "VALUES (:id, :u, :t, 'implementador')"), {"id": str(uuid4()), "u": usuario, "t": tid})
            for rol, capacidad in (("editor", "editor"), ("tecnico", "revisor_tecnico"),
                                   ("juridico", "revisor_juridico"), ("publicador", "publicador")):
                await conexion.execute(text("INSERT INTO biblioteca_capacidades(usuario_id,capacidad,concedida_por,motivo) "
                                            "VALUES (:id,:cap,:id,'Fixture sintética rollback')"), {"id": ids[rol], "cap": capacidad})
            await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
            async with AsyncSession(bind=conexion, expire_on_commit=False, join_transaction_mode="create_savepoint") as sesion:
                await sesion.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": ta})
                version = await bib.crear_version_md(sesion, ids["editor"], "TEST-" + uuid4().hex[:10].upper(), "0.1.0",
                                                     "# Maestra sintética\n")
                version = await bib.editar(sesion, ids["editor"], version["id"], bib.EditarFicha(
                    ficha=bib.Ficha(**FICHA), generacion=version["generacion"]))
                for rol, tipo in (("tecnico", "tecnica"), ("juridico", "juridica")):
                    await bib.revisar(sesion, ids[rol], version["id"], bib.Dictamen(
                        tipo=tipo, aprobado=True, comentario="Dictamen sintético", generacion=version["generacion"]))
                publicada = await bib.publicar(sesion, ids["publicador"], version["id"], bib.Transicion(
                    generacion=version["generacion"], motivo="Publicación sintética"))
                yield Mundo(conexion, sesion, ids, ta, tb, publicada["id"], escaner)
        except DBAPIError:
            pytest.fail("Fallo DB BIB-106 (detalles de conexión omitidos); comprobar migración y permisos", pytrace=False)
        finally:
            bib.registrar_analizador(None)
            await transaccion.rollback()
    await engine.dispose()


# ¤adpa
async def _cargar(m: Mundo, contenido: bytes, *, tenant=None, usuario=None, **extra):
    tenant, usuario = tenant or m.ta, usuario or m.ids["redactor_a"]
    entrada = {"titulo": "Política propia", "codigo": "POL-EXT", "version_propia": "2026.1", "formato": "DOCX",
               "nombre_archivo": "politica.docx", "tamano_bytes": len(contenido), **extra}
    carga = await bib.reservar_carga(m.sesion, tenant, usuario, bib.ReservarCarga(**entrada))
    return await bib.subir_archivo(m.sesion, tenant, usuario, carga.id, contenido)


# ¤adpa
@pytest.mark.asyncio
async def test_db_carga_limpia_queda_borrador_con_procedencia_y_huella_del_servidor(mundo):
    contenido = ooxml()
    carga = await _cargar(mundo, contenido, version_maestra_id=mundo.maestra_id)
    import hashlib
    assert carga.sha256 == hashlib.sha256(contenido).hexdigest() and carga.tamano_bytes == len(contenido)
    assert carga.estado_analisis == "limpio" and carga.descargable and carga.version_maestra.id == mundo.maestra_id
    doc = await bib.finalizar_carga(mundo.sesion, mundo.ta, mundo.ids["redactor_a"], carga.id)
    assert (doc.origen, doc.estado, doc.codigo, doc.nombre) == ("subido", "borrador", "POL-EXT", "Política propia")
    assert "Versión propia: 2026.1" in doc.contenido_markdown and "Origen no vinculado" not in doc.contenido_markdown
    archivo, nombre, _ = await bib.descargar_carga(mundo.sesion, mundo.ta, mundo.ids["otro_a"], carga.id)
    assert archivo == contenido and nombre == "politica.docx"
    with pytest.raises(ErrorNegocio) as exc:
        await bib.finalizar_carga(mundo.sesion, mundo.ta, mundo.ids["redactor_a"], carga.id)
    assert exc.value.code == "BIB_CARGA_ESTADO_INVALIDO"


# ¤adpa
@pytest.mark.asyncio
async def test_db_sin_version_maestra_figura_origen_no_vinculado(mundo):
    carga = await _cargar(mundo, ooxml())
    assert carga.version_maestra is None
    doc = await bib.finalizar_carga(mundo.sesion, mundo.ta, mundo.ids["redactor_a"], carga.id)
    assert "Origen no vinculado" in doc.contenido_markdown
    with pytest.raises(ErrorNegocio) as exc:
        await _cargar(mundo, ooxml(), version_maestra_id="no-existe")
    assert exc.value.code == "BIB_CARGA_VERSION_MAESTRA_INVALIDA"


# ¤adpa
@pytest.mark.asyncio
async def test_db_cuarentena_pendiente_o_fallido_no_se_descarga(mundo):
    for resultado in ("infectado", "error"):
        mundo.escaner.resultado = resultado
        carga = await _cargar(mundo, ooxml())
        assert carga.estado_analisis == resultado and not carga.descargable
        for operacion in (bib.descargar_carga, bib.finalizar_carga):
            with pytest.raises(ErrorNegocio) as exc:
                await operacion(mundo.sesion, mundo.ta, mundo.ids["redactor_a"], carga.id)
            assert exc.value.code in ("BIB_CARGA_EN_CUARENTENA", "BIB_CARGA_ESTADO_INVALIDO")
    bib.registrar_analizador(None)
    carga = await _cargar(mundo, ooxml())
    assert carga.estado_analisis == "pendiente"
    with pytest.raises(ErrorNegocio) as exc:
        await bib.descargar_carga(mundo.sesion, mundo.ta, mundo.ids["redactor_a"], carga.id)
    assert exc.value.code == "BIB_CARGA_EN_CUARENTENA"


# ¤adpa
@pytest.mark.asyncio
async def test_db_tamano_real_distinto_y_archivo_no_se_reemplaza(mundo):
    contenido = ooxml()
    carga = await bib.reservar_carga(mundo.sesion, mundo.ta, mundo.ids["redactor_a"], bib.ReservarCarga(
        titulo="T", codigo="X-1", version_propia="1", formato="DOCX", nombre_archivo="x.docx",
        tamano_bytes=len(contenido) + 1))
    with pytest.raises(ErrorNegocio) as exc:
        await bib.subir_archivo(mundo.sesion, mundo.ta, mundo.ids["redactor_a"], carga.id, contenido)
    assert exc.value.code == "BIB_CARGA_TAMANO_INVALIDO"
    hecha = await _cargar(mundo, contenido)
    with pytest.raises(ErrorNegocio) as exc:
        await bib.subir_archivo(mundo.sesion, mundo.ta, mundo.ids["redactor_a"], hecha.id, ooxml("DOCX", extra={"a": b"b"}))
    assert exc.value.code == "BIB_CARGA_ESTADO_INVALIDO"


# ¤adpa
@pytest.mark.asyncio
async def test_db_nueva_revision_no_sobrescribe_la_anterior(mundo):
    base = ooxml()
    primera = await _cargar(mundo, base)
    doc = await bib.finalizar_carga(mundo.sesion, mundo.ta, mundo.ids["redactor_a"], primera.id)
    otro = ooxml(extra={"word/nota.xml": b"<n/>"})
    segunda = await _cargar(mundo, otro, documento_id=doc.id, version_propia="2026.2")
    doc2 = await bib.finalizar_carga(mundo.sesion, mundo.ta, mundo.ids["redactor_a"], segunda.id)
    assert doc2.id == doc.id and doc2.revision == doc.revision + 1 and "Revisión externa: 2" in doc2.contenido_markdown
    revisiones = await bib.listar_cargas(mundo.sesion, mundo.ta, mundo.ids["otro_a"], doc.id)
    assert [(c.revision_externa, c.version_propia) for c in revisiones] == [(1, "2026.1"), (2, "2026.2")]
    original, _, _ = await bib.descargar_carga(mundo.sesion, mundo.ta, mundo.ids["redactor_a"], primera.id)
    assert original == base


# ¤adpa
@pytest.mark.asyncio
async def test_db_reserva_es_del_usuario_y_otra_organizacion_recibe_404(mundo):
    carga = await bib.reservar_carga(mundo.sesion, mundo.ta, mundo.ids["redactor_a"], bib.ReservarCarga(
        titulo="T", codigo="X-1", version_propia="1", formato="DOCX", nombre_archivo="x.docx", tamano_bytes=10))
    for tenant, usuario in ((mundo.ta, mundo.ids["otro_a"]), (mundo.tb, mundo.ids["redactor_b"])):
        with pytest.raises(ErrorNegocio) as exc:
            await bib.subir_archivo(mundo.sesion, tenant, usuario, carga.id, b"0" * 10)
        assert exc.value.code == "BIB_CARGA_NO_ENCONTRADA"
    limpia = await _cargar(mundo, ooxml())
    await bib.finalizar_carga(mundo.sesion, mundo.ta, mundo.ids["redactor_a"], limpia.id)
    with pytest.raises(ErrorNegocio) as exc:
        await bib.descargar_carga(mundo.sesion, mundo.tb, mundo.ids["redactor_b"], limpia.id)
    assert exc.value.status_code == 404


# ¤adpa
@pytest.mark.asyncio
async def test_db_rls_forzada_aisla_las_cargas(mundo):
    await _cargar(mundo, ooxml())
    sesion = mundo.sesion
    for tenant, esperado in ((mundo.ta, 1), (mundo.tb, 0), ("", 0)):
        await sesion.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant})
        assert (await sesion.execute(text("SELECT count(*) FROM biblioteca_cargas"))).scalar() == esperado
    await sesion.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": mundo.tb})
    with pytest.raises(DBAPIError):
        async with sesion.begin_nested():
            await sesion.execute(text(
                "INSERT INTO biblioteca_cargas(id, tenant_id, usuario_id, titulo, codigo, version_propia, formato, "
                "nombre_archivo, tamano_declarado, expira_en) VALUES (:id, :t, :u, 'T', 'X', '1', 'DOCX', 'x.docx', 1, now())"
            ), {"id": str(uuid4()), "t": mundo.ta, "u": mundo.ids["redactor_a"]})
