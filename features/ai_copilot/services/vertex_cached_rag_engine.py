# ¤copiloto-ia ¤gemini-vertex ¤vertex-cache
"""Copiloto normativo sobre Gemini en Vertex AI con filtro DLP pre-vuelo y citación cerrada (VTX-01).

Orden fijo: (1) redacción de cédulas ecuatorianas válidas por Módulo 10, (2) descriptor de la caché
del corpus público, (3) inferencia por la compuerta de inferencia, (4) validación de citas contra
el corpus; sin cita válida devuelve una declaración de incertidumbre. La compuerta aplica además
su propio DLP como segunda capa. Ni el texto de la consulta ni la cédula se registran en logs.
"""
from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Callable, Literal

from pydantic import BaseModel, Field

from app_core.app_service import validar_cedula_ecuatoriana

logger = logging.getLogger(__name__)

MARCA_CEDULA = "[CEDULA-REDACTADA]"
MODELO_POR_MODO = {"dictamen": "gemini-2.5-pro", "rapida": "gemini-2.5-flash"}
INCERTIDUMBRE = (
    "No encuentro en el corpus normativo vigente un artículo que respalde una respuesta. "
    "Consulte al delegado de protección de datos."
)
PROMPT_ID = "ai_copilot.copiloto_normativo_cache"
PROMPT_VERSION = 1
SISTEMA = (
    "Eres un copiloto normativo de protección de datos personales de Ecuador. Responde solo con base en "
    "el corpus normativo indicado. Cita cada fundamento con su identificador del corpus en `citas`. "
    "Si el corpus no respalda la respuesta, deja `citas` vacía. No inventes artículos ni numerales."
)
PLANTILLA = (
    "Versión del corpus: {corpus_version} (sha256 {corpus_sha256}).\n"
    "Identificadores citables:\n{indice}\n\nConsulta:\n{consulta}"
)

# Diez dígitos con separador opcional (espacio, punto o guion) entre cualquiera de ellos; también el
# RUC de persona natural (+001). Se busca sobre texto con dígitos ya convertidos a ASCII.
_CANDIDATA = re.compile(r"(?<![0-9])(?:[0-9][ .\-]?){9}[0-9](?:[ .\-]?001)?(?![0-9])", re.ASCII)
_SEPARADORES = re.compile(r"[ .\-]")


def _digitos_ascii(texto: str) -> str:
    """Todo dígito decimal Unicode (ancho completo, árabe-índico…) pasa a su dígito ASCII."""
    return "".join(str(unicodedata.decimal(c)) if c.isdecimal() else c for c in texto)


def redactar_cedulas(texto: str) -> tuple[str, int]:
    """Sustituye toda cédula válida (Módulo 10) por la marca. Devuelve (texto normalizado, reemplazos).

    Límite aceptado por Seguridad: secuencias con verificador inválido no se redactan.
    """
    if not texto:
        return texto, 0
    cuenta = 0

    def _sustituir(match: re.Match) -> str:
        nonlocal cuenta
        digitos = _SEPARADORES.sub("", match.group(0))
        if validar_cedula_ecuatoriana(digitos[:10]):
            cuenta += 1
            return MARCA_CEDULA
        return match.group(0)

    return _CANDIDATA.sub(_sustituir, _digitos_ascii(texto)), cuenta


def _redactar_o_cerrar(texto: str) -> tuple[str, int]:
    """Falla cerrada: si el filtro falla, no sale nada hacia Vertex."""
    try:
        return redactar_cedulas(texto)
    except Exception as exc:  # noqa: BLE001
        from app_core.pasillo import inferencia

        no_disponible, _ = inferencia.errores()
        logger.warning("Filtro DLP pre-vuelo falló: %s", type(exc).__name__)
        raise no_disponible() from exc


class RespuestaGemini(BaseModel):
    respuesta: str
    citas: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class RespuestaCopilotoCache:
    respuesta: str
    citas: list[dict] = field(default_factory=list)
    incertidumbre: bool = False
    cache_name: str = ""
    corpus_sha256: str = ""
    modelo: str = ""
    cedulas_redactadas: int = 0
    traza: object | None = None


def _cache_por_defecto(modelo: str):
    from app_core.pasillo import regulacion_rag

    return regulacion_rag.obtener_o_crear_cache_normativo(modelo)


def _corpus_por_defecto() -> dict:
    from app_core.pasillo import regulacion_rag

    return regulacion_rag.corpus_citable()


async def consultar(
    consulta: str,
    *,
    org_id: str,
    modo: Literal["dictamen", "rapida"] = "rapida",
    obtener_cache: Callable[[str], object] = _cache_por_defecto,
    corpus_citable: Callable[[], dict] = _corpus_por_defecto,
) -> RespuestaCopilotoCache:
    from app_core.pasillo import inferencia

    modelo = MODELO_POR_MODO.get(modo)
    if modelo is None:
        raise ValueError("modo no admitido")
    # (1) DLP pre-vuelo: nada sale sin pasar por aquí.
    segura, redactadas = _redactar_o_cerrar(consulta)
    logger.info("DLP pre-vuelo: %d cédulas redactadas", redactadas)
    # (2) Caché del corpus público: el contenido cacheado no depende de la consulta ni del tenant.
    descriptor = obtener_cache(modelo)
    corpus = corpus_citable()
    indice = "\n".join(f"- {clave}: {f['articulo']} · {f['titulo']}" for clave, f in sorted(corpus.items()))
    prompt = inferencia.prompt_versionado(PROMPT_ID, PROMPT_VERSION, SISTEMA, PLANTILLA)
    # (3) Inferencia por la compuerta (sin cached_content hasta la ficha de inferencia).
    resultado, traza = await inferencia.generar_trazado(
        prompt,
        {
            "corpus_version": descriptor.corpus_version,
            "corpus_sha256": descriptor.corpus_sha256,
            "indice": indice,
            "consulta": segura,
        },
        RespuestaGemini,
        modelo=modelo,
        org_id=org_id,
        corpus_sha256=descriptor.corpus_sha256,
    )
    # (4) Citación cerrada: solo cuentan identificadores del corpus.
    citas = [dict(corpus[c], id=c) for c in dict.fromkeys(resultado.citas) if c in corpus]
    if not citas:
        logger.info("Copiloto sin cita válida del corpus; se devuelve incertidumbre")
        return RespuestaCopilotoCache(
            respuesta=INCERTIDUMBRE,
            incertidumbre=True,
            cache_name=descriptor.cache_name,
            corpus_sha256=descriptor.corpus_sha256,
            modelo=modelo,
            cedulas_redactadas=redactadas,
            traza=traza,
        )
    respuesta, _ = _redactar_o_cerrar(resultado.respuesta)
    return RespuestaCopilotoCache(
        respuesta=respuesta,
        citas=citas,
        cache_name=descriptor.cache_name,
        corpus_sha256=descriptor.corpus_sha256,
        modelo=modelo,
        cedulas_redactadas=redactadas,
        traza=traza,
    )
