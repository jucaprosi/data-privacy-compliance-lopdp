# ¤vertex-cache ¤copiloto-ia ¤gemini-vertex
"""VTX-01: caché del corpus por sha256, DLP Módulo 10 pre-vuelo y citación cerrada. Sin red: Vertex con doble."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import replace
from types import SimpleNamespace

import pytest

from app_core.errors import ErrorNegocio
from features.ai_copilot.services import vertex_cached_rag_engine as motor
from features.inferencia import inferencia_service as svc
from features.regulacion_rag.domain.corpus import CORPUS_NORMATIVO_OFICIAL, fundamento
from features.regulacion_rag.services import vertex_context_cache as cache

CEDULA = "1710034065"
CEDULA_2 = "0926687856"
CEDULA_INVALIDA = "1712345678"
ORG = "org-vtx01"


class DobleVertex:
    """Doble del cliente genai: registra lo que saldría hacia Vertex y responde lo programado."""

    def __init__(self, texto: str):
        self.texto = texto
        self.enviados: list[dict] = []
        self.aio = SimpleNamespace(models=SimpleNamespace(generate_content=self._generar))

    async def _generar(self, *, model, contents, config):
        self.enviados.append({"model": model, "contents": contents, "sistema": config.system_instruction})
        return SimpleNamespace(text=self.texto, model_version=f"{model}-001")


class DobleCreador:
    def __init__(self):
        self.llamadas: list[tuple[str, str, int]] = []

    def __call__(self, modelo, contenido, ttl_seconds):
        self.llamadas.append((modelo, contenido, ttl_seconds))
        return f"projects/p/locations/us-central1/cachedContents/c{len(self.llamadas)}", 4321


def _corpus() -> dict:
    return {n.id: fundamento(n.id) for n in CORPUS_NORMATIVO_OFICIAL}


@pytest.fixture
def entorno(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "proyecto-prueba")
    monkeypatch.setenv("VERTEX_LOCATION", "us-central1")

    async def consumir(_org):
        return None

    svc.inyectar_consumidor_de_prueba(consumir)
    creador = DobleCreador()
    cache.vaciar_registro()
    cache.configurar_creador(creador)
    yield creador
    svc.inyectar_cliente_de_prueba(None)
    svc.inyectar_consumidor_de_prueba(None)
    cache.configurar_creador(None)
    cache.vaciar_registro()


def _consultar(texto, doble, modo="rapida"):
    svc.inyectar_cliente_de_prueba(doble)
    return asyncio.run(
        motor.consultar(texto, org_id=ORG, modo=modo, obtener_cache=lambda m: cache.obtener_o_crear(m), corpus_citable=_corpus)
    )


def _fuga(doble: DobleVertex, cedula: str) -> bool:
    """Hay fuga si la cédula llega a Vertex o si el filtro pre-vuelo no dejó su marca."""
    salida = " ".join(e["contents"] + e["sistema"] for e in doble.enviados)
    return cedula in salida or motor.MARCA_CEDULA not in salida


def test_vertex_context_cache_reutiliza_corpus_y_cita_fuente(entorno):
    doble = DobleVertex('{"respuesta": "Se requiere consentimiento.", "citas": ["L8"]}')
    r1 = _consultar("¿Cuándo necesito consentimiento?", doble)
    r2 = _consultar("¿Y si lo revocan?", doble)
    assert r1.cache_name == r2.cache_name and r1.cache_name.endswith("/c1")
    assert len(entorno.llamadas) == 1
    assert r2.citas[0]["id"] == "L8" and r2.citas[0]["articulo"] == "LOPDP, Art. 8"
    assert not r2.incertidumbre
    assert r2.traza.corpus_sha256 == r2.corpus_sha256


def test_modelo_por_modo(entorno):
    doble = DobleVertex('{"respuesta": "x", "citas": ["L7"]}')
    _consultar("a", doble, modo="dictamen")
    _consultar("b", doble, modo="rapida")
    assert [e["model"] for e in doble.enviados] == ["gemini-2.5-pro", "gemini-2.5-flash"]
    assert {ll[0] for ll in entorno.llamadas} == {"gemini-2.5-pro", "gemini-2.5-flash"}


def test_reforma_normativa_invalida_la_cache(entorno):
    d1 = cache.obtener_o_crear("gemini-2.5-flash")
    reformado = list(CORPUS_NORMATIVO_OFICIAL)
    reformado[0] = replace(reformado[0], texto_oficial=reformado[0].texto_oficial + " Reforma.")
    d2 = cache.obtener_o_crear("gemini-2.5-flash", corpus=reformado, corpus_version="reforma-1")
    assert d1.corpus_sha256 != d2.corpus_sha256 and d1.cache_name != d2.cache_name
    assert len(entorno.llamadas) == 2


def test_ttl_vencido_recrea(entorno):
    t = [0.0]
    cache.obtener_o_crear("gemini-2.5-flash", ttl_seconds=10, reloj=lambda: t[0])
    t[0] = 11.0
    cache.obtener_o_crear("gemini-2.5-flash", ttl_seconds=10, reloj=lambda: t[0])
    assert len(entorno.llamadas) == 2


def test_contenido_cacheado_es_solo_corpus_publico(entorno):
    doble = DobleVertex('{"respuesta": "x", "citas": ["L8"]}')
    _consultar(f"Consulta secreta del tenant {ORG} con cédula {CEDULA}", doble)
    (_, contenido, _), = entorno.llamadas
    assert contenido == cache.texto_canonico(CORPUS_NORMATIVO_OFICIAL)
    for dato in ("secreta", ORG, CEDULA, motor.MARCA_CEDULA):
        assert dato not in contenido


def test_vertex_rag_redacta_cedula_modulo10_prevuelo(entorno, caplog):
    caplog.set_level(logging.DEBUG)
    doble = DobleVertex('{"respuesta": "x", "citas": ["L13"]}')
    texto = f"Titular {CEDULA}, RUC {CEDULA_2}001, con guion 171003406-5, inválida {CEDULA_INVALIDA}."
    r = _consultar(texto, doble)
    enviado = doble.enviados[0]["contents"]
    assert enviado.count(motor.MARCA_CEDULA) == 3
    for fuga in (CEDULA, CEDULA_2, "171003406-5"):
        assert fuga not in enviado
        assert fuga not in caplog.text
        assert fuga not in repr(r.traza)
    assert CEDULA_INVALIDA in enviado
    assert r.cedulas_redactadas == 3
    assert not _fuga(doble, CEDULA)


def test_mutacion_sin_filtro_dlp_es_rojo(entorno, monkeypatch):
    """Quitar el filtro pre-vuelo debe detectarse: la marca no llega a Vertex."""
    monkeypatch.setattr(motor, "redactar_cedulas", lambda t: (t, 0))
    doble = DobleVertex('{"respuesta": "x", "citas": ["L13"]}')
    _consultar(f"Titular {CEDULA}", doble)
    assert _fuga(doble, CEDULA)


def test_respuesta_tambien_se_redacta(entorno):
    doble = DobleVertex(f'{{"respuesta": "El titular {CEDULA} tiene acceso.", "citas": ["L13"]}}')
    r = _consultar("acceso", doble)
    assert CEDULA not in r.respuesta and motor.MARCA_CEDULA in r.respuesta


@pytest.mark.parametrize("citas", ['[]', '["L999", "Art. 99"]'])
def test_sin_cita_del_corpus_declara_incertidumbre(entorno, citas):
    doble = DobleVertex(f'{{"respuesta": "Afirmación sin fundamento.", "citas": {citas}}}')
    r = _consultar("pregunta", doble)
    assert r.incertidumbre and r.respuesta == motor.INCERTIDUMBRE and r.citas == []


def test_creador_por_defecto_falla_cerrado():
    cache.vaciar_registro()
    cache.configurar_creador(None)
    with pytest.raises(ErrorNegocio) as exc:
        cache.obtener_o_crear("gemini-2.5-flash")
    assert "VTX_CACHE_NO_DISPONIBLE" in str(exc.value.__dict__) or "VTX_CACHE_NO_DISPONIBLE" in repr(exc.value)


def test_modelo_fuera_de_lista_falla_cerrado(entorno):
    with pytest.raises(ErrorNegocio):
        cache.obtener_o_crear("text-embedding-005")
    assert entorno.llamadas == []


SEPARADAS = ["1710.034.065", "1 7 1 0 0 3 4 0 6 5", "１７１００３４０６５",
             "١٧١٠٠٣٤٠٦٥"]


@pytest.mark.parametrize("variante", SEPARADAS)
def test_redacta_puntos_espacios_y_digitos_unicode(entorno, variante):
    doble = DobleVertex('{"respuesta": "x", "citas": ["L13"]}')
    r = _consultar(f"Titular {variante} pide acceso", doble)
    enviado = doble.enviados[0]["contents"]
    assert motor.MARCA_CEDULA in enviado and CEDULA not in enviado and variante not in enviado
    assert r.cedulas_redactadas == 1


@pytest.mark.parametrize("variante", SEPARADAS[:3])
def test_mutacion_patron_anterior_es_rojo(entorno, monkeypatch, variante):
    """Con el patrón de dc70ec35 (sin normalizar ni separadores internos) hay fuga."""
    import re

    anterior = re.compile(r"(?<!\d)(\d{9})[ -]?(\d)(001)?(?!\d)")

    def redactar_anterior(t):
        return anterior.sub(lambda m: motor.MARCA_CEDULA if motor.validar_cedula_ecuatoriana(m.group(1) + m.group(2)) else m.group(0), t), 0

    monkeypatch.setattr(motor, "redactar_cedulas", redactar_anterior)
    doble = DobleVertex('{"respuesta": "x", "citas": ["L13"]}')
    _consultar(f"Titular {variante}", doble)
    assert motor.MARCA_CEDULA not in doble.enviados[0]["contents"]


def test_filtro_que_falla_cierra_sin_llamar_a_vertex(entorno, monkeypatch, caplog):
    def roto(_t):
        raise RuntimeError(CEDULA)

    monkeypatch.setattr(motor, "redactar_cedulas", roto)
    doble = DobleVertex('{"respuesta": "x", "citas": ["L13"]}')
    with pytest.raises(svc.InferenciaNoDisponible):
        _consultar(f"Titular {CEDULA}", doble)
    assert doble.enviados == [] and CEDULA not in caplog.text


def test_respuesta_con_digitos_unicode_se_redacta(entorno):
    doble = DobleVertex(f'{{"respuesta": "Titular {SEPARADAS[2]}.", "citas": ["L13"]}}')
    r = _consultar("acceso", doble)
    assert motor.MARCA_CEDULA in r.respuesta and SEPARADAS[2] not in r.respuesta
