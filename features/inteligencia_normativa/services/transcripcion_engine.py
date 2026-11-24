# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤vigilancia-spdp ¤inteligencia-normativa ¤transcripcion-normativa
"""NORM-06 R3 y R4: texto de un original, por tramos de 10 páginas y una sola vez por `sha256`.

Llega a Vertex solo por el pasillo de inferencia. Si un tramo falla o da vacío falla todo el documento y no se guarda
nada parcial. La fila se inserta en la transacción del llamador (no hace commit).
"""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional

from sqlalchemy import text

from features.inteligencia_normativa.domain.errores import IaNoDisponible, ResolucionSinTexto
from features.inteligencia_normativa.domain.transcripcion import PAGINAS_POR_TRAMO, PROMPT, es_escaneo
from features.inteligencia_normativa.services import extraccion

logger = logging.getLogger(__name__)

ORIGEN_CAPA_TEXTO = "capa_texto"
ORIGEN_TRANSCRIPCION = "transcripcion"
Transcriptor = Callable[..., Awaitable[tuple[str, Any]]]


@dataclass(frozen=True)
class TextoDeOriginal:
    texto: str
    origen: str


def partir_en_tramos(pdf: bytes) -> list[bytes]:
    """Tramos de `PAGINAS_POR_TRAMO` páginas, en orden, dentro del mismo máximo de páginas de la extracción."""
    from pypdf import PdfReader, PdfWriter

    paginas = PdfReader(io.BytesIO(pdf)).pages[: extraccion.MAXIMO_PAGINAS]
    tramos: list[bytes] = []
    for inicio in range(0, len(paginas), PAGINAS_POR_TRAMO):
        escritor = PdfWriter()
        for pagina in paginas[inicio: inicio + PAGINAS_POR_TRAMO]:
            escritor.add_page(pagina)
        salida = io.BytesIO()
        escritor.write(salida)
        tramos.append(salida.getvalue())
    return tramos


async def _por_el_pasillo(pdf: bytes, prompt, *, modelo: str):
    from app_core.pasillo import inferencia as pasillo_inferencia

    return await pasillo_inferencia.transcribir_pdf(pdf, prompt, modelo=modelo)


async def transcribir_por_tramos(pdf: bytes, transcribir: Optional[Transcriptor], modelo: str) -> tuple[str, Any]:
    """(texto unido, traza del primer tramo). Cualquier fallo o vacío falla todo: nunca texto parcial."""
    transcribir = transcribir or _por_el_pasillo
    try:
        tramos = partir_en_tramos(pdf)
    except Exception as exc:  # noqa: BLE001 — el PDF es externo
        raise ResolucionSinTexto() from exc
    textos: list[str] = []
    traza = None
    for tramo in tramos:
        try:
            texto, t = await transcribir(tramo, PROMPT, modelo=modelo)
        except Exception as exc:  # noqa: BLE001 — falla cerrada; solo el tipo, nunca el mensaje
            logger.warning("Transcripción sin IA: %s", type(exc).__name__)
            raise IaNoDisponible() from exc
        if not (texto or "").strip():
            raise ResolucionSinTexto()
        textos.append(texto.strip())
        traza = traza or t
    if not textos:
        raise ResolucionSinTexto()
    return "\n".join(textos), traza


async def _guardada(sesion, archivo_sha256: str) -> Optional[str]:
    return (await sesion.execute(
        text("SELECT texto FROM normativa_transcripciones WHERE archivo_sha256 = :h"), {"h": archivo_sha256},
    )).scalar_one_or_none()


async def texto_de(sesion, pdf: bytes, archivo_sha256: str, *, modelo: str,
                   transcribir: Optional[Transcriptor] = None) -> TextoDeOriginal:
    """Capa de texto si el PDF no es un escaneo; si lo es, la transcripción guardada o una nueva (una por `sha256`)."""
    paginas = extraccion.estadisticas(pdf)
    if not es_escaneo(paginas):
        return TextoDeOriginal(extraccion.extraer_texto(pdf), ORIGEN_CAPA_TEXTO)
    guardada = await _guardada(sesion, archivo_sha256)
    if guardada is not None:
        return TextoDeOriginal(guardada, ORIGEN_TRANSCRIPCION)
    await sesion.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:h, 6))"), {"h": archivo_sha256})
    guardada = await _guardada(sesion, archivo_sha256)  # otro análisis pudo transcribirla mientras esperábamos
    if guardada is not None:
        return TextoDeOriginal(guardada, ORIGEN_TRANSCRIPCION)
    texto, traza = await transcribir_por_tramos(pdf, transcribir, modelo)
    await sesion.execute(
        text("INSERT INTO normativa_transcripciones (archivo_sha256, texto, paginas, caracteres, modelo_solicitado, "
             "modelo_version, prompt_id, prompt_version) VALUES (:h, :t, :p, :c, :ms, :mv, :pi, :pv)"),
        {"h": archivo_sha256, "t": texto, "p": len(paginas), "c": len(texto), "ms": traza.modelo_solicitado,
         "mv": traza.modelo_version, "pi": traza.prompt_id, "pv": traza.prompt_version},
    )
    return TextoDeOriginal(texto, ORIGEN_TRANSCRIPCION)
