# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤vertex-cache ¤arbitro
"""IA-12: vectores y caché de contexto de Vertex AI por la compuerta de inferencia. Cliente falso; sin red.

Mutaciones (governance/especificaciones/IA-12.md §5):
  m1. Si la compuerta devuelve menos vectores que textos sin error, falla `test_vectorizar_un_vector_por_texto`.
  m2. Si la compuerta acepta una caché con nombre vacío, falla `test_crear_cache_contenido`.
  IA-13 m3. Si los vectores usan `VERTEX_LOCATION`, falla `test_vectores_sin_su_ubicacion_y_la_generacion_sigue`.
"""
import asyncio
from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from app_core.errors import ErrorNegocio
from features.inferencia import inferencia_service as svc
from features.inferencia.domain.errores import InferenciaNoDisponible
from features.inferencia.domain.modelos_permitidos import MODELO_EMBEDDING, MODELO_GENERACION, MODELOS_EMBEDDING
from features.inferencia.services import cliente_vertex


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

    async def generate_content(self, **kw):
        self.llamadas.append(kw)
        return SimpleNamespace(text='{"estado": "ok"}')


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
    monkeypatch.setenv("VERTEX_LOCATION", "us")
    monkeypatch.setenv("VERTEX_LOCATION_EMBEDDING", "us-central1")
    monkeypatch.setattr(svc, "_cliente", None)
    monkeypatch.setattr(svc, "_cliente_vectores", None)
    consumos: list[str] = []

    async def consumir(org):
        consumos.append(org)

    svc.inyectar_consumidor_de_prueba(consumir)
    yield consumos
    svc.inyectar_cliente_de_prueba(None)
    svc.inyectar_consumidor_de_prueba(None)


def _vectorizar(cliente, textos, modelo=MODELO_EMBEDDING):
    svc.inyectar_cliente_de_prueba(cliente)
    return asyncio.run(svc.vectorizar(textos, modelo))


def test_vectorizar_un_vector_por_texto(entorno):
    c = ClienteFalso()
    textos = ["uno", "dos dos", "tres tres tres"]
    vectores = _vectorizar(c, textos)
    assert vectores == [[0.0, 3.0], [1.0, 7.0], [2.0, 14.0]]
    assert c.modelos.llamadas == [{"model": MODELO_EMBEDDING, "contents": textos}]
    assert entorno == []  # R3: no consume el tope de ninguna organización

    # m1: menos vectores que textos debe fallar cerrado
    with pytest.raises(InferenciaNoDisponible):
        _vectorizar(ClienteFalso(recortar=1), textos)


def test_modelo_de_vectores_fuera_de_lista():
    assert MODELOS_EMBEDDING == ("text-embedding-005",)
    c = ClienteFalso()
    for modelo in (MODELO_GENERACION, "text-embedding-004", ""):
        with pytest.raises(ErrorNegocio) as e:
            _vectorizar(c, ["texto"], modelo=modelo)
        assert e.value.code == "IA_MODELO_EMBEDDING_NO_PERMITIDO"
    assert c.modelos.llamadas == []


def test_crear_cache_contenido(entorno):
    c = ClienteFalso()
    svc.inyectar_cliente_de_prueba(c)
    assert svc.crear_cache_contenido(MODELO_GENERACION, "corpus público", 3600) == ("cachedContents/abc123", 4321)
    llamada = c.caches.llamadas[0]
    assert llamada["model"] == MODELO_GENERACION
    assert llamada["config"].contents and llamada["config"].ttl == "3600s"
    assert entorno == []

    # m2: un nombre vacío debe fallar cerrado
    for nombre in ("", "   ", None):
        svc.inyectar_cliente_de_prueba(ClienteFalso(nombre=nombre))
        with pytest.raises(InferenciaNoDisponible):
            svc.crear_cache_contenido(MODELO_GENERACION, "corpus público", 3600)


class Esquema(BaseModel):
    estado: str


def test_vectores_sin_su_ubicacion_y_la_generacion_sigue(monkeypatch):
    """IA-13 R3 y m3: sin `VERTEX_LOCATION_EMBEDDING` no hay vectores aunque haya `VERTEX_LOCATION`."""
    c = ClienteFalso()
    svc.inyectar_cliente_de_prueba(c)
    monkeypatch.delenv("VERTEX_LOCATION_EMBEDDING")
    with pytest.raises(InferenciaNoDisponible):
        asyncio.run(svc.vectorizar(["texto"], MODELO_EMBEDDING))
    assert c.modelos.llamadas == []
    r = asyncio.run(svc.generar_estructurado("s", "u", Esquema, modelo=MODELO_GENERACION, org_id="org-1"))
    assert r == Esquema(estado="ok") and c.modelos.llamadas[0]["model"] == MODELO_GENERACION


def test_cliente_de_vectores_en_su_ubicacion(monkeypatch):
    """IA-13 R3: el cliente de vectores va a `us-central1` y el de generación a `us`."""
    capturado: list[dict] = []

    class Fake:
        def __init__(self, **kw):
            capturado.append(kw)

    import google.genai as genai

    monkeypatch.setattr(genai, "Client", Fake)
    cliente_vertex.crear_cliente(vectores=True)
    cliente_vertex.crear_cliente()
    assert [kw["location"] for kw in capturado] == ["us-central1", "us"]


def test_sin_configuracion_falla_cerrada(monkeypatch):
    c = ClienteFalso()
    svc.inyectar_cliente_de_prueba(c)
    monkeypatch.delenv("VERTEX_LOCATION")
    monkeypatch.delenv("VERTEX_LOCATION_EMBEDDING")
    with pytest.raises(InferenciaNoDisponible):
        asyncio.run(svc.vectorizar(["texto"], MODELO_EMBEDDING))
    with pytest.raises(InferenciaNoDisponible):
        svc.crear_cache_contenido(MODELO_GENERACION, "corpus", 60)
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
        svc.crear_cache_contenido(MODELO_GENERACION, "corpus", 60)


def test_pasillo_reexporta_vectores_y_cache():
    from app_core.pasillo import inferencia

    c = ClienteFalso()
    svc.inyectar_cliente_de_prueba(c)
    assert asyncio.run(inferencia.vectorizar(["a", "bb"], MODELO_EMBEDDING)) == [[0.0, 1.0], [1.0, 2.0]]
    assert inferencia.crear_cache_contenido(MODELO_GENERACION, "corpus", 120) == ("cachedContents/abc123", 4321)
