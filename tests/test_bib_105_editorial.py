# ¤adpa
# ¤¤developer-architect
"""Árbitro BIB-105: reglas puras y persistencia real opt-in en Neon propio.

Sin TEST_DATABASE_URL solo se ejecutan reglas/contratos; los skips no acreditan RLS.
No aplica migraciones automáticamente ni crea asignaciones reales: datos sintéticos rollback.
"""
import base64
import importlib.util
import io
import os
from pathlib import Path
from uuid import uuid4
import zipfile
import pytest
import pytest_asyncio
from alembic.config import Config
from alembic.script import ScriptDirectory
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from api.errores import ErrorNegocio
from features.biblioteca import biblioteca_service as bib

ROOT = Path(__file__).resolve().parents[1]
FICHA = {"nombre": "Maestro sintético", "objetivo": "Probar administración", "fuentes": "Fuente de prueba",
         "fecha_revision": "2026-10-25", "instrucciones": "Revisar antes de usar", "dependencias": "Ninguna",
         "restricciones": "Solo pruebas"}


# ¤adpa
def archivo(formato="DOCX"):
    contenido = io.BytesIO()
    with zipfile.ZipFile(contenido, "w") as z:
        raiz = "word/document.xml" if formato == "DOCX" else "xl/workbook.xml"
        mime = ("application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
                if formato == "DOCX" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml")
        namespace = ("http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                     if formato == "DOCX" else "http://schemas.openxmlformats.org/spreadsheetml/2006/main")
        etiqueta = "document" if formato == "DOCX" else "workbook"
        z.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   f'<Override PartName="/{raiz}" ContentType="{mime}"/></Types>')
        z.writestr(raiz, f'<{etiqueta} xmlns="{namespace}"/>')
    return bib.ArchivoMaestro(nombre="prueba." + formato.lower(),
        contenido_base64=base64.b64encode(contenido.getvalue()).decode(), generacion=1)


# ¤adpa
def xlsx_con_tipos(tipos: str):
    """XLSX mínimo cuyo [Content_Types].xml se fija a mano."""
    contenido = io.BytesIO()
    with zipfile.ZipFile(contenido, "w") as z:
        z.writestr("[Content_Types].xml",
                   f'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">{tipos}</Types>')
        z.writestr("xl/workbook.xml", '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"/>')
    return bib.ArchivoMaestro(nombre="prueba.xlsx",
        contenido_base64=base64.b64encode(contenido.getvalue()).decode(), generacion=1)


MIME_WORKBOOK = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"


# ¤adpa
def version_pura(**cambios):
    return {"estado": "en_revision", "sha256": "a" * 64, "responsable_id": "editor",
            "autores": ["editor"], "ficha": FICHA, "generacion": 3, **cambios}


# ¤adpa
def revisiones_puras():
    return [{"tipo": tipo, "aprobado": True, "generacion": 3, "revisor_id": revisor}
            for tipo, revisor in [("tecnica", "tecnico"), ("juridica", "juridico")]]


# ¤adpa
@pytest.mark.parametrize("faltante", ["tecnica", "juridica"])
def test_publicacion_incompleta_exige_revision(faltante):
    revisiones = [r for r in revisiones_puras() if r["tipo"] != faltante]
    with pytest.raises(ErrorNegocio, match="revisión") as exc:
        bib.exigir_publicable(version_pura(), revisiones, "publicador")
    assert exc.value.code == "BIB_REVISION_PENDIENTE"


# ¤adpa
def test_publicacion_completa_explicita():
    bib.exigir_publicable(version_pura(), revisiones_puras(), "publicador")


# ¤adpa
@pytest.mark.parametrize("cambio", [{"generacion": 2}, {"aprobado": False}, {"revisor_id": "editor"}])
def test_dictamen_obsoleto_rechazado_o_propio_no_cuenta(cambio):
    revisiones = revisiones_puras()
    revisiones[0].update(cambio)
    with pytest.raises(ErrorNegocio):
        bib.exigir_publicable(version_pura(), revisiones, "publicador")


# ¤adpa
@pytest.mark.parametrize("actor", ["editor", "coautor"])
def test_cuatro_ojos_para_todos_los_autores(actor):
    with pytest.raises(ErrorNegocio) as exc:
        bib.exigir_publicable(version_pura(autores=["editor", "coautor"]), revisiones_puras(), actor)
    assert exc.value.code == "BIB_AUTOR_NO_INDEPENDIENTE"


# ¤adpa
@pytest.mark.parametrize("cambio", [{"sha256": None}, {"ficha": None}, {"responsable_id": None}])
def test_publicacion_sin_insumos_denegada(cambio):
    with pytest.raises(ErrorNegocio) as exc:
        bib.exigir_publicable(version_pura(**cambio), revisiones_puras(), "publicador")
    assert exc.value.code == "BIB_PUBLICACION_INCOMPLETA"


# ¤adpa
@pytest.mark.parametrize("estado", ["publicada", "retirada", "sustituida"])
def test_estado_cerrado_no_se_republica(estado):
    with pytest.raises(ErrorNegocio):
        bib.exigir_publicable(version_pura(estado=estado), revisiones_puras(), "publicador")


# ¤adpa
def test_xlsx_con_tipo_raiz_por_default_aceptado():
    # OPC (ECMA-376-2): sin Override, el tipo de la parte sale del Default de su extensión.
    bib.validar_archivo(xlsx_con_tipos(f'<Default Extension="xml" ContentType="{MIME_WORKBOOK}"/>'), "XLSX")


# ¤adpa
def test_xlsx_override_raiz_con_otro_tipo_rechazado_aunque_haya_default():
    tipos = (f'<Default Extension="xml" ContentType="{MIME_WORKBOOK}"/>'
             '<Override PartName="/xl/workbook.xml" ContentType="application/xml"/>')
    with pytest.raises(ErrorNegocio) as exc:
        bib.validar_archivo(xlsx_con_tipos(tipos), "XLSX")
    assert exc.value.code == "BIB_ARCHIVO_INVALIDO"


KIT = ROOT / "data/biblioteca/kit_v1"
# Solo los maestros declarados en el manifiesto: ignora restos locales (p. ej. bloqueos «~$» de Word).
MAESTROS = sorted((linea.split()[1], linea.split()[0])
                  for linea in (KIT / "MANIFIESTO.sha256").read_text(encoding="utf-8").splitlines()
                  if linea.strip() and linea.split()[1].startswith("plantillas/v0.1/"))


# ¤adpa
def test_manifiesto_declara_los_ocho_maestros():
    assert len(MAESTROS) == 8


# ¤adpa
@pytest.mark.parametrize("relativa,huella", MAESTROS, ids=[m[0].rsplit("/", 1)[-1] for m in MAESTROS])
def test_maestros_reales_del_kit_pasan_validacion(relativa, huella):
    ruta = KIT / relativa
    maestro = bib.ArchivoMaestro(nombre=ruta.name, contenido_base64=base64.b64encode(ruta.read_bytes()).decode(),
                                 generacion=1)
    datos, checksum = bib.validar_archivo(maestro, ruta.suffix[1:].upper())
    assert datos == ruta.read_bytes() and checksum == huella


# ¤adpa
@pytest.mark.parametrize("sustituye", [None, "otra-version"])
def test_sustitucion_exigida_si_ya_hay_publicada(sustituye):
    with pytest.raises(ErrorNegocio) as exc:
        bib.exigir_sustitucion("publicada-vigente", sustituye)
    assert exc.value.code == "BIB_SUSTITUCION_REQUERIDA"


# ¤adpa
@pytest.mark.parametrize("publicada,sustituye", [(None, None), ("publicada-vigente", "publicada-vigente")])
def test_sustitucion_valida_o_primera_publicacion(publicada, sustituye):
    bib.exigir_sustitucion(publicada, sustituye)


# ¤adpa
@pytest.mark.parametrize("formato", ["DOCX", "XLSX"])
def test_archivo_comprobado_con_integridad(formato):
    datos, sha = bib.validar_archivo(archivo(formato), formato)
    import hashlib
    assert sha == hashlib.sha256(datos).hexdigest()


# ¤adpa
@pytest.mark.parametrize("contenido", ["????", base64.b64encode(b"archivo falso").decode()])
def test_archivo_falso_no_aceptado(contenido):
    entrada = archivo().model_copy(update={"contenido_base64": contenido})
    with pytest.raises(ErrorNegocio):
        bib.validar_archivo(entrada, "DOCX")


# ¤adpa
def test_macros_no_aceptadas():
    datos = io.BytesIO(base64.b64decode(archivo().contenido_base64))
    with zipfile.ZipFile(datos, "a") as z:
        z.writestr("word/vbaProject.bin", b"macro")
    entrada = archivo().model_copy(update={"contenido_base64": base64.b64encode(datos.getvalue()).decode()})
    with pytest.raises(ErrorNegocio):
        bib.validar_archivo(entrada, "DOCX")


# ¤adpa
def test_cliente_no_puede_declarar_estado_ni_capacidades():
    for campo in ("estado", "capacidades", "responsable_id", "tenant_id"):
        with pytest.raises(ValidationError):
            bib.CrearVersion(codigo="TEST-01", version="1.0", formato="DOCX", **{campo: "publicada"})


def test_contrato_privado_no_admite_objeto_de_otro_tenant():
    with pytest.raises(ValidationError):
        bib.RevisionDocumento(tenant_id="empresa-a", documento_id="documento", revision_id="revision",
            autor_id="autor", creada_en="2026-10-25T12:00:00Z", objeto=bib.ObjetoDocumento(
                tenant_id="empresa-b", objeto_id="objeto", sha256="a"*64, bytes=10, estado_analisis="limpio"))


def test_xml_ooxml_falso_denegado():
    datos = io.BytesIO()
    with zipfile.ZipFile(datos, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml", "<falso/>")
    with pytest.raises(ErrorNegocio):
        bib.validar_archivo(archivo().model_copy(update={"contenido_base64": base64.b64encode(datos.getvalue()).decode()}), "DOCX")


@pytest.mark.asyncio
async def test_autorizacion_sin_asignaciones_no_infiere_privilegios():
    class Resultado:
        def scalars(self):
            return []
    class Sesion:
        def __init__(self):
            self.actores = []
        async def execute(self, consulta, parametros):
            self.actores.append(parametros["actor"])
            return Resultado()
    sesion = Sesion()
    with pytest.raises(ErrorNegocio) as exc:
        await bib.listar(sesion, "administrador-sin-capacidad")
    assert exc.value.code == "BIB_SIN_CAPACIDAD"
    assert sesion.actores == ["administrador-sin-capacidad"] * 2


# ¤adpa
def test_ficha_vacia_no_publicable():
    with pytest.raises(ValidationError):
        bib.Ficha(**{**FICHA, "nombre": "   "})


# ¤adpa
def test_compuerta_reserva_22_secciones():
    contenido = (ROOT / "features/biblioteca/biblioteca_service.py").read_text()
    for tarea in [101,102,103,104,106,107,108,*range(201,209),*range(301,308)]:
        assert contenido.count(f"# === BIB-{tarea} ===") == 1
        assert contenido.count(f"# === fin BIB-{tarea} ===") == 1


# ¤adpa
def test_migracion_base_unica_sin_asignaciones():
    ruta = ROOT / "alembic/versions/20261025_biblioteca_base.py"
    spec = importlib.util.spec_from_file_location("bib_migracion", ruta)
    migracion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migracion)
    assert len(migracion.revision) <= 32
    # Sin fijar el padre literal ni exigir que sea la última (CAPA-01 se encadena después): la
    # historia es lineal, con una sola cabeza, y Biblioteca está en ella colgando de una revisión existente.
    configuracion = Config(str(ROOT / "alembic.ini"))
    configuracion.set_main_option("script_location", str(ROOT / "alembic"))
    guion = ScriptDirectory.from_config(configuracion)
    cabezas = guion.get_heads()
    assert len(cabezas) == 1
    assert migracion.revision in {r.revision for r in guion.iterate_revisions(cabezas[0], "base")}
    assert isinstance(migracion.down_revision, str)
    assert guion.get_revision(migracion.down_revision) is not None
    assert len(guion.get_revision(migracion.revision).nextrev) <= 1
    sql = []
    class Operaciones:
        def execute(self, consulta): sql.append(consulta)
    migracion.op = Operaciones()
    migracion.upgrade()
    texto = "\n".join(sql)
    assert "INSERT INTO biblioteca_capacidades" not in texto
    assert texto.count("FORCE ROW LEVEL SECURITY") == 6
    assert "GRANT UPDATE ON biblioteca_versiones" in texto
    assert "GRANT UPDATE ON biblioteca_capacidades" not in texto
    assert "editorial_global" in texto
    assert "tenant_id" not in texto


# ¤adpa
def test_migracion_audita_capacidades_con_search_path_fijo():
    texto = (ROOT / "alembic/versions/20261025_biblioteca_base.py").read_text(encoding="utf-8")
    funcion = texto.split("CREATE FUNCTION biblioteca_auditar_capacidad()")[1].split("$$;")[0]
    assert "SECURITY DEFINER SET search_path=pg_catalog,public" in funcion
    assert "AFTER INSERT OR UPDATE OR DELETE ON biblioteca_capacidades" in texto
    assert "GRANT INSERT ON biblioteca_auditoria_capacidades" not in texto


# ¤adpa
@pytest_asyncio.fixture
async def db_bib():
    url = os.environ.get("TEST_DATABASE_URL", "")
    if "ep-late-hall-b50bpbk5" in url.lower():
        pytest.fail("Host de producción prohibido; no se abrió conexión", pytrace=False)
    if not url or os.environ.get("BIB105_RAMA_PROPIA") != "1":
        pytest.skip("Persistencia/RLS pendientes: falta rama Neon propia (TEST_DATABASE_URL y BIB105_RAMA_PROPIA=1)")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_async_engine(url, echo=False, hide_parameters=True)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            existe = (await conexion.execute(text("SELECT to_regclass('public.biblioteca_versiones')"))).scalar()
            if not existe:
                pytest.fail("Aplicar migración BIB-105 solo en la rama propia antes de este árbitro", pytrace=False)
            ids = {rol: "bib-test-" + uuid4().hex for rol in ("editor", "tecnico", "juridico", "publicador", "sin_permiso")}
            for rol, usuario in ids.items():
                await conexion.execute(text("INSERT INTO users(id,email,nombre) VALUES (:id,:email,:nombre)"),
                    {"id": usuario, "email": usuario + "@example.test", "nombre": rol})
            for rol, capacidad in [("editor","editor"),("tecnico","revisor_tecnico"),
                                   ("juridico","revisor_juridico"),("publicador","publicador")]:
                await conexion.execute(text("INSERT INTO biblioteca_capacidades(usuario_id,capacidad,concedida_por,motivo) "
                    "VALUES (:id,:cap,:id,'Fixture sintética rollback')"), {"id": ids[rol], "cap": capacidad})
            await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
            async with AsyncSession(bind=conexion, expire_on_commit=False, join_transaction_mode="create_savepoint") as sesion:
                yield sesion, ids
        except DBAPIError:
            pytest.fail("Fallo DB BIB-105 (detalles de conexión omitidos); comprobar migración y permisos de rama", pytrace=False)
        finally:
            await transaccion.rollback()
    await engine.dispose()


# ¤adpa
async def crear_db(sesion, ids):
    v = await bib.crear(sesion, ids["editor"], bib.CrearVersion(
        codigo="TEST-" + uuid4().hex[:10].upper(), version="1.0", formato="DOCX", ficha=bib.Ficha(**FICHA)))
    return await bib.cargar(sesion, ids["editor"], v["id"], archivo().model_copy(update={"generacion": v["generacion"]}))


# ¤adpa
async def aprobar_db(sesion, ids, v):
    for rol, tipo in [("tecnico","tecnica"),("juridico","juridica")]:
        await bib.revisar(sesion, ids[rol], v["id"], bib.Dictamen(
            tipo=tipo, aprobado=True, comentario="Dictamen sintético", generacion=v["generacion"]))


# ¤adpa
@pytest.mark.asyncio
async def test_db_sin_asignacion_denegado_incluso_cabecera_admin(db_bib):
    sesion, ids = db_bib
    await sesion.execute(text("SELECT set_config('app.current_user_id',:id,true)"), {"id": ids["editor"]})
    # La identidad verificada reemplaza el contexto previo, sin inferir roles de empresa/plataforma.
    with pytest.raises(ErrorNegocio) as exc:
        await bib.listar(sesion, ids["sin_permiso"])
    assert exc.value.code == "BIB_SIN_CAPACIDAD"
    assert (await sesion.execute(text("SELECT count(*) FROM biblioteca_versiones"))).scalar() == 0
    assert not (await sesion.execute(text("SELECT has_table_privilege('lopdp_app','biblioteca_capacidades','INSERT')"))).scalar()


# ¤adpa
@pytest.mark.asyncio
async def test_db_revisiones_obligatorias_y_publicacion_auditada(db_bib):
    sesion, ids = db_bib
    v = await crear_db(sesion, ids)
    decision = bib.Transicion(generacion=v["generacion"], motivo="Prueba sintética")
    with pytest.raises(ErrorNegocio) as exc:
        await bib.publicar(sesion, ids["publicador"], v["id"], decision)
    assert exc.value.code == "BIB_REVISION_PENDIENTE"
    with pytest.raises(DBAPIError):
        async with sesion.begin_nested():
            await sesion.execute(text("UPDATE biblioteca_versiones SET estado='publicada',motivo='salto' WHERE id=:id"), {"id": v["id"]})
    await aprobar_db(sesion, ids, v)
    publicada = await bib.publicar(sesion, ids["publicador"], v["id"], decision)
    assert publicada["estado"] == "publicada"
    eventos = await bib.historial(sesion, ids["publicador"], v["id"])
    assert any(e["accion"] == "publicada" and e["actor_id"] == ids["publicador"]
               and e["alcance"] == "editorial_global" for e in eventos)


# ¤adpa
@pytest.mark.asyncio
async def test_db_editar_invalida_dictamen_y_no_borra_historial(db_bib):
    sesion, ids = db_bib
    v = await crear_db(sesion, ids)
    await aprobar_db(sesion, ids, v)
    cambiada = await bib.editar(sesion, ids["editor"], v["id"], bib.EditarFicha(
        ficha=bib.Ficha(**{**FICHA,"objetivo":"Objetivo nuevo"}), generacion=v["generacion"]))
    with pytest.raises(ErrorNegocio) as exc:
        await bib.publicar(sesion, ids["publicador"], v["id"], bib.Transicion(generacion=cambiada["generacion"], motivo="Prueba"))
    assert exc.value.code == "BIB_REVISION_PENDIENTE"
    assert (await sesion.execute(text("SELECT count(*) FROM biblioteca_revisiones WHERE version_id=:id"), {"id": v["id"]})).scalar() == 2


# ¤adpa
@pytest.mark.asyncio
async def test_db_inmutabilidad_retiro_sucesora_y_archivo_conservado(db_bib):
    sesion, ids = db_bib
    v = await crear_db(sesion, ids)
    await aprobar_db(sesion, ids, v)
    await bib.publicar(sesion, ids["publicador"], v["id"], bib.Transicion(generacion=v["generacion"], motivo="Publicar prueba"))
    with pytest.raises(ErrorNegocio) as exc:
        await bib.cargar(sesion, ids["editor"], v["id"], archivo().model_copy(update={"generacion":v["generacion"]}))
    assert exc.value.code == "BIB_VERSION_INMUTABLE"
    sucesora = await bib.crear(sesion, ids["editor"], bib.CrearVersion(codigo=v["codigo"], version="2.0",
        formato="DOCX", ficha=bib.Ficha(**FICHA), sustituye_id=v["id"]))
    sucesora = await bib.cargar(sesion, ids["editor"], sucesora["id"], archivo())
    await aprobar_db(sesion, ids, sucesora)
    await bib.publicar(sesion, ids["publicador"], sucesora["id"], bib.Transicion(generacion=sucesora["generacion"], motivo="Sustituir prueba"))
    vieja = (await sesion.execute(text("SELECT estado,sha256,archivo FROM biblioteca_versiones WHERE id=:id"), {"id":v["id"]})).mappings().one()
    assert vieja["estado"] == "sustituida" and vieja["sha256"] == v["sha256"] and vieja["archivo"]
    retirada = await bib.retirar(sesion, ids["publicador"], sucesora["id"], bib.Transicion(generacion=sucesora["generacion"], motivo="Retirar prueba"))
    assert retirada["estado"] == "retirada"


# ¤adpa
@pytest.mark.asyncio
async def test_db_una_sola_publicada_por_codigo(db_bib):
    sesion, ids = db_bib
    v1 = await crear_db(sesion, ids)
    # Paralela creada antes de que exista publicada: no declara sustitución.
    v2 = await bib.crear(sesion, ids["editor"], bib.CrearVersion(codigo=v1["codigo"], version="2.0",
        formato="DOCX", ficha=bib.Ficha(**FICHA)))
    v2 = await bib.cargar(sesion, ids["editor"], v2["id"], archivo())
    await aprobar_db(sesion, ids, v1)
    await aprobar_db(sesion, ids, v2)
    await bib.publicar(sesion, ids["publicador"], v1["id"], bib.Transicion(generacion=v1["generacion"], motivo="Publicar 1.0"))
    with pytest.raises(ErrorNegocio) as exc:
        await bib.crear(sesion, ids["editor"], bib.CrearVersion(codigo=v1["codigo"], version="3.0", formato="DOCX"))
    assert exc.value.code == "BIB_SUSTITUCION_REQUERIDA"
    with pytest.raises(ErrorNegocio) as exc:
        await bib.publicar(sesion, ids["publicador"], v2["id"], bib.Transicion(generacion=v2["generacion"], motivo="Publicar 2.0"))
    assert exc.value.code == "BIB_SUSTITUCION_REQUERIDA"
    # Sin la comprobación Python, la base sigue impidiendo la segunda publicada.
    with pytest.raises(DBAPIError):
        async with sesion.begin_nested():
            await sesion.execute(text("UPDATE biblioteca_versiones SET estado='publicada',motivo='salto' WHERE id=:id"), {"id": v2["id"]})
    publicadas = (await sesion.execute(text(
        "SELECT count(*) FROM biblioteca_versiones WHERE codigo=:codigo AND estado='publicada'"
    ), {"codigo": v1["codigo"]})).scalar()
    assert publicadas == 1


# ¤adpa
@pytest.mark.asyncio
async def test_db_capacidades_auditadas_e_inalterables(db_bib):
    sesion, ids = db_bib
    usuario, actor = ids["sin_permiso"], ids["publicador"]
    # Las capacidades solo las cambia el propietario; la auditoría debe registrarlo igualmente.
    await sesion.execute(text("RESET ROLE"))
    await sesion.execute(text("INSERT INTO biblioteca_capacidades(usuario_id,capacidad,concedida_por,motivo) "
        "VALUES (:u,'editor',:a,'Alta sintética')"), {"u": usuario, "a": actor})
    await sesion.execute(text("UPDATE biblioteca_capacidades SET revocada_en=now(),revocada_por=:a,"
        "motivo_revocacion='Revocación sintética' WHERE usuario_id=:u"), {"u": usuario, "a": actor})
    await sesion.execute(text("UPDATE biblioteca_capacidades SET revocada_en=NULL,revocada_por=NULL,"
        "motivo_revocacion=NULL,concedida_por=:a,motivo='Reactivación sintética' WHERE usuario_id=:u"), {"u": usuario, "a": actor})
    await sesion.execute(text("DELETE FROM biblioteca_capacidades WHERE usuario_id=:u"), {"u": usuario})
    await sesion.execute(text("SET LOCAL ROLE lopdp_app"))
    await sesion.execute(text("SELECT set_config('app.current_user_id',:id,true)"), {"id": actor})
    eventos = (await sesion.execute(text(
        "SELECT accion, actor_id, capacidad, motivo FROM biblioteca_auditoria_capacidades "
        "WHERE usuario_id=:u ORDER BY id"), {"u": usuario})).all()
    assert [tuple(e) for e in eventos] == [
        ("alta", actor, "editor", "Alta sintética"),
        ("revocacion", actor, "editor", "Revocación sintética"),
        ("reactivacion", actor, "editor", "Reactivación sintética"),
        ("baja", None, "editor", None)]
    for sql in ("INSERT INTO biblioteca_auditoria_capacidades(usuario_id,capacidad,accion,actor_id) "
                "VALUES (:u,'editor','alta',:u)",
                "UPDATE biblioteca_auditoria_capacidades SET motivo='falso' WHERE usuario_id=:u",
                "DELETE FROM biblioteca_auditoria_capacidades WHERE usuario_id=:u"):
        with pytest.raises(DBAPIError):
            async with sesion.begin_nested():
                await sesion.execute(text(sql), {"u": usuario})


# ¤adpa
@pytest.mark.asyncio
async def test_db_duplicados_y_concurrencia(db_bib):
    sesion, ids = db_bib
    v = await crear_db(sesion, ids)
    with pytest.raises(ErrorNegocio):
        await bib.crear(sesion, ids["editor"], bib.CrearVersion(codigo=v["codigo"], version="1.0", formato="DOCX"))
    with pytest.raises(ErrorNegocio) as exc:
        await bib.editar(sesion, ids["editor"], v["id"], bib.EditarFicha(ficha=bib.Ficha(**FICHA), generacion=1))
    assert exc.value.code == "BIB_CONFLICTO_VERSION"


# ¤adpa
@pytest.mark.asyncio
async def test_db_v01_creada_siempre_en_revision(db_bib):
    sesion, ids = db_bib
    v = await bib.crear(sesion, ids["editor"], bib.CrearVersion(codigo="TEST-"+uuid4().hex[:10].upper(), version="0.1", formato="DOCX"))
    assert v["estado"] == "en_revision"


@pytest.mark.asyncio
async def test_db_cuatro_ojos_aunque_el_editor_tenga_otras_capacidades(db_bib):
    sesion, ids = db_bib
    v = await crear_db(sesion, ids)
    # Simula doble asignación autorizada por propietario; el usuario sigue sin poder autoaprobar.
    await sesion.execute(text("RESET ROLE"))
    for cap in ("revisor_tecnico", "publicador"):
        await sesion.execute(text("INSERT INTO biblioteca_capacidades(usuario_id,capacidad,concedida_por,motivo) "
            "VALUES (:id,:cap,:id,'Fixture SoD rollback')"), {"id":ids["editor"],"cap":cap})
    await sesion.execute(text("SET LOCAL ROLE lopdp_app"))
    with pytest.raises(ErrorNegocio) as exc:
        await bib.revisar(sesion, ids["editor"], v["id"], bib.Dictamen(tipo="tecnica", aprobado=True,
            comentario="Auto revisión", generacion=v["generacion"]))
    assert exc.value.code == "BIB_AUTOR_NO_INDEPENDIENTE"
    with pytest.raises(ErrorNegocio) as exc:
        await bib.publicar(sesion, ids["editor"], v["id"], bib.Transicion(generacion=v["generacion"], motivo="Auto publicación"))
    assert exc.value.code == "BIB_AUTOR_NO_INDEPENDIENTE"


@pytest.mark.asyncio
async def test_db_version_publicada_no_admite_sql_directo_ni_borrar_auditoria(db_bib):
    sesion, ids = db_bib
    v = await crear_db(sesion, ids)
    await aprobar_db(sesion, ids, v)
    await bib.publicar(sesion, ids["publicador"], v["id"], bib.Transicion(generacion=v["generacion"], motivo="Prueba de inmutabilidad"))
    await bib.listar(sesion, ids["editor"])
    for sql in ("UPDATE biblioteca_versiones SET ficha='{}' WHERE id=:id",
                "DELETE FROM biblioteca_versiones WHERE id=:id",
                "DELETE FROM biblioteca_auditoria WHERE version_id=:id"):
        with pytest.raises(DBAPIError):
            async with sesion.begin_nested():
                await sesion.execute(text(sql), {"id":v["id"]})


@pytest.mark.asyncio
async def test_api_real_identidad_verificada_ignora_usuario_y_rol_de_cabeceras(db_bib, monkeypatch):
    from types import SimpleNamespace
    from fastapi import FastAPI, HTTPException
    from httpx import ASGITransport, AsyncClient
    from api import rbac
    from api.errores import error_negocio_handler
    from api.routers.biblioteca_editorial import router
    from app_core.db.session import get_session
    sesion, ids = db_bib
    monkeypatch.setenv("AUTH_MODE", "oidc")
    async def identidad(_sesion, authorization):
        if authorization != "Bearer credencial-sintetica-de-prueba":
            raise HTTPException(401, "Identidad no verificada")
        return SimpleNamespace(usuario_id=ids["sin_permiso"])
    monkeypatch.setattr(rbac, "usuario_verificado", identidad)
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.add_exception_handler(ErrorNegocio, error_negocio_handler)
    async def usar_sesion():
        yield sesion
    app.dependency_overrides[get_session] = usar_sesion
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://prueba") as cliente:
        respuesta = await cliente.post("/api/v1/biblioteca/editorial/versiones",
            headers={"Authorization":"Bearer credencial-sintetica-de-prueba", "X-User-ID":ids["editor"],
                     "X-Role":"admin_organizacion"},
            json={"codigo":"TEST-HTTP", "version":"1.0", "formato":"DOCX"})
        assert respuesta.status_code == 403
        assert respuesta.json()["code"] == "BIB_SIN_CAPACIDAD"
        sin_credencial = await cliente.get("/api/v1/biblioteca/editorial", headers={"X-User-ID":ids["editor"]})
        assert sin_credencial.status_code == 401
