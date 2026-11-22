# ¤vertex-cache ¤arbitro
"""REG-03: compuertas de vectores, caché y corpus citable de la sala regulacion_rag. Dobles; sin red.

Mutaciones (governance/especificaciones/REG-03.md §5):
  m1. Quitar una de las cuatro funciones de la compuerta hace fallar `test_cuatro_compuertas_presentes`.
  m2. No vaciar el registro en `regenerar_cache_normativo` hace fallar `test_regenerar_cache_con_otro_hash`.
  m3. Tomar otro corpus en la caché o en `corpus_citable` hace fallar `test_corpus_citable_y_cache_del_mismo_corpus`.
"""
import asyncio

import pytest

from app_core.pasillo import inferencia as pasillo_inferencia
from app_core.pasillo import regulacion_rag as pasillo
from features.regulacion_rag import regulacion_rag_service as compuerta
from features.regulacion_rag.domain.corpus import CORPUS_NORMATIVO_OFICIAL, POR_ID, fundamento
from features.regulacion_rag.services import vertex_context_cache as cache


@pytest.fixture(autouse=True)
def inferencia_simulada(monkeypatch):
    llamadas = {"vectores": [], "caches": []}

    async def vectorizar(textos, modelo):
        llamadas["vectores"].append((list(textos), modelo))
        return [[float(len(t))] for t in textos]

    def crear_cache_contenido(modelo, contenido, ttl_segundos):
        llamadas["caches"].append((modelo, contenido, ttl_segundos))
        return f"cachedContents/c{len(llamadas['caches'])}", 100

    monkeypatch.setattr(pasillo_inferencia, "vectorizar", vectorizar)
    monkeypatch.setattr(pasillo_inferencia, "crear_cache_contenido", crear_cache_contenido)
    cache.configurar_creador(None)
    cache.vaciar_registro()
    yield llamadas
    cache.vaciar_registro()
    cache.configurar_creador(None)


def test_cuatro_compuertas_presentes(inferencia_simulada):
    vectores = asyncio.run(pasillo.vectorizar_fragmentos(["uno", "tres"], "text-embedding-005"))
    assert vectores == [[3.0], [4.0]]
    assert inferencia_simulada["vectores"] == [(["uno", "tres"], "text-embedding-005")]

    descriptor = pasillo.obtener_o_crear_cache_normativo("gemini-2.5-flash")
    assert descriptor.cache_name == "cachedContents/c1"
    assert descriptor.model_name == "gemini-2.5-flash"

    assert pasillo.pedir_regeneracion_cache(descriptor.corpus_sha256) is None
    assert pasillo.corpus_citable()


def test_regenerar_cache_con_otro_hash(inferencia_simulada):
    primera = pasillo.obtener_o_crear_cache_normativo("gemini-2.5-flash")
    segunda = pasillo.obtener_o_crear_cache_normativo("gemini-2.5-flash")
    assert primera == segunda
    assert len(inferencia_simulada["caches"]) == 1

    pasillo.pedir_regeneracion_cache(primera.corpus_sha256)  # mismo hash: la caché vigente se conserva
    assert pasillo.obtener_o_crear_cache_normativo("gemini-2.5-flash") == primera
    assert len(inferencia_simulada["caches"]) == 1

    pasillo.pedir_regeneracion_cache("0" * 64)  # otro hash: se crea otra
    tercera = pasillo.obtener_o_crear_cache_normativo("gemini-2.5-flash")
    assert len(inferencia_simulada["caches"]) == 2
    assert tercera.cache_name == "cachedContents/c2"


def test_corpus_citable_y_cache_del_mismo_corpus(inferencia_simulada):
    citable = pasillo.corpus_citable()
    assert set(citable) == {n.id for n in CORPUS_NORMATIVO_OFICIAL}
    assert all(citable[k] == fundamento(k) for k in citable)

    descriptor = pasillo.obtener_o_crear_cache_normativo("gemini-2.5-pro")
    assert descriptor.corpus_sha256 == cache.huella_corpus([POR_ID[k] for k in citable])
    assert descriptor.corpus_sha256 == cache.huella_corpus(CORPUS_NORMATIVO_OFICIAL)


def test_sin_inferencia_falla_cerrado(monkeypatch):
    from app_core.errors import ErrorNegocio
    from features.inferencia.domain.errores import InferenciaNoDisponible

    async def vectorizar(textos, modelo):
        raise InferenciaNoDisponible("x")

    def crear(modelo, contenido, ttl):
        raise InferenciaNoDisponible("x")

    monkeypatch.setattr(pasillo_inferencia, "vectorizar", vectorizar)
    monkeypatch.setattr(pasillo_inferencia, "crear_cache_contenido", crear)
    with pytest.raises(InferenciaNoDisponible):
        asyncio.run(pasillo.vectorizar_fragmentos(["a"], "text-embedding-005"))
    with pytest.raises(ErrorNegocio):
        pasillo.obtener_o_crear_cache_normativo("gemini-2.5-flash")
