# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤vigilancia-spdp ¤inteligencia-normativa ¤transcripcion-normativa ¤arbitro
"""NORM-06: el análisis de impacto lee los PDF escaneados con Gemini (por el pasillo de inferencia).

Los PDF se generan aquí (ningún binario en el repositorio) y el modelo es siempre un doble: nunca se llama a Vertex.
Cada prueba documenta su mutación: el cambio en el código que la pondría en rojo.
"""
import asyncio
import io
import uuid
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from features.inferencia import inferencia_service as svc_inferencia
from features.inferencia.domain.errores import InferenciaNoDisponible
from features.inferencia.domain.modelos_permitidos import MODELO_GENERACION
from features.inteligencia_normativa.domain import transcripcion as dominio
from features.inteligencia_normativa.domain.errores import IaNoDisponible, ResolucionSinTexto
from features.inteligencia_normativa.domain.transcripcion import PaginaPdf, es_escaneo
from features.inteligencia_normativa.services import extraccion, impacto, transcripcion_engine

SELLO = "Registro Oficial 5S 459 " + "x" * 16  # 40 caracteres de sello
TEXTO_DENSO = ("Articulo 5. El responsable publica un aviso de privacidad claro. " * 8)[:600]
MODELO = MODELO_GENERACION


def pdf_de_paginas(paginas: list[tuple[str, bool]]) -> bytes:
    """PDF mínimo: por página, su texto y, si `con_imagen`, un XObject /Image de 1x1 píxeles."""
    objetos: list[str] = ["", ""]  # 1 catálogo y 2 páginas, se rellenan al final
    imagen = len(objetos) + 1
    objetos.append("<< /Type /XObject /Subtype /Image /Width 1 /Height 1 /ColorSpace /DeviceGray "
                   "/BitsPerComponent 8 /Length 1 >>\nstream\n\x00\nendstream")
    fuente = len(objetos) + 1
    objetos.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    hijos = []
    for texto, con_imagen in paginas:
        flujo = f"BT /F1 9 Tf 20 800 Td ({texto}) Tj ET"
        contenido = len(objetos) + 1
        objetos.append(f"<< /Length {len(flujo)} >>\nstream\n{flujo}\nendstream")
        pagina = len(objetos) + 1
        xobj = f"/XObject << /Im0 {imagen} 0 R >>" if con_imagen else ""
        objetos.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents {contenido} 0 R "
                       f"/Resources << /Font << /F1 {fuente} 0 R >> {xobj} >> >>")
        hijos.append(pagina)
    objetos[0] = "<< /Type /Catalog /Pages 2 0 R >>"
    objetos[1] = f"<< /Type /Pages /Kids [{' '.join(f'{h} 0 R' for h in hijos)}] /Count {len(hijos)} >>"
    salida = b"%PDF-1.4\n"
    posiciones = []
    for i, o in enumerate(objetos, 1):
        posiciones.append(len(salida))
        salida += f"{i} 0 obj\n{o}\nendobj\n".encode("latin-1")
    xref = len(salida)
    salida += f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode()
    salida += b"".join(f"{p:010d} 00000 n \n".encode() for p in posiciones)
    salida += f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    return salida


def escaneado(paginas: int = 1) -> bytes:
    return pdf_de_paginas([(SELLO, True)] * paginas)


def con_texto(paginas: int = 1) -> bytes:
    return pdf_de_paginas([(TEXTO_DENSO, False)] * paginas)


def _paginas(pdf: bytes) -> int:
    from pypdf import PdfReader

    return len(PdfReader(io.BytesIO(pdf)).pages)


# ------------------------------------------------------------ R1: detección del escaneo

def test_es_escaneo_distingue_el_escaneado_del_de_texto():
    """Mutación m1: umbral de 30 caracteres da rojo (el sello de 40 ya no cuenta como escaneado). m2: no exigir `tiene_imagen`."""
    assert es_escaneo(extraccion.estadisticas(escaneado(3))) is True
    assert es_escaneo(extraccion.estadisticas(con_texto(3))) is False


def test_el_umbral_son_300_caracteres_utiles_y_la_imagen_es_necesaria():
    """Mutación m2: no exigir `tiene_imagen` hace escaneada una página corta sin imagen."""
    assert dominio.UMBRAL_CARACTERES_UTILES == 300
    assert es_escaneo([PaginaPdf(40, True)]) is True
    assert es_escaneo([PaginaPdf(299, True)]) is True
    assert es_escaneo([PaginaPdf(300, True)]) is False
    assert es_escaneo([PaginaPdf(40, False)]) is False  # corta pero sin imagen: no es un escaneo


def test_la_mitad_de_las_paginas_decide():
    assert es_escaneo([PaginaPdf(40, True), PaginaPdf(2000, False)]) is True   # 50 %
    assert es_escaneo([PaginaPdf(40, True), PaginaPdf(2000, False), PaginaPdf(2000, False)]) is False
    assert es_escaneo([]) is False


def test_las_estadisticas_cuentan_caracteres_sin_espacios_e_imagen():
    estadisticas = extraccion.estadisticas(pdf_de_paginas([(SELLO, True), (TEXTO_DENSO, False)]))
    assert [p.tiene_imagen for p in estadisticas] == [True, False]
    assert estadisticas[0].caracteres_utiles == len(SELLO.replace(" ", ""))
    assert estadisticas[1].caracteres_utiles > 300
    assert extraccion.estadisticas(b"no es un pdf") == []


# ------------------------------------------------------------ R2: transcribir_pdf por el pasillo

class Modelos:
    def __init__(self, texto="Articulo 5. Texto transcrito.", version=f"{MODELO}-001"):
        self.llamadas: list[dict] = []
        self.texto, self.version = texto, version

    async def generate_content(self, **kw):
        self.llamadas.append(kw)
        return SimpleNamespace(text=self.texto, model_version=self.version)


@pytest.fixture
def vertex(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "proyecto-prueba")
    monkeypatch.setenv("VERTEX_LOCATION", "us")
    monkeypatch.setattr(svc_inferencia, "_cliente", None)
    topes: list[str] = []

    async def consumir(org):
        topes.append(org)

    svc_inferencia.inyectar_consumidor_de_prueba(consumir)
    yield topes
    svc_inferencia.inyectar_cliente_de_prueba(None)
    svc_inferencia.inyectar_consumidor_de_prueba(None)


def _cliente(modelos):
    return SimpleNamespace(aio=SimpleNamespace(models=modelos))


def test_transcribir_pdf_manda_el_pdf_como_parte_y_no_consume_tope(vertex):
    """Mutación m7: llamar a `_consumir_tope` en `transcribir_pdf` da rojo (el tope registraría una llamada)."""
    modelos = Modelos()
    svc_inferencia.inyectar_cliente_de_prueba(_cliente(modelos))
    texto, traza = asyncio.run(svc_inferencia.transcribir_pdf(escaneado(), dominio.PROMPT, modelo=MODELO))
    assert texto == "Articulo 5. Texto transcrito." and vertex == []
    assert (traza.modelo_version, traza.modelo_solicitado) == (f"{MODELO}-001", MODELO)
    assert (traza.prompt_id, traza.prompt_version) == ("normativa.transcripcion", 1)
    llamada = modelos.llamadas[0]
    partes = llamada["contents"]
    pdf_parte = partes[0]
    assert pdf_parte.inline_data.mime_type == "application/pdf" and pdf_parte.inline_data.data.startswith(b"%PDF")
    assert llamada["config"].temperature == 0


def test_transcribir_pdf_rechaza_un_modelo_no_permitido_sin_llamar(vertex):
    modelos = Modelos()
    svc_inferencia.inyectar_cliente_de_prueba(_cliente(modelos))
    with pytest.raises(InferenciaNoDisponible):
        asyncio.run(svc_inferencia.transcribir_pdf(escaneado(), dominio.PROMPT, modelo="gemini-no-permitido"))
    assert modelos.llamadas == []


@pytest.mark.parametrize("version", [None, "", "  "])
def test_transcribir_pdf_exige_model_version(vertex, version):
    svc_inferencia.inyectar_cliente_de_prueba(_cliente(Modelos(version=version)))
    with pytest.raises(InferenciaNoDisponible):
        asyncio.run(svc_inferencia.transcribir_pdf(escaneado(), dominio.PROMPT, modelo=MODELO))


def test_transcribir_pdf_reintenta_una_vez_y_falla_cerrada(vertex):
    from google.genai import errors

    class ModelosCaidos(Modelos):
        async def generate_content(self, **kw):
            self.llamadas.append(kw)
            raise errors.APIError(503, {"error": {"status": "UNAVAILABLE", "message": "x"}})

    modelos = ModelosCaidos()
    svc_inferencia.inyectar_cliente_de_prueba(_cliente(modelos))
    with pytest.raises(InferenciaNoDisponible):
        asyncio.run(svc_inferencia.transcribir_pdf(escaneado(), dominio.PROMPT, modelo=MODELO))
    assert len(modelos.llamadas) == 2


def test_transcribir_pdf_sin_region_falla_cerrada(vertex, monkeypatch):
    monkeypatch.delenv("VERTEX_LOCATION")
    svc_inferencia.inyectar_cliente_de_prueba(_cliente(Modelos()))
    with pytest.raises(InferenciaNoDisponible):
        asyncio.run(svc_inferencia.transcribir_pdf(escaneado(), dominio.PROMPT, modelo=MODELO))


def test_el_prompt_pide_transcripcion_literal_versionada():
    assert (dominio.PROMPT.id, dominio.PROMPT.version) == ("normativa.transcripcion", 1)
    sistema = dominio.PROMPT.sistema.lower()
    assert "literal" in sistema and "[ilegible]" in dominio.PROMPT.sistema and "resum" in sistema


# ------------------------------------------------------------ R3: por tramos

class Transcriptor:
    """Doble del pasillo: anota las páginas de cada llamada y devuelve un texto por tramo."""

    def __init__(self, falla_en: int | None = None, vacio_en: int | None = None):
        self.paginas: list[int] = []
        self.falla_en, self.vacio_en = falla_en, vacio_en

    async def __call__(self, pdf, prompt, *, modelo):
        self.paginas.append(_paginas(pdf))
        n = len(self.paginas)
        if n == self.falla_en:
            raise InferenciaNoDisponible()
        if n == self.vacio_en:
            return "   ", None
        traza = SimpleNamespace(modelo_version=f"{modelo}-001", modelo_solicitado=modelo,
                                prompt_id=prompt.id, prompt_version=prompt.version)
        return f"Articulo {n}. Tramo {n}.", traza


def test_25_paginas_son_tres_tramos_de_10_10_y_5_en_orden():
    transcriptor = Transcriptor()
    texto, traza = asyncio.run(transcripcion_engine.transcribir_por_tramos(escaneado(25), transcriptor, MODELO))
    assert transcriptor.paginas == [10, 10, 5]
    assert texto.index("Tramo 1") < texto.index("Tramo 2") < texto.index("Tramo 3")
    assert traza.modelo_version == f"{MODELO}-001"


@pytest.mark.parametrize("modo", ["falla", "vacio"])
def test_si_un_tramo_falla_o_da_vacio_falla_todo(modo):
    """Mutación m6: devolver lo parcial (los tramos ya transcritos) en vez de fallar da rojo."""
    transcriptor = Transcriptor(**{"falla_en" if modo == "falla" else "vacio_en": 2})
    with pytest.raises((IaNoDisponible, ResolucionSinTexto)):
        asyncio.run(transcripcion_engine.transcribir_por_tramos(escaneado(25), transcriptor, MODELO))
    assert transcriptor.paginas == [10, 10]  # no sigue con el tercero


# ------------------------------------------------------------ PostgreSQL: R4, R5 y privilegios

try:  # sin DATABASE_URL (sin PostgreSQL) el módulo de NORM-03 no se puede importar: las pruebas de base se saltan
    from tests.test_norm03_impacto_hitl import (  # noqa: F401 - fixtures y dobles de NORM-03
        ELEMENTOS_CON_SUSTENTO, RUTA, CatalogoFijo, LectorEnMemoria, modelo_simulado, mundo,
    )
    HAY_BASE = True
except RuntimeError:
    HAY_BASE = False

con_base = pytest.mark.skipif(not HAY_BASE, reason="necesita PostgreSQL (DATABASE_URL)")


@pytest_asyncio.fixture
async def doc(mundo):
    """Fija una huella única para el documento de la prueba y limpia sus transcripciones al terminar."""
    sha = uuid.uuid4().hex + uuid.uuid4().hex
    async with mundo["f"]() as s:
        await s.execute(text("UPDATE normativa_resoluciones SET archivo_sha256 = :h WHERE id = CAST(:i AS uuid)"),
                        {"h": sha, "i": mundo["resolucion"]})
        await s.commit()
    yield sha
    async with mundo["f"]() as s:
        await s.execute(text("DELETE FROM normativa_transcripciones WHERE archivo_sha256 = :h"), {"h": sha})
        await s.commit()


async def _solicitar(mundo, pdf, transcriptor, analizar=None):
    async with mundo["f"]() as s:
        return await impacto.solicitar(
            s, mundo["ta"], mundo["u"]["dpo_a"], mundo["resolucion"], lector=LectorEnMemoria({RUTA: pdf}),
            catalogo=CatalogoFijo(), analizar=analizar or modelo_simulado(ELEMENTOS_CON_SUSTENTO),
            modelo=MODELO, transcribir=transcriptor)


async def _cuenta(mundo, sha):
    async with mundo["f"]() as s:
        transcripciones = (await s.execute(text("SELECT count(*) FROM normativa_transcripciones "
                                                "WHERE archivo_sha256 = :h"), {"h": sha})).scalar_one()
        from app_core.db.session import fijar_contexto_rls
        await fijar_contexto_rls(s, mundo["ta"], mundo["u"]["dpo_a"])
        analisis = (await s.execute(text("SELECT count(*) FROM normativa_analisis_impacto"))).scalar_one()
    return transcripciones, analisis


@con_base
@pytest.mark.asyncio
async def test_un_escaneo_se_analiza_con_el_texto_transcrito(mundo, doc):
    """Mutación m3: analizar con la capa de texto (el sello) en vez de la transcripción da rojo."""
    analizar = modelo_simulado(ELEMENTOS_CON_SUSTENTO)
    r = await _solicitar(mundo, escaneado(2), Transcriptor(), analizar)
    assert r.origen_texto == "transcripcion" and "Tramo 1" in analizar.llamadas[0][0]
    assert SELLO not in analizar.llamadas[0][0]
    async with mundo["f"]() as s:
        fila = (await s.execute(text("SELECT modelo_solicitado, modelo_version, prompt_id, prompt_version, paginas, "
                                     "caracteres FROM normativa_transcripciones WHERE archivo_sha256 = :h"),
                                {"h": doc})).one()
    assert (fila.modelo_solicitado, fila.modelo_version) == (MODELO, f"{MODELO}-001")
    assert (fila.prompt_id, fila.prompt_version, fila.paginas) == ("normativa.transcripcion", 1, 2)


@con_base
@pytest.mark.asyncio
async def test_un_pdf_con_texto_no_llama_al_modelo_de_transcripcion(mundo, doc):
    transcriptor = Transcriptor()
    r = await _solicitar(mundo, con_texto(2), transcriptor)
    assert r.origen_texto == "capa_texto" and transcriptor.paginas == []
    assert (await _cuenta(mundo, doc))[0] == 0


@con_base
@pytest.mark.asyncio
@pytest.mark.parametrize("modo", ["lanza", "vacio"])
async def test_un_escaneo_con_el_pasillo_caido_o_vacio_no_guarda_nada(mundo, doc, modo):
    """Mutación m4: seguir con las cabeceras del sello cuando falla la transcripción da rojo."""
    transcriptor = Transcriptor(**{"falla_en" if modo == "lanza" else "vacio_en": 1})
    with pytest.raises((IaNoDisponible, ResolucionSinTexto)):
        await _solicitar(mundo, escaneado(2), transcriptor)
    assert await _cuenta(mundo, doc) == (0, 0)


@con_base
@pytest.mark.asyncio
async def test_dos_analisis_del_mismo_sha_transcriben_una_vez(mundo, doc):
    """Mutación m5: quitar la consulta previa a `normativa_transcripciones` da rojo (se llama otra vez)."""
    transcriptor = Transcriptor()
    await _solicitar(mundo, escaneado(25), transcriptor)
    await _solicitar(mundo, escaneado(25), transcriptor)
    assert transcriptor.paginas == [10, 10, 5]
    assert (await _cuenta(mundo, doc))[0] == 1


@con_base
@pytest.mark.asyncio
async def test_un_fallo_en_el_segundo_tramo_no_guarda_lo_parcial(mundo, doc):
    with pytest.raises(IaNoDisponible):
        await _solicitar(mundo, escaneado(25), Transcriptor(falla_en=2))
    assert await _cuenta(mundo, doc) == (0, 0)


@con_base
@pytest.mark.asyncio
async def test_lopdp_app_solo_lee_e_inserta_transcripciones(mundo, doc, db_engine):
    """La transcripción es inmutable: `UPDATE` y `DELETE` dan error como `lopdp_app`."""
    await _solicitar(mundo, escaneado(1), Transcriptor())
    motor = create_async_engine(db_engine.url, poolclass=NullPool)

    @event.listens_for(motor.sync_engine, "connect")
    def _rol(conexion, _registro):
        cursor = conexion.cursor()
        cursor.execute("SET SESSION AUTHORIZATION lopdp_app")
        cursor.close()

    fabrica = async_sessionmaker(motor, expire_on_commit=False, class_=AsyncSession)
    try:
        async with fabrica() as s:
            assert (await s.execute(text("SELECT count(*) FROM normativa_transcripciones"))).scalar_one() >= 1
        for sentencia in ("UPDATE normativa_transcripciones SET texto = 'otro'",
                          "DELETE FROM normativa_transcripciones"):
            async with fabrica() as s:
                with pytest.raises(DBAPIError):
                    await s.execute(text(sentencia))
                await s.rollback()
    finally:
        await motor.dispose()
