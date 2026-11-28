# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤gemini-vertex ¤arbitro ¤vertex-cache
"""Compuerta de inferencia Gemini en Vertex AI sin clave (IA-03): DLP previo, tope de organización, falla cerrada."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Callable

from pydantic import BaseModel

from app_core.dlp_sanitizer import sanitizar_texto_pii
from app_core.errors import CodigoErrorNegocio, ErrorNegocio
from features.inferencia.domain.errores import MOTIVO_NEUTRO, InferenciaNoDisponible
from features.inferencia.domain.modelos_permitidos import (
    MODELO_EMBEDDING,
    MODELO_GENERACION,
    MODELOS_EMBEDDING,
    MODELOS_PERMITIDOS,
)
from features.inferencia.domain.prompts import PromptVersionado
from features.inferencia.domain.regiones import UBICACION_POR_REGION
from features.inferencia.domain.traza import Traza
from features.inferencia.services import cliente_vertex

logger = logging.getLogger(__name__)

PLAZO_TOTAL_S = 140  # IA-18 R3: por debajo de los 150 s del proxy de la web y del `--timeout` de Cloud Run
MARGEN_S = 5  # IA-18 R5: lo que se resta al plazo de cada petición
CODIGOS_TRANSITORIOS = frozenset({429, 503, 504})  # IA-18 R2
_reloj = time.monotonic  # las pruebas lo sustituyen: nunca se duerme de verdad

__all__ = [
    "EstadoProveedor",
    "InferenciaNoDisponible",
    "MODELO_EMBEDDING",
    "MODELO_GENERACION",
    "MODELOS_EMBEDDING",
    "MODELOS_PERMITIDOS",
    "MOTIVO_NEUTRO",
    "estado",
    "PromptVersionado",
    "Traza",
    "generar_estructurado",
    "generar_trazado",
    "registrar_traza",
    "TrazaTranscripcion",
    "transcribir_pdf",
    "generar_trazado_sin_tope",
    "vectorizar",
    "crear_cache_contenido",
    "inyectar_cliente_de_prueba",
    "inyectar_consumidor_de_prueba",
]


IA_MODELO_EMBEDDING_NO_PERMITIDO = CodigoErrorNegocio(
    "IA_MODELO_EMBEDDING_NO_PERMITIDO", 422, "El modelo de vectores no está en la lista permitida."
)


@dataclass(frozen=True)
class EstadoProveedor:
    disponible: bool
    proveedor: str | None
    modelo: str | None
    motivo: str | None
    region: str | None = None
    ubicacion: str | None = None


_cliente = None
_cliente_vectores = None
_cliente_de_prueba = None
_consumidor_de_prueba: Callable | None = None


def inyectar_cliente_de_prueba(cliente) -> None:
    """SOLO PARA PRUEBAS: cliente falso."""
    global _cliente_de_prueba
    _cliente_de_prueba = cliente


def inyectar_consumidor_de_prueba(consumidor: Callable | None) -> None:
    """SOLO PARA PRUEBAS: sustituye el consumo del tope (corrutina `f(org_id)`)."""
    global _consumidor_de_prueba
    _consumidor_de_prueba = consumidor


def _etiquetar(region: str) -> tuple[str, str]:
    ubicacion = UBICACION_POR_REGION.get(region)
    if ubicacion is None:
        raise InferenciaNoDisponible()
    return region, ubicacion


def _region_valida() -> tuple[str, str]:
    """(región de generación, país) o InferenciaNoDisponible si falta o no tiene etiqueta (IA-13 R2 y R4)."""
    _, region = cliente_vertex.configuracion()
    return _etiquetar(region)


def _region_vectores_valida() -> tuple[str, str]:
    """(región de vectores, país) o InferenciaNoDisponible; no depende de la de generación (IA-13 R3)."""
    _, region = cliente_vertex.configuracion_embedding()
    return _etiquetar(region)


def estado() -> EstadoProveedor:
    """Sin conectar: solo mira configuración y mapa de regiones. `region` y `ubicacion` son las de generación."""
    try:
        region, ubicacion = _region_valida()
    except InferenciaNoDisponible:
        return EstadoProveedor(False, None, None, MOTIVO_NEUTRO)
    return EstadoProveedor(True, "vertex-ai", None, None, region, ubicacion)


def _obtener_cliente():
    global _cliente
    _region_valida()
    if _cliente_de_prueba is not None:
        return _cliente_de_prueba
    if _cliente is None:
        _cliente = cliente_vertex.crear_cliente()
    return _cliente


def _obtener_cliente_vectores():
    global _cliente_vectores
    _region_vectores_valida()
    if _cliente_de_prueba is not None:
        return _cliente_de_prueba
    if _cliente_vectores is None:
        _cliente_vectores = cliente_vertex.crear_cliente(vectores=True, plazo_ms=(PLAZO_TOTAL_S - MARGEN_S) * 1000)
    return _cliente_vectores


def _transitorio(exc: Exception) -> bool:
    from google.genai import errors

    return isinstance(exc, errors.APIError) and getattr(exc, "code", None) in CODIGOS_TRANSITORIOS


def _describir(exc: Exception) -> str:
    """Tipo, código y estado de la excepción. Nunca su mensaje: puede traer el prompt o datos personales."""
    from google.genai import errors

    partes = [type(exc).__name__]
    if isinstance(exc, errors.APIError):
        partes += ["code=%s" % getattr(exc, "code", None), "status=%s" % getattr(exc, "status", None)]
    return " ".join(partes)


def _registrar_uso(etiqueta: str, respuesta, intento: int, duracion: float) -> None:
    """IA-18 R9: tokens de `usage_metadata` de un intento correcto. Solo cifras: nunca el prompt ni la respuesta."""
    uso = getattr(respuesta, "usage_metadata", None)
    if uso is None:
        return
    cifras = []
    for campo in ("prompt_token_count", "candidates_token_count", "thoughts_token_count"):
        valor = getattr(uso, campo, None)
        if isinstance(valor, int) and not isinstance(valor, bool):
            cifras.append("%s=%d" % (campo, valor))
    logger.info("%s: uso %s intento=%d duracion=%.1fs", etiqueta, " ".join(cifras), intento, duracion)


async def _con_plazo(etiqueta: str, llamar):
    """IA-18 R1-R3 y R5: `llamar(plazo_ms)` con un reintento solo ante 429/503/504 y solo si cabe en el plazo total."""
    inicio = _reloj()
    intento = 1
    while True:
        desde = _reloj()
        plazo_ms = max(int((PLAZO_TOTAL_S - (desde - inicio) - MARGEN_S) * 1000), 0)
        try:
            salida = await llamar(plazo_ms)
            _registrar_uso(etiqueta, salida[1], intento, _reloj() - desde)
            return salida
        except Exception as exc:  # noqa: BLE001
            duracion = _reloj() - desde
            logger.warning("%s: %s intento=%d duracion=%.1fs", etiqueta, _describir(exc), intento, duracion)
            if intento == 1 and _transitorio(exc):
                if PLAZO_TOTAL_S - (_reloj() - inicio) >= duracion:
                    intento = 2
                    continue
                logger.warning("%s: reintento omitido por plazo", etiqueta)
            raise


async def _consumir_tope(org_id: str) -> None:
    if _consumidor_de_prueba is not None:
        await _consumidor_de_prueba(org_id)
        return
    from app_core.db.session import async_session_factory, fijar_contexto_rls
    from app_core.limites.tope_organizacion import consumir_generacion

    async with async_session_factory() as session:
        await fijar_contexto_rls(session, org_id, "inferencia")
        await consumir_generacion(session, org_id)
        await session.commit()


async def _generar(
    sistema: str, usuario: str, esquema: type[BaseModel], *, modelo: str, org_id: str
) -> tuple[BaseModel, object]:
    """Núcleo común: (resultado validado, respuesta cruda). Falla cerrada: sin plan simulado ni respaldo."""
    if modelo not in MODELOS_PERMITIDOS:
        raise InferenciaNoDisponible()
    await _consumir_tope(org_id)  # ErrorNegocio 429 si se agotó; no llega al cliente
    sistema_seguro = sanitizar_texto_pii(sistema)
    usuario_seguro = sanitizar_texto_pii(usuario)
    try:
        cliente = _obtener_cliente()

        async def llamar(plazo_ms: int):
            respuesta = await cliente_vertex.generar_json(
                cliente, modelo, sistema_seguro, usuario_seguro, esquema, plazo_ms=plazo_ms
            )
            texto = getattr(respuesta, "text", None)
            if not texto:
                raise ValueError("respuesta vacía")
            return esquema.model_validate_json(texto), respuesta

        return await _con_plazo("Fallo de inferencia Vertex", llamar)
    except InferenciaNoDisponible:
        raise
    except Exception as exc:  # noqa: BLE001
        raise InferenciaNoDisponible() from exc


async def generar_estructurado(
    sistema: str, usuario: str, esquema: type[BaseModel], *, modelo: str, org_id: str
) -> BaseModel:
    """Una generación estructurada validada contra `esquema`. Se retira cuando IA-05 e IA-06 usen `generar_trazado`."""
    resultado, _ = await _generar(sistema, usuario, esquema, modelo=modelo, org_id=org_id)
    return resultado


async def generar_trazado(
    prompt: PromptVersionado,
    valores: dict,
    esquema: type[BaseModel],
    *,
    modelo: str,
    org_id: str,
    corpus_sha256: str | None = None,
) -> tuple[BaseModel, Traza]:
    """Generación con traza (invariante 64). Falla cerrada si Vertex no devuelve `model_version`."""
    usuario = prompt.renderizar(valores)
    resultado, respuesta = await _generar(prompt.sistema, usuario, esquema, modelo=modelo, org_id=org_id)
    version = getattr(respuesta, "model_version", None)
    if not isinstance(version, str) or not version.strip():
        logger.warning("Vertex no devolvió la versión del modelo")
        raise InferenciaNoDisponible()
    return resultado, Traza(
        sala=prompt.sala,
        tenant_id=org_id,
        modelo_version=version.strip(),
        modelo_solicitado=modelo,
        prompt_id=prompt.id,
        prompt_version=prompt.version,
        corpus_sha256=corpus_sha256,
    )


async def registrar_traza(session, traza: Traza, entidad: str, entidad_id: str) -> None:
    """Escribe la traza en la sesión del llamador, en la misma transacción que el resultado: no hace commit.

    La sesión ya debe traer el contexto RLS del tenant; la política rechaza cualquier otro `tenant_id`.
    """
    from sqlalchemy import text

    await session.execute(
        text(
            "INSERT INTO trazas_ia (id, tenant_id, sala, entidad, entidad_id, modelo_version, modelo_solicitado, "
            "prompt_id, prompt_version, corpus_sha256) "
            "VALUES (:id, :tenant_id, :sala, :entidad, :entidad_id, :modelo_version, :modelo_solicitado, "
            ":prompt_id, :prompt_version, :corpus_sha256)"
        ),
        {
            "id": traza.id, "tenant_id": traza.tenant_id, "sala": traza.sala, "entidad": entidad,
            "entidad_id": entidad_id, "modelo_version": traza.modelo_version,
            "modelo_solicitado": traza.modelo_solicitado, "prompt_id": traza.prompt_id,
            "prompt_version": traza.prompt_version, "corpus_sha256": traza.corpus_sha256,
        },
    )


# NORM-06 · Transcripción de PDF escaneados. Corpus normativo común sin datos personales: no consume tope (IA-12 R3).


@dataclass(frozen=True)
class TrazaTranscripcion:
    modelo_version: str  # lo que devuelve Vertex, nunca el alias
    modelo_solicitado: str
    prompt_id: str
    prompt_version: int


async def transcribir_pdf(pdf: bytes, prompt: PromptVersionado, *, modelo: str) -> tuple[str, TrazaTranscripcion]:
    """Texto del PDF y su traza. Falla cerrada: modelo no permitido, región sin etiqueta, vacío o sin `model_version`."""
    if modelo not in MODELOS_PERMITIDOS:
        raise InferenciaNoDisponible()
    try:
        cliente = _obtener_cliente()  # comprueba la región de generación (IA-17)

        async def llamar(plazo_ms: int):
            respuesta = await cliente_vertex.transcribir(
                cliente, modelo, prompt.sistema, prompt.renderizar({}), pdf, plazo_ms=plazo_ms
            )
            texto = getattr(respuesta, "text", None)
            if not isinstance(texto, str) or not texto.strip():
                raise ValueError("respuesta vacía")
            return texto, respuesta

        texto, respuesta = await _con_plazo("Fallo de transcripción Vertex", llamar)
    except InferenciaNoDisponible:
        raise
    except Exception as exc:  # noqa: BLE001
        raise InferenciaNoDisponible() from exc
    version = getattr(respuesta, "model_version", None)
    if not isinstance(version, str) or not version.strip():
        logger.warning("Vertex no devolvió la versión del modelo")
        raise InferenciaNoDisponible()
    return texto.strip(), TrazaTranscripcion(version.strip(), modelo, prompt.id, prompt.version)


# BIB-406 R2c · Generación trazada para el catálogo común de la plataforma (plantillas, sin datos personales).
# Mismo patrón que `transcribir_pdf`: no consume el tope de ninguna organización (IA-12 R3, NORM-06 R2).
async def generar_trazado_sin_tope(
    prompt: PromptVersionado, valores: dict, esquema: type[BaseModel], *, modelo: str
) -> tuple[BaseModel, TrazaTranscripcion]:
    """Resultado validado y su traza. Falla cerrada: modelo no permitido, respuesta inválida o sin `model_version`."""
    if modelo not in MODELOS_PERMITIDOS:
        raise InferenciaNoDisponible()
    sistema_seguro = sanitizar_texto_pii(prompt.sistema)
    usuario_seguro = sanitizar_texto_pii(prompt.renderizar(valores))
    try:
        cliente = _obtener_cliente()

        async def llamar(plazo_ms: int):
            respuesta = await cliente_vertex.generar_json(
                cliente, modelo, sistema_seguro, usuario_seguro, esquema, plazo_ms=plazo_ms
            )
            texto = getattr(respuesta, "text", None)
            if not texto:
                raise ValueError("respuesta vacía")
            return esquema.model_validate_json(texto), respuesta

        resultado, respuesta = await _con_plazo("Fallo de inferencia Vertex", llamar)
    except InferenciaNoDisponible:
        raise
    except Exception as exc:  # noqa: BLE001
        raise InferenciaNoDisponible() from exc
    version = getattr(respuesta, "model_version", None)
    if not isinstance(version, str) or not version.strip():
        logger.warning("Vertex no devolvió la versión del modelo")
        raise InferenciaNoDisponible()
    return resultado, TrazaTranscripcion(version.strip(), modelo, prompt.id, prompt.version)


# IA-12 · Vectores y caché de contexto. R3: corpus normativo común sin datos personales, no consume tope.


async def vectorizar(textos: list[str], modelo: str) -> list[list[float]]:
    """Un vector por texto, en el mismo orden. Falla cerrada si el recuento no cuadra."""
    if modelo not in MODELOS_EMBEDDING:
        raise ErrorNegocio(IA_MODELO_EMBEDDING_NO_PERMITIDO)  # no llega al cliente
    lista = list(textos)
    cliente = _obtener_cliente_vectores()  # InferenciaNoDisponible sin VERTEX_LOCATION_EMBEDDING
    if not lista:
        return []
    try:
        vectores = await cliente_vertex.vectorizar(cliente, modelo, lista)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Fallo de vectores Vertex: %s", type(exc).__name__)
        raise InferenciaNoDisponible() from exc
    if len(vectores) != len(lista) or any(not v for v in vectores):
        logger.warning("Vertex devolvió %d vectores para %d textos", len(vectores), len(lista))
        raise InferenciaNoDisponible()
    return vectores


def crear_cache_contenido(modelo: str, contenido: str, ttl_segundos: int) -> tuple[str, int]:
    """(nombre de la caché, tokens). Cumple el puerto `(modelo, contenido, ttl_seconds) -> (nombre, tokens)`."""
    if modelo not in MODELOS_PERMITIDOS:
        raise InferenciaNoDisponible()
    cliente = _obtener_cliente()  # InferenciaNoDisponible sin configuración
    try:
        nombre, tokens = cliente_vertex.crear_cache(cliente, modelo, contenido, ttl_segundos)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Fallo de caché Vertex: %s", type(exc).__name__)
        raise InferenciaNoDisponible() from exc
    if not isinstance(nombre, str) or not nombre.strip():
        logger.warning("Vertex devolvió una caché sin nombre")
        raise InferenciaNoDisponible()
    if isinstance(tokens, bool) or not isinstance(tokens, int) or tokens < 0:
        logger.warning("Vertex devolvió una caché sin recuento de tokens")
        raise InferenciaNoDisponible()
    return nombre.strip(), tokens
