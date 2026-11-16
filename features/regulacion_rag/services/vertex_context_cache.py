# ¤vertex-cache ¤gemini-vertex ¤regulation-code
"""Caché de contexto de Vertex AI para el corpus normativo público (VTX-01).

Solo se cachea normativa pública del corpus cerrado: nunca la consulta ni datos del tenant.
La caché se identifica por `corpus_sha256`; si el corpus cambia (reforma), se crea otra.

Límite conocido: el registro vive en memoria del proceso. En Cloud Run cada instancia crea
su propia caché. La creación real en Vertex depende de una ficha de la sala inferencia; hasta
entonces el creador por defecto falla cerrado (VTX_CACHE_NO_DISPONIBLE).
"""
from __future__ import annotations

import hashlib
import threading
import time
from dataclasses import dataclass
from typing import Callable, Iterable, Protocol

from app_core.errors import ErrorNegocio
from features.regulacion_rag.domain.corpus import CORPUS_NORMATIVO_OFICIAL, CORPUS_VERSION
from features.regulacion_rag.domain.errores import VTX_CACHE_NO_DISPONIBLE
from features.regulacion_rag.domain.models import UnidadNormativa

MODELOS_CACHE: frozenset[str] = frozenset({"gemini-2.5-pro", "gemini-2.5-flash"})
TTL_POR_DEFECTO = 3600


@dataclass(frozen=True)
class VertexCorpusCacheDescriptor:
    cache_name: str
    model_name: str
    corpus_version: str
    corpus_sha256: str
    ttl_seconds: int
    token_count: int


class CreadorCacheContenido(Protocol):
    """Puerto: crea un CachedContent con `contenido` y devuelve (cache_name, token_count)."""

    def __call__(self, modelo: str, contenido: str, ttl_seconds: int) -> tuple[str, int]: ...


def _creador_no_disponible(modelo: str, contenido: str, ttl_seconds: int) -> tuple[str, int]:
    raise ErrorNegocio(VTX_CACHE_NO_DISPONIBLE)


def texto_canonico(corpus: Iterable[UnidadNormativa]) -> str:
    """Texto determinista del corpus público; base del hash y del contenido cacheado."""
    lineas = [
        f"[{n.id}] {n.numero_o_titulo}, {n.articulo_o_seccion} · {n.titulo} · {n.version}\n{n.texto_oficial}"
        for n in sorted(corpus, key=lambda n: n.id)
    ]
    return "\n\n".join(lineas)


def huella_corpus(corpus: Iterable[UnidadNormativa]) -> str:
    return hashlib.sha256(texto_canonico(corpus).encode("utf-8")).hexdigest()


_creador: CreadorCacheContenido = _creador_no_disponible
_registro: dict[tuple[str, str], tuple[VertexCorpusCacheDescriptor, float]] = {}
_candado = threading.Lock()


def configurar_creador(creador: CreadorCacheContenido | None) -> None:
    """Conecta el puerto (doble en pruebas; adaptador de inferencia cuando exista). None restaura el cerrado."""
    global _creador
    _creador = creador or _creador_no_disponible


def vaciar_registro() -> None:
    with _candado:
        _registro.clear()


def obtener_o_crear(
    modelo: str,
    *,
    corpus: list[UnidadNormativa] | None = None,
    corpus_version: str = CORPUS_VERSION,
    ttl_seconds: int = TTL_POR_DEFECTO,
    reloj: Callable[[], float] = time.monotonic,
) -> VertexCorpusCacheDescriptor:
    """Reutiliza la caché vigente del mismo (modelo, corpus_sha256); si no hay, la crea. Falla cerrada."""
    if modelo not in MODELOS_CACHE:
        raise ErrorNegocio(VTX_CACHE_NO_DISPONIBLE)
    unidades = CORPUS_NORMATIVO_OFICIAL if corpus is None else corpus
    contenido = texto_canonico(unidades)
    sha = hashlib.sha256(contenido.encode("utf-8")).hexdigest()
    clave = (modelo, sha)
    with _candado:
        vigente = _registro.get(clave)
        ahora = reloj()
        if vigente is not None and vigente[1] > ahora:
            return vigente[0]
        try:
            nombre, tokens = _creador(modelo, contenido, ttl_seconds)
        except ErrorNegocio:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ErrorNegocio(VTX_CACHE_NO_DISPONIBLE) from exc
        if not isinstance(nombre, str) or not nombre.strip():
            raise ErrorNegocio(VTX_CACHE_NO_DISPONIBLE)
        descriptor = VertexCorpusCacheDescriptor(
            cache_name=nombre.strip(),
            model_name=modelo,
            corpus_version=corpus_version,
            corpus_sha256=sha,
            ttl_seconds=ttl_seconds,
            token_count=int(tokens),
        )
        # Una reforma deja obsoletas las cachés del mismo modelo con otro hash.
        for otra in [k for k in _registro if k[0] == modelo and k[1] != sha]:
            del _registro[otra]
        _registro[clave] = (descriptor, ahora + ttl_seconds)
        return descriptor
