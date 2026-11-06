# ¤adpa ¤rbac-tenant ¤arbitro
# ¤¤qa-engineer
"""Árbitro BIB-206: la vista previa usa la misma instantánea y modelo de salida que el archivo.

Puras: el texto de la vista previa coincide con el del DOCX generado (acentos, texto extenso, varias filas,
campos vacíos, bloques condicionales) y no expone variables ni cortes; la huella anunciada es la del archivo;
la vista previa obsoleta se rechaza. Persistencia (base del arnés o rama Neon propia): editar el borrador
invalida la vista previa anterior y emitir desde ella no crea archivo; otra organización no la ve.

Mutación decisiva (servir la vista previa de una revisión anterior tras editar): en
`features/biblioteca/services/preview.py:111` (`exigir_vigente`), cambiar la condición por `if False:` acepta
la vista previa de la revisión anterior. Observado el 2026-11-04 con
`python3 -m pytest tests/test_bib_206_preview.py -q`: falla ``test_vista_obsoleta_se_rechaza`` (1 fallo,
10 pasan, sin base); restaurado: 11 pasan.
"""
import pytest
from sqlalchemy import text
from api.errores import ErrorNegocio
from app_core.errors import CATALOGO_ERRORES
from features.biblioteca import biblioteca_service as bib
from features.biblioteca.services.generacion import huella_bytes
from features.biblioteca.services.salida import residuos
from tests.test_bib_201_formularios import fuentes, db_bib  # noqa: F401
import html
import io
import re
import zipfile
from tests.test_bib_205_generacion import COMPLETO, _borrador, instantanea, pedido

LARGO = "Tratamiento de datos de niñas, niños y adolescentes en Quito — Ñandú, pingüino, acción. " * 40


def texto_docx(archivo: bytes) -> str:
    """Texto de los `<w:t>` del DOCX, sin saltos, con entidades resueltas."""
    with zipfile.ZipFile(io.BytesIO(archivo)) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    return html.unescape("".join(re.findall(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", xml, re.S)))


def plano(vista: bib.VistaPrevia) -> str:
    """Texto de la vista previa en el orden del documento."""
    partes: list[str] = []
    for b in vista.bloques:
        partes.extend(c for fila in b.filas for c in fila) if b.tipo == "tabla" else partes.append(b.texto)
    return "".join(partes).replace("**", "").replace("\n", "")


def vista(contexto=None, modo="revision", formato="docx", revision=1):
    return bib.vista_de(instantanea(contexto), pedido(modo, formato), "b-1", revision)


# --------------------------------------------------------------------------- fidelidad (puras)

@pytest.mark.parametrize("contexto", [
    COMPLETO,
    {**COMPLETO, "contexto.finalidad": LARGO},
    {**COMPLETO, "contexto.notas": ""},
    {**COMPLETO, "contexto.camaras": "no"},
])
def test_vista_previa_igual_al_docx_y_sin_marcas(contexto):
    v = vista(contexto)
    archivo, _, nombre = bib.construir_generacion(instantanea(contexto), pedido())
    assert plano(v) == texto_docx(archivo)
    assert v.archivo_sha256 == huella_bytes(archivo) and v.nombre_archivo == nombre
    todo = plano(v)
    assert residuos(todo) == [] and "{{" not in todo and "[FALTA:" not in todo


def test_acentos_texto_largo_y_varias_filas_completos():
    v = vista({**COMPLETO, "contexto.finalidad": LARGO})
    todo = plano(v)
    assert LARGO.strip() in todo  # sin cortes
    tabla = next(b for b in v.bloques if b.tipo == "tabla")
    assert len(tabla.filas) == 3 and all(len(f) == 3 for f in tabla.filas)
    assert any(b.tipo == "titulo" and b.texto.startswith("Política de") for b in v.bloques)


def test_condicional_muestra_solo_la_rama_que_aplica():
    assert "Sin cámaras en las instalaciones." in plano(vista({**COMPLETO, "contexto.camaras": "no"}))
    assert "Zonas: Recepción" in plano(vista())
    assert "Sin cámaras" not in plano(vista())


def test_guia_no_aparece_en_la_vista_previa():
    todo = plano(vista())
    assert "Escriba aquí la guía interna" not in todo and "Ejemplo: cámaras" not in todo


def test_borrador_marca_faltantes_y_revision_los_rechaza():
    incompleto = {"contexto.camaras": "si"}
    v = vista(incompleto, modo="borrador")
    assert v.estado == "borrador" and v.faltantes == ["contexto.finalidad"]
    assert "[FALTA: contexto.finalidad]" in plano(v)
    with pytest.raises(ErrorNegocio) as e:
        vista(incompleto)
    assert e.value.code == "BIB_GEN_INCOMPLETA"


def test_identifica_estado_version_e_instantanea():
    v = vista(revision=4)
    assert v.estado == "para_revision" and v.revision == 4 and v.instantanea_sha256 == instantanea().sha256
    assert v.nombre_archivo.endswith("-para_revision.docx")


def test_xlsx_comparte_instantanea_y_huella_de_archivo():
    v = vista(formato="xlsx")
    archivo, _, _ = bib.construir_generacion(instantanea(), pedido(formato="xlsx"))
    assert v.archivo_sha256 == huella_bytes(archivo) and v.instantanea_sha256 == vista().instantanea_sha256


def test_vista_obsoleta_se_rechaza():
    v = vista(revision=2)
    bib.exigir_vigente(v, 2, v.instantanea_sha256)
    for revision, sha in ((1, v.instantanea_sha256), (2, "0" * 64)):
        with pytest.raises(ErrorNegocio) as e:
            bib.exigir_vigente(v, revision, sha)
        assert e.value.code == "BIB_PREVIEW_OBSOLETA"
    assert CATALOGO_ERRORES["BIB_PREVIEW_OBSOLETA"].status_code == 409


# --------------------------------------------------------------------------- persistencia (base propia)

def _emitir(v: bib.VistaPrevia) -> bib.EmitirDesdeVista:
    return bib.EmitirDesdeVista(modo=v.modo, formato=v.formato, revision=v.revision,
                                instantanea_sha256=v.instantanea_sha256)


@pytest.mark.asyncio
async def test_db_editar_invalida_la_vista_previa_anterior(db_bib):
    sesion, ids, tenant, _ = db_bib
    borrador = await _borrador(sesion, ids, tenant, COMPLETO)
    antes = await bib.previsualizar(sesion, fuentes(), tenant, ids["miembro"], borrador.id, pedido())
    assert antes.revision == 1
    await bib.guardar_borrador(sesion, fuentes(), tenant, ids["miembro"], borrador.id,
                               bib.GuardarBorrador(revision=1, contexto={**COMPLETO, "contexto.finalidad": "Bodega"}))
    despues = await bib.previsualizar(sesion, fuentes(), tenant, ids["miembro"], borrador.id, pedido())
    assert despues.revision == 2 and despues.instantanea_sha256 != antes.instantanea_sha256
    assert "Zonas: Bodega" in plano(despues) and "Zonas: Recepción" in plano(antes)
    contar = text("SELECT count(*) FROM biblioteca_generaciones WHERE borrador_id=:b")
    with pytest.raises(ErrorNegocio) as e:
        await bib.emitir_desde_vista(sesion, fuentes(), tenant, ids["miembro"], borrador.id, _emitir(antes))
    assert e.value.code == "BIB_PREVIEW_OBSOLETA"
    assert (await sesion.execute(contar, {"b": borrador.id})).scalar_one() == 0
    g = await bib.emitir_desde_vista(sesion, fuentes(), tenant, ids["miembro"], borrador.id, _emitir(despues))
    assert g.instantanea_sha256 == despues.instantanea_sha256 and g.archivo_sha256 == despues.archivo_sha256
    datos, _, _, _ = await bib.archivo_generado(sesion, tenant, ids["miembro"], g.id)
    assert plano(despues) == texto_docx(datos)


@pytest.mark.asyncio
async def test_db_otra_organizacion_no_previsualiza(db_bib):
    sesion, ids, tenant, otro = db_bib
    borrador = await _borrador(sesion, ids, tenant, COMPLETO)
    with pytest.raises(ErrorNegocio) as e:
        await bib.previsualizar(sesion, fuentes(), otro, ids["ajeno"], borrador.id, pedido())
    assert e.value.code == "BIB_BORRADOR_NO_ENCONTRADO"
