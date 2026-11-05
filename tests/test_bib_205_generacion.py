# ¤adpa ¤rbac-tenant ¤arbitro
# ¤¤qa-engineer
"""Árbitro BIB-205: generación de Word y Excel desde una instantánea inmutable.

Reglas puras siempre (determinismo, borrador frente a revisión, salida limpia, DOCX con estilos y tablas,
XLSX con fechas, tablas, validaciones y fórmula autorizada recalculada, texto seguro). La persistencia
(RLS, inmutabilidad, checksum) corre contra la base local del arnés o una rama Neon propia, con la fixture
de BIB-201 (transacción que se revierte).

Mutación decisiva: en `features/biblioteca/services/salida.py:53` (`preparar`, función `marca`), cambiar
el `""` final por `m.group(0)` conserva el token `⟦falta: contexto.notas⟧` en la salida para revisión y
hace fallar ``test_revision_no_exige_el_opcional_ni_la_rama_que_no_aplica`` (BIB_GEN_SALIDA_INVALIDA).
Observado el 2026-11-04 con `python3 -m pytest tests/test_bib_205_generacion.py -q`: 1 fallo, 17 pasan;
restaurado: 18 pasan (3 de base omitidas sin TEST_DATABASE_URL; con el arnés local, 21 pasan).
"""
import io
import re
import zipfile
from datetime import date
from pathlib import Path
import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from openpyxl import load_workbook
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from api.errores import ErrorNegocio
from app_core.errors import CATALOGO_ERRORES
from features.biblioteca import biblioteca_service as bib
from features.biblioteca.domain.plantillas_md import huella
from features.biblioteca.services import generador_docx, generador_xlsx, salida
from features.biblioteca.services.rellenado import datos_del_documento
from tests.test_bib_201_formularios import CAMARAS, FINALIDAD, ORG, db_bib, fuentes, plantilla, publicar  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
MIGRACION = ROOT / "alembic/versions/20261116_biblioteca_generacion.py"
NOTAS = "  - clave: contexto.notas\n    etiqueta: Notas\n    obligatoria: false\n"
CUERPO = (
    "# Política de {{organizacion.razon_social}}\n\n"
    "<!-- instruccion -->Escriba aquí la guía interna.<!-- /instruccion -->\n"
    "<!-- ejemplo -->Ejemplo: cámaras en recepción.<!-- /ejemplo -->\n\n"
    "## Alcance\n\nEmitida el {{fecha_emision}}. Notas: {{contexto.notas}}\n\n"
    "{{#si contexto.camaras}}Zonas: {{contexto.finalidad}}{{#sino}}Sin cámaras en las instalaciones.{{/si}}\n\n"
    "| Dato | Fecha | ¿Activo? |\n|---|---|---|\n"
    "| {{organizacion.ruc}} | {{fecha_emision}} | sí |\n| {{contexto.notas}} | 2026-02-30 | no |\n\n"
    "Aprobado por: {{documento.aprobado_por}}")
TEXTO = plantilla(CUERPO, contexto=CAMARAS + FINALIDAD + NOTAS)
COMPLETO = {"contexto.camaras": "si", "contexto.finalidad": "Recepción", "contexto.notas": "=HYPERLINK(\"http://x.test\")"}


def instantanea(contexto=None, org=None) -> bib.InstantaneaGeneracion:
    p = bib.leer_plantilla(TEXTO)
    datos = {**(ORG if org is None else org), **datos_del_documento(p, date(2026, 11, 4)), "dpo.designado": False}
    return bib.InstantaneaGeneracion(
        version_id="v-1", plantilla_md=TEXTO, plantilla_sha256=huella(TEXTO), esquema=[c.model_dump() for c in p.campos],
        organizacion=datos, contexto=dict(COMPLETO if contexto is None else contexto), fecha_emision="2026-11-04")


def pedido(modo="revision", formato="docx"):
    return bib.PedirGeneracion(modo=modo, formato=formato)


def texto_docx(archivo: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(archivo)) as z:
        xml = z.read("word/document.xml").decode()
    return "\n".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", xml))


def partes(archivo: bytes) -> dict[str, str]:
    with zipfile.ZipFile(io.BytesIO(archivo)) as z:
        return {n: z.read(n).decode("utf-8", "replace") for n in z.namelist()}


# --------------------------------------------------------------------------- instantánea y determinismo

def test_instantanea_con_checksum_estable_y_sensible_a_los_datos():
    a, b = instantanea(), instantanea()
    assert a.sha256 == b.sha256 and re.fullmatch(r"[a-f0-9]{64}", a.sha256)
    assert instantanea({**COMPLETO, "contexto.notas": "otra"}).sha256 != a.sha256
    assert bib.InstantaneaGeneracion.desde_dict(a.como_dict()).sha256 == a.sha256
    assert a.como_dict()["plantilla_sha256"] == huella(TEXTO) and a.procedencia is None  # BIB-202 la rellenará


@pytest.mark.parametrize("formato", ["docx", "xlsx"])
def test_misma_instantanea_mismos_bytes(formato):
    uno = bib.construir_generacion(instantanea(), pedido(formato=formato))[0]
    otro = bib.construir_generacion(bib.InstantaneaGeneracion.desde_dict(instantanea().como_dict()),
                                    pedido(formato=formato))[0]
    assert uno == otro


# --------------------------------------------------------------------------- borrador y revisión

def test_borrador_admite_faltantes_con_marca_y_listado():
    archivo, faltan, nombre = bib.construir_generacion(instantanea({"contexto.camaras": "si"}), pedido("borrador"))
    assert faltan == ["contexto.finalidad"]
    contenido = texto_docx(archivo)
    assert "BORRADOR" in contenido and "Datos que faltan:" in contenido and "[FALTA: contexto.finalidad]" in contenido
    assert nombre == "BIB-099-v0.1.0-borrador.docx"


@pytest.mark.parametrize("contexto, falta", [
    ({"contexto.camaras": "si"}, "contexto.finalidad"),  # obligatorio de la rama que aplica
    ({"contexto.finalidad": "Recepción"}, "contexto.camaras"),  # condición sin responder
])
def test_revision_exige_obligatorios_y_condicionales(contexto, falta):
    with pytest.raises(ErrorNegocio) as e:
        bib.construir_generacion(instantanea(contexto), pedido())
    assert e.value.code == "BIB_GEN_INCOMPLETA" and falta in e.value.detail


def test_revision_no_exige_el_opcional_ni_la_rama_que_no_aplica():
    archivo, faltan, _ = bib.construir_generacion(instantanea({"contexto.camaras": "no"}), pedido())
    assert faltan == [] and "Sin cámaras en las instalaciones." in texto_docx(archivo)


def test_revision_sin_instrucciones_ni_bloques_ni_variables():
    archivo, faltan, nombre = bib.construir_generacion(instantanea(), pedido())
    contenido = texto_docx(archivo)
    assert faltan == [] and nombre.endswith("para_revision.docx")
    for resto in ("{{", "}}", "⟦", "⟧", "[FALTA", "FALTA", "BORRADOR", "<!--", "Escriba aquí", "Ejemplo:",
                  "Sin cámaras", "documento.aprobado_por"):
        assert resto not in contenido, resto
    assert "Zonas: Recepción" in contenido and "=HYPERLINK" in contenido and salida.LINEA_FIRMA in contenido


def test_guia_separada_del_contenido():
    uso, guia = salida.separar_guia(bib.leer_plantilla(TEXTO).cuerpo)
    assert "Escriba aquí la guía interna." in guia and "Ejemplo: cámaras en recepción." in guia
    assert "<!--" not in uso and "Escriba aquí" not in uso


def test_residuos_detecta_marcas_del_sistema_y_no_datos_del_usuario():
    assert salida.residuos("hola ⟦falta: x⟧ {{#si a}}") and salida.residuos("[FALTA: x]")
    assert salida.residuos("dato del usuario: {{no es plantilla}} <!-- texto -->") == []


# --------------------------------------------------------------------------- DOCX

def test_docx_mantiene_estilos_y_tablas_y_escapa_html():
    inst = instantanea({**COMPLETO, "contexto.finalidad": "<b>no</b> & <script>x</script>"})
    archivo = bib.construir_generacion(inst, pedido())[0]
    p = partes(archivo)
    assert {"[Content_Types].xml", "word/document.xml", "word/styles.xml"} <= set(p)
    for estilo in ("Title", "Heading1", "TablaDocumento"):
        assert f'w:styleId="{estilo}"' in p["word/styles.xml"]
    doc = p["word/document.xml"]
    assert '<w:pStyle w:val="Heading1"/>' in doc and '<w:tblStyle w:val="TablaDocumento"/>' in doc
    assert doc.count("<w:tr>") == 3 and "<script>" not in doc and "&lt;script&gt;" in doc


def test_variables_partidas_entre_runs():
    assert generador_docx.resolver_runs(["Hola {{NOM", "BRE}}", " y {{RUC}}."], {"NOMBRE": "Ana", "RUC": "1"}) == \
        ["Hola Ana", "", " y 1."]
    assert generador_docx.resolver_runs(["{{", "A", "}}{{B}}"], {"A": "x", "B": "y"}) == ["x", "", "y"]
    xml = ('<w:p><w:r><w:rPr><w:b/></w:rPr><w:t>RUC {{R</w:t></w:r><w:r><w:t>UC}}</w:t></w:r></w:p>')
    assert generador_docx.rellenar_document_xml(xml, {"RUC": "<1>"}) == \
        '<w:p><w:r><w:rPr><w:b/></w:rPr><w:t>RUC &lt;1&gt;</w:t></w:r><w:r><w:t></w:t></w:r></w:p>'


# --------------------------------------------------------------------------- XLSX

def test_xlsx_fechas_tablas_validaciones_y_formula_recalculada():
    archivo = bib.construir_generacion(instantanea(), pedido(formato="xlsx"))[0]
    libro = load_workbook(io.BytesIO(archivo))
    assert libro.sheetnames == ["Documento", "Tabla 1"] and libro.calculation.fullCalcOnLoad
    hoja = libro["Tabla 1"]
    assert "Tabla1" in hoja.tables and hoja.tables["Tabla1"].ref == "A1:C3"
    assert hoja["B2"].value.date() == date(2026, 11, 4) and hoja["B2"].number_format == "yyyy-mm-dd"
    assert hoja["B3"].value == "2026-02-30"  # fecha imposible: queda como texto, no se inventa
    assert any(v.formula1 == '"sí,no"' and "C2:C3" in str(v.sqref) for v in hoja.data_validations.dataValidation)
    assert hoja["B4"].value == "=COUNTA(A2:A3)" and generador_xlsx.recalcular(hoja, "B4") == 2
    assert "Datos" in libro["Documento"].tables and libro["Documento"]["A2"].value == "Para revisión"


def test_xlsx_entrada_que_parece_formula_queda_como_texto():
    archivo = bib.construir_generacion(instantanea(), pedido(formato="xlsx"))[0]
    hoja = load_workbook(io.BytesIO(archivo))["Tabla 1"]
    celda = hoja["A3"]
    assert celda.value == "=HYPERLINK(\"http://x.test\")" and celda.data_type == "s" and celda.quotePrefix
    hoja_xml = partes(archivo)["xl/worksheets/sheet2.xml"]
    assert re.findall(r"<f>([^<]*)</f>", hoja_xml) == ["COUNTA(A2:A3)"]


def test_xlsx_borrador_lista_faltantes():
    archivo = bib.construir_generacion(instantanea({"contexto.camaras": "si"}), pedido("borrador", "xlsx"))[0]
    libro = load_workbook(io.BytesIO(archivo))
    assert libro["Documento"]["A2"].value.startswith("BORRADOR") and libro["Faltantes"]["A2"].value == "contexto.finalidad"


def test_formula_no_autorizada_se_rechaza():
    with pytest.raises(ErrorNegocio) as e:
        generador_xlsx.formula("INDIRECT", "A", 1, 2)
    assert e.value.code == "BIB_GEN_FORMULA_NO_AUTORIZADA"


# --------------------------------------------------------------------------- catálogo y migración

def test_codigos_registrados():
    for codigo in ("BIB_GEN_INCOMPLETA", "BIB_GEN_NO_ENCONTRADA", "BIB_GEN_SALIDA_INVALIDA",
                   "BIB_GEN_FORMULA_NO_AUTORIZADA"):
        assert codigo in CATALOGO_ERRORES


def test_migracion_una_cabeza_rls_y_sin_update():
    script = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini")))
    assert len(script.get_heads()) == 1
    revision = script.get_revision("20261116_bib_generacion")
    assert revision is not None and len(revision.revision) <= 32
    cuerpo = MIGRACION.read_text(encoding="utf-8")
    assert "FORCE ROW LEVEL SECURITY" in cuerpo and "GRANT SELECT,INSERT ON biblioteca_generaciones TO lopdp_app" in cuerpo
    assert not re.search(r"GRANT[^;]*(UPDATE|DELETE)[^;]*biblioteca_generaciones", cuerpo)


# --------------------------------------------------------------------------- persistencia (base propia)

async def _borrador(sesion, ids, tenant, contexto):
    version = await publicar(sesion, ids, TEXTO)
    return await bib.crear_borrador(sesion, fuentes(), tenant, ids["miembro"],
                                    bib.EntradaBorrador(version_id=version, contexto=contexto))


@pytest.mark.asyncio
async def test_db_generar_guarda_instantanea_checksum_y_archivo(db_bib):
    sesion, ids, tenant, _ = db_bib
    borrador = await _borrador(sesion, ids, tenant, {"contexto.camaras": "si"})
    g = await bib.generar_documento(sesion, fuentes(), tenant, ids["miembro"], borrador.id, pedido("borrador"))
    assert g.estado == "borrador" and g.faltantes == ["contexto.finalidad"]
    with pytest.raises(ErrorNegocio) as e:
        await bib.generar_documento(sesion, fuentes(), tenant, ids["miembro"], borrador.id, pedido())
    assert e.value.code == "BIB_GEN_INCOMPLETA"
    borrador = await bib.guardar_borrador(sesion, fuentes(), tenant, ids["miembro"], borrador.id,
                                          bib.GuardarBorrador(revision=1, contexto=COMPLETO))
    r = await bib.generar_documento(sesion, fuentes(), tenant, ids["miembro"], borrador.id, pedido(formato="xlsx"))
    assert r.estado == "para_revision" and r.faltantes == [] and r.plantilla_sha256 == huella(TEXTO)
    datos, mime, nombre, sha = await bib.archivo_generado(sesion, tenant, ids["miembro"], r.id)
    assert mime.endswith("spreadsheetml.sheet") and nombre.endswith(".xlsx") and sha == r.archivo_sha256
    fila = (await sesion.execute(text("SELECT instantanea FROM biblioteca_generaciones WHERE id=:id"),
                                 {"id": r.id})).scalar_one()
    rehecho = bib.construir_generacion(bib.InstantaneaGeneracion.desde_dict(fila), pedido(formato="xlsx"))[0]
    assert bib.InstantaneaGeneracion.desde_dict(fila).sha256 == r.instantanea_sha256 and rehecho == datos
    listadas = await bib.listar_generaciones(sesion, tenant, ids["miembro"], borrador.id)
    assert {x.id for x in listadas} == {r.id, g.id}  # misma transacción: mismo creado_en


@pytest.mark.asyncio
async def test_db_otra_organizacion_no_ve_ni_genera(db_bib):
    sesion, ids, tenant, otro = db_bib
    borrador = await _borrador(sesion, ids, tenant, COMPLETO)
    g = await bib.generar_documento(sesion, fuentes(), tenant, ids["miembro"], borrador.id, pedido())
    with pytest.raises(ErrorNegocio) as e:
        await bib.archivo_generado(sesion, otro, ids["ajeno"], g.id)
    assert e.value.code == "BIB_GEN_NO_ENCONTRADA"
    with pytest.raises(ErrorNegocio) as e:
        await bib.generar_documento(sesion, fuentes(), otro, ids["ajeno"], borrador.id, pedido())
    assert e.value.code == "BIB_BORRADOR_NO_ENCONTRADO"


@pytest.mark.asyncio
async def test_db_generacion_inmutable(db_bib):
    sesion, ids, tenant, _ = db_bib
    borrador = await _borrador(sesion, ids, tenant, COMPLETO)
    g = await bib.generar_documento(sesion, fuentes(), tenant, ids["miembro"], borrador.id, pedido())
    for orden in ("UPDATE biblioteca_generaciones SET estado='borrador' WHERE id=:id",
                  "DELETE FROM biblioteca_generaciones WHERE id=:id"):
        punto = await sesion.begin_nested()
        with pytest.raises(DBAPIError):
            await sesion.execute(text(orden), {"id": g.id})
        await punto.rollback()
