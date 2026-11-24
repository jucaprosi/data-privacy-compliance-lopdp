# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤vigilancia-spdp ¤inteligencia-normativa ¤transcripcion-normativa
"""NORM-06 R1 y R7: cuándo un PDF es un escaneo y el prompt versionado de su transcripción. Sin E/S.

300 caracteres útiles por página: el sello de los escaneos de la LOPDP y del Reglamento da unos 75, cuatro veces menos,
y una página con capa de texto del Registro Oficial da miles. El 50 %: un PDF con texto puede traer portadas o anexos
escaneados sueltos sin ser un escaneo.
"""
from __future__ import annotations

from dataclasses import dataclass

from app_core.pasillo import inferencia as pasillo_inferencia

UMBRAL_CARACTERES_UTILES = 300
FRACCION_ESCANEADAS = 0.5
PAGINAS_POR_TRAMO = 10


@dataclass(frozen=True)
class PaginaPdf:
    caracteres_utiles: int  # sin espacios
    tiene_imagen: bool  # un XObject /Image en la página


def pagina_escaneada(pagina: PaginaPdf) -> bool:
    return pagina.tiene_imagen and pagina.caracteres_utiles < UMBRAL_CARACTERES_UTILES


def es_escaneo(paginas: list[PaginaPdf]) -> bool:
    """Verdadero si al menos el 50 % de las páginas son escaneadas. Sin páginas legibles no es un escaneo."""
    if not paginas:
        return False
    return sum(1 for p in paginas if pagina_escaneada(p)) >= len(paginas) * FRACCION_ESCANEADAS


PROMPT = pasillo_inferencia.prompt_versionado(
    "normativa.transcripcion", 1,
    "Eres un transcriptor de documentos oficiales. Transcribes de forma literal, página a página, sin resumir, "
    "sin corregir y sin completar lo que falte. Lo que no se pueda leer lo marcas como [ilegible]. "
    "Devuelves solo el texto, sin comentarios.",
    "Transcribe literalmente el documento adjunto.",
)
