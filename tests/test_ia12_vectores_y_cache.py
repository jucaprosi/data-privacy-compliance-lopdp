# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤vertex-cache ¤arbitro
"""IA-12: vectores y caché de contexto de Vertex AI por la compuerta de inferencia. Cliente falso; sin red.

Mutaciones (governance/especificaciones/IA-12.md §5):
  m1. Si la compuerta devuelve menos vectores que textos sin error, falla `test_vectorizar_un_vector_por_texto`.
  m2. Si la compuerta acepta una caché con nombre vacío, falla `test_crear_cache_contenido`.
"""
import asyncio
from types import SimpleNamespace

import pytest

from app_core.errors import ErrorNegocio
from features.inferencia import inferencia_service as svc
from features.inferencia.domain.errores import InferenciaNoDisponible
from features.inferencia.domain.modelos_permitidos import MODELOS_EMBEDDING


class ModelosFalsos:
    def __init__(self, recortar: int = 0):
        self.llamadas: list[dict] = []
        self.recortar = recortar

    async def embed_content(self, **kw):
        self.llamadas.append(kw)
        textos = kw["contents"]
        vectores = [SimpleNamespace(values=[float(i), float(len(t))]) for i, t in enumerate(textos)]
        if self.recortar:
            vectores = vectores[: -self.recortar]
        return SimpleNamespace(embeddings=vectores)


class CachesFalsas:
    def __init__(self, nombre="cachedContents/abc123", tokens=4321):
        self.llamadas: list[dict] = []
        self.nombre = nombre
        self.tokens = tokens

    def create(self, **kw):
        self.llamadas.append(kw)
        return SimpleNamespace(name=self.nombre, usage_metadata=SimpleNamespace(total_token_count=self.tokens))


class ClienteFalso:
    def __init__(self, recortar: int = 0, **kw_cache):
        self.modelos = ModelosFalsos(recortar)
        self.aio = SimpleNamespace(models=self.modelos)
        self.caches = CachesFalsas(**kw_cache)


@pytest.fixture(autouse=True)
def entorno(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "proyecto-prueba")
    monkeypatch.setenv("VERTEX_LOCATION", "us-central1")
    monkeypatch.setattr(svc, "_cliente", None)
    consumos: list[str] = []

    async def consumir(org):
        consumos.append(org)

    svc.inyectar_consumidor_de_prueba(consumir)
    yield consumos
    svc.inyectar_cliente_de_prueba(None)
    svc.inyectar_consumidor_de_prueba(None)


def _vectorizar(cliente, textos, modelo="text-embedding-005"):
    svc.inyectar_cliente_de_prueba(cliente)
    return asyncio.run(svc.vectorizar(textos, modelo))


def test_vectorizar_un_vector_por_texto(entorno):
    c = ClienteFalso()
    textos = ["uno", "dos dos", "tres tres tres"]
    vectores = _vectorizar(c, textos)
    assert vectores == [[0.0, 3.0], [1.0, 7.0], [2.0, 14.0]]
    assert c.modelos.llamadas == [{"model": "text-embedding-005", "contents": textos}]
    assert entorno == []  # R3: no consume el tope de ninguna organización

    # m1: menos vectores que textos debe fallar cerrado
    with pytest.raises(InferenciaNoDisponible):
        _vectorizar(ClienteFalso(recortar=1), textos)


def test_modelo_de_vectores_fuera_de_lista():
    assert MODELOS_EMBEDDING == ("text-embedding-005",)
    c = ClienteFalso()
    for modelo in ("gemini-2.5-flash", "text-embedding-004", ""):
        with pytest.raises(ErrorNegocio) as e:
            _vectorizar(c, ["texto"], modelo=modelo)
        assert e.value.code == "IA_MODELO_EMBEDDING_NO_PERMITIDO"
    assert c.modelos.llamadas == []


def test_crear_cache_contenido(entorno):
    c = ClienteFalso()
    svc.inyectar_cliente_de_prueba(c)
    assert svc.crear_cache_contenido("gemini-2.5-pro", "corpus público", 3600) == ("cachedContents/abc123", 4321)
    llamada = c.caches.llamadas[0]
    assert llamada["model"] == "gemini-2.5-pro"
    assert llamada["config"].contents and llamada["config"].ttl == "3600s"
    assert entorno == []

    # m2: un nombre vacío debe fallar cerrado
    for nombre in ("", "   ", None):
        svc.inyectar_cliente_de_prueba(ClienteFalso(nombre=nombre))
        with pytest.raises(InferenciaNoDisponible):
            svc.crear_cache_contenido("gemini-2.5-pro", "corpus público", 3600)


def test_sin_configuracion_falla_cerrada(monkeypatch):
    c = ClienteFalso()
    svc.inyectar_cliente_de_prueba(c)
    monkeypatch.delenv("VERTEX_LOCATION")
    with pytest.raises(InferenciaNoDisponible):
        asyncio.run(svc.vectorizar(["texto"], "text-embedding-005"))
    with pytest.raises(InferenciaNoDisponible):
        svc.crear_cache_contenido("gemini-2.5-pro", "corpus", 60)
    assert c.modelos.llamadas == [] and c.caches.llamadas == []


def test_errores_del_cliente_fallan_cerradas():
    class Roto(ClienteFalso):
        def __init__(self):
            super().__init__()

            async def embed_content(**kw):
                raise RuntimeError("403 PERMISSION_DENIED")

            def create(**kw):
                raise RuntimeError("403 PERMISSION_DENIED")

            self.aio = SimpleNamespace(models=SimpleNamespace(embed_content=embed_content))
            self.caches = SimpleNamespace(create=create)

    with pytest.raises(InferenciaNoDisponible):
        _vectorizar(Roto(), ["texto"])
    with pytest.raises(InferenciaNoDisponible):
        svc.crear_cache_contenido("gemini-2.5-pro", "corpus", 60)


def test_pasillo_reexporta_vectores_y_cache():
    from app_core.pasillo import inferencia

    c = ClienteFalso()
    svc.inyectar_cliente_de_prueba(c)
    assert asyncio.run(inferencia.vectorizar(["a", "bb"], "text-embedding-005")) == [[0.0, 1.0], [1.0, 2.0]]
    assert inferencia.crear_cache_contenido("gemini-2.5-flash", "corpus", 120) == ("cachedContents/abc123", 4321)
