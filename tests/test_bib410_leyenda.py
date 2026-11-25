# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤arbitro
"""BIB-410: leyenda de redacción y aprobación (governance/especificaciones/BIB-410.md). Sin base: corre en cualquier máquina.

Mutaciones (cada una hace fallar la prueba indicada):
  - m1: un nombre fijo en el código -> test_m1_la_leyenda_de_la_ia_lleva_el_nombre_de_quien_aprobo;
  - m2: «Redactada con IA» en todas -> test_m2_la_leyenda_de_una_persona_nombra_al_autor;
  - m3: devolver la leyenda con el aprobador vacío -> test_m3_sin_aprobacion_registrada_la_leyenda_es_nula;
  - m4: quitar la versión del pie -> test_m4_el_pie_del_docx_y_del_xlsx_lleva_codigo_version_redaccion_y_aprobador.
"""
from __future__ import annotations

import hashlib
import re
import zipfile
from datetime import date, datetime, timezone
from io import BytesIO

import pytest

from features.biblioteca.domain.leyenda import CLAVE_PIE, fecha_larga, leyenda_de, pie_de_plantilla

FECHA = datetime(2026, 11, 25, 15, 0, tzinfo=timezone.utc)
PROHIBIDAS = ("validada", "certificada", "conforme", "legal")
TEXTO = "# Política\n\nTexto.\n\n| A | B |\n|---|---|\n| sí | 2026-01-15 |\n"
LEYENDA_DEMO = "Demostración · datos ficticios"


def test_la_fecha_va_larga_y_en_espanol():
    assert fecha_larga(date(2026, 11, 25)) == "25 de noviembre de 2026"
    assert fecha_larga(FECHA) == "25 de noviembre de 2026"
    assert fecha_larga(date(2027, 3, 1)) == "1 de marzo de 2027"


@pytest.mark.parametrize("nombre", ["Aleczandra Villavicencio", "José Pérez"])
def test_m1_la_leyenda_de_la_ia_lleva_el_nombre_de_quien_aprobo(nombre):
    ley = leyenda_de("publicada", "ia", ["ia"], nombre, FECHA)
    assert ley == {"redaccion": "ia", "aprobada_por": nombre, "aprobada_en": "25 de noviembre de 2026",
                   "texto": f"Redactada con IA y aprobada por {nombre} el 25 de noviembre de 2026."}


def test_m2_la_leyenda_de_una_persona_nombra_al_autor():
    ley = leyenda_de("publicada", "persona", ["Luis Mora"], "Ana Pérez", FECHA)
    assert ley["texto"] == "Redactada por Luis Mora y aprobada por Ana Pérez el 25 de noviembre de 2026."
    assert ley["redaccion"] == "persona" and "IA" not in ley["texto"]
    varios = leyenda_de("publicada", "persona", ["Luis Mora", "Eva Ruiz"], "Ana Pérez", FECHA)
    assert varios["texto"].startswith("Redactada por Luis Mora y Eva Ruiz y aprobada por Ana Pérez")


@pytest.mark.parametrize("estado,aprobador,fecha", [("en_revision", "Ana Pérez", FECHA), ("publicada", None, None),
                                                    ("publicada", "", FECHA), ("publicada", "  ", FECHA),
                                                    ("publicada", "Ana Pérez", None), ("retirada", "Ana Pérez", FECHA)])
def test_m3_sin_aprobacion_registrada_la_leyenda_es_nula(estado, aprobador, fecha):
    assert leyenda_de(estado, "ia", ["ia"], aprobador, fecha) is None
    assert leyenda_de(estado, "persona", ["Luis Mora"], aprobador, fecha) is None


def test_persona_sin_nombre_de_autor_no_inventa_leyenda():
    assert leyenda_de("publicada", "persona", [], "Ana Pérez", FECHA) is None


def test_el_texto_no_usa_palabras_de_certificacion():
    for ley in (leyenda_de("publicada", "ia", ["ia"], "Ana Pérez", FECHA),
                leyenda_de("publicada", "persona", ["Luis Mora"], "Ana Pérez", FECHA)):
        assert not any(p in ley["texto"].lower() for p in PROHIBIDAS)


# --- R4 · Pie de los documentos ---------------------------------------------------------------------

def _pie() -> str:
    return pie_de_plantilla("BIB-001", "1.0", leyenda_de("publicada", "persona", ["Luis Mora"], "Ana Pérez", FECHA))


def _construir(monkeypatch, entorno: str, formato: str, con_pie: bool = True) -> bytes:
    from features.biblioteca.domain.generacion import InstantaneaGeneracion, PedirGeneracion
    from features.biblioteca.services.generacion import construir

    cuerpo = "---\ncodigo: BIB-001\nversion: '1.0'\nnombre: Política\n---\n" + TEXTO
    organizacion = {"organizacion.ruc": "9999999990099"}
    if con_pie:
        organizacion[CLAVE_PIE] = _pie()
    inst = InstantaneaGeneracion(version_id="v-1", plantilla_md=cuerpo, plantilla_sha256=hashlib.sha256(cuerpo.encode()).hexdigest(),
                                 esquema=[], organizacion=organizacion, contexto={}, fecha_emision="2026-01-15", procedencia=None)
    monkeypatch.setenv("APP_ENV", entorno)
    return construir(inst, PedirGeneracion(modo="borrador", formato=formato))[0]


def _partes(archivo: bytes) -> dict[str, str]:
    with zipfile.ZipFile(BytesIO(archivo)) as z:
        return {n: z.read(n).decode("utf-8") for n in z.namelist() if n.endswith((".xml", ".rels"))}


def _pies_docx(partes: dict[str, str]) -> list[str]:
    return [n for n in partes if re.fullmatch(r"word/footer\d*\.xml", n)]


def test_el_pie_dice_codigo_version_redaccion_aprobador_y_alcance():
    assert _pie() == ("Plantilla del catálogo BIB-001 v1.0, redactada por Luis Mora y aprobada por Ana Pérez el 25 de noviembre de 2026. "
                      "La aprobación es de la plantilla, no de este documento.")
    ia = pie_de_plantilla("BIB-002", "2.1", leyenda_de("publicada", "ia", ["ia"], "Ana Pérez", FECHA))
    assert ia.startswith("Plantilla del catálogo BIB-002 v2.1, redactada con IA y aprobada por Ana Pérez el ")


def test_m4_el_pie_del_docx_y_del_xlsx_lleva_codigo_version_redaccion_y_aprobador(monkeypatch):
    from openpyxl import load_workbook

    pie = _pie()
    partes = _partes(_construir(monkeypatch, "development", "docx"))
    pies = _pies_docx(partes)
    assert pies and all(pie in partes[n] for n in pies)
    assert "BIB-001 v1.0" in partes[pies[0]] and "Ana Pérez" in partes[pies[0]] and "Luis Mora" in partes[pies[0]]
    assert pie not in partes["word/document.xml"]
    libro = load_workbook(BytesIO(_construir(monkeypatch, "development", "xlsx")))
    assert len(libro.worksheets) >= 2
    for hoja in libro.worksheets:
        assert hoja.oddFooter.center.text == pie, hoja.title
    assert all(CLAVE_PIE not in str(c.value) and pie not in str(c.value)
               for h in libro.worksheets for f in h.iter_rows() for c in f if c.value)  # la clave reservada no sale como dato


def test_sin_leyenda_la_salida_no_tiene_pie(monkeypatch):
    from openpyxl import load_workbook

    assert not _pies_docx(_partes(_construir(monkeypatch, "development", "docx", con_pie=False)))
    assert all(not h.oddFooter.center.text
               for h in load_workbook(BytesIO(_construir(monkeypatch, "development", "xlsx", con_pie=False))).worksheets)
    for formato in ("docx", "xlsx"):
        assert (_construir(monkeypatch, "development", formato, con_pie=False)
                == _construir(monkeypatch, "production", formato, con_pie=False))


def test_en_la_demo_van_los_dos_pies_primero_el_de_la_demo(monkeypatch):
    from openpyxl import load_workbook

    pie = _pie()
    docx = _partes(_construir(monkeypatch, "demo", "docx"))
    assert _pies_docx(docx)
    for n in _pies_docx(docx):
        assert docx[n].index(LEYENDA_DEMO) < docx[n].index(pie)
    for hoja in load_workbook(BytesIO(_construir(monkeypatch, "demo", "xlsx"))).worksheets:
        assert hoja.oddFooter.center.text == LEYENDA_DEMO + "\n" + pie


def test_el_pie_de_la_demo_solo_no_cambia(monkeypatch):
    from openpyxl import load_workbook

    docx = _partes(_construir(monkeypatch, "demo", "docx", con_pie=False))
    assert all(docx[n].count("<w:p>") == 1 and LEYENDA_DEMO in docx[n] for n in _pies_docx(docx))
    for hoja in load_workbook(BytesIO(_construir(monkeypatch, "demo", "xlsx", con_pie=False))).worksheets:
        assert hoja.oddFooter.center.text == LEYENDA_DEMO


# --- R1 a R3 · Lectura de datos (sesión simulada: la consulta real la corre el CI con PostgreSQL) -------

class _Filas:
    def __init__(self, filas):
        self._filas = filas

    def mappings(self):
        return self

    def all(self):
        return self._filas


class _Sesion:
    def __init__(self, versiones, revisiones, usuarios):
        self._por_tabla = {"biblioteca_versiones": versiones, "biblioteca_revisiones": revisiones, "users": usuarios}

    async def execute(self, consulta, _parametros=None):
        sql = str(consulta)
        return _Filas(next(f for t, f in self._por_tabla.items() if f"FROM {t}" in sql))


def _leyendas(versiones, revisiones, usuarios):
    import asyncio

    from features.biblioteca.services.catalogo import leyendas_de_versiones

    ids = [v["id"] for v in versiones]
    return asyncio.run(leyendas_de_versiones(_Sesion(versiones, revisiones, usuarios), ids))


def test_las_leyendas_salen_de_la_revision_tecnica_aprobada_y_el_nombre_visible():
    versiones = [
        {"id": "v-ia", "estado": "publicada", "redactada_por": "ia", "autores": ["ia"], "generacion": 2},
        {"id": "v-p", "estado": "publicada", "redactada_por": "persona", "autores": ["u-luis"], "generacion": 1},
        {"id": "v-rev", "estado": "en_revision", "redactada_por": "ia", "autores": ["ia"], "generacion": 1},
        {"id": "v-vieja", "estado": "publicada", "redactada_por": "persona", "autores": ["u-luis"], "generacion": 1},
    ]
    revisiones = [
        {"version_id": "v-ia", "generacion": 1, "revisor_id": "u-eva", "creada_en": datetime(2026, 11, 1, tzinfo=timezone.utc)},
        {"version_id": "v-ia", "generacion": 2, "revisor_id": "u-ana", "creada_en": datetime(2026, 11, 26, 2, 0, tzinfo=timezone.utc)},
        {"version_id": "v-p", "generacion": 1, "revisor_id": "u-luis", "creada_en": FECHA},  # el autor no se aprueba a sí mismo
        {"version_id": "v-p", "generacion": 1, "revisor_id": "u-ana", "creada_en": FECHA},
        {"version_id": "v-rev", "generacion": 1, "revisor_id": "u-ana", "creada_en": FECHA},
    ]
    usuarios = [{"id": "u-ana", "nombre": "Ana Pérez"}, {"id": "u-luis", "nombre": "Luis Mora"}, {"id": "u-eva", "nombre": "Eva Ruiz"}]
    salida = _leyendas(versiones, revisiones, usuarios)
    # 26 nov 02:00 UTC es el 25 nov a las 21:00 en Guayaquil: manda el día de negocio
    assert salida["v-ia"]["texto"] == "Redactada con IA y aprobada por Ana Pérez el 25 de noviembre de 2026."
    assert salida["v-p"]["texto"] == "Redactada por Luis Mora y aprobada por Ana Pérez el 25 de noviembre de 2026."
    assert salida["v-rev"] is None  # en revisión
    assert salida["v-vieja"] is None  # publicada sin aprobación registrada: nunca «aprobada por —»


def test_sin_nombre_visible_no_hay_leyenda_ni_se_usa_el_correo():
    versiones = [{"id": "v-1", "estado": "publicada", "redactada_por": "ia", "autores": ["ia"], "generacion": 1}]
    revisiones = [{"version_id": "v-1", "generacion": 1, "revisor_id": "u-ana", "creada_en": FECHA}]
    assert _leyendas(versiones, revisiones, [])["v-1"] is None


def test_la_lectura_editorial_lleva_el_campo_leyenda():
    from features.biblioteca.domain.propuestas_ia import VersionMaestraMd
    from features.biblioteca.services import editorial

    assert "leyenda" in VersionMaestraMd.model_fields and VersionMaestraMd.model_fields["leyenda"].default is None
    fuente = editorial.__loader__.get_source(editorial.__name__)
    assert fuente.count("leyendas_de_versiones(session") == 2  # listar (una vez para la lista) y leer_version
