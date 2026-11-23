# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤inteligencia-normativa ¤vertex-cache ¤adpa
"""NORM-03: texto del original de una resolución, fragmentos y citas de artículos.

El original sale de NORM-01 (PDF custodiado). El texto se divide en fragmentos con solape para indexarlos con
el modelo de vectores del pasillo, por el pasillo de `regulacion_rag`; sin indexador disponible el análisis sigue, porque el modelo
recibe el texto completo y los vectores solo sirven para recuperar.
"""
from __future__ import annotations

import io
import re
import unicodedata
from dataclasses import dataclass
from typing import Optional, Protocol

from app_core.pasillo import inferencia as pasillo_inferencia

MODELO_EMBEDDING = pasillo_inferencia.MODELO_EMBEDDING
LARGO_FRAGMENTO = 1500
SOLAPE = 150
MAXIMO_PAGINAS = 400

_ARTICULO = re.compile(r"\bart(?:[ií]culo|\.)?\s*(\d{1,3})(?:\s*[-.]?\s*([A-Za-z]))?\b", re.IGNORECASE)
_DISPOSICION = re.compile(
    r"\bdisposici[oó]n\s+(general|transitoria|final|derogatoria|reformatoria)\s+(\w+)", re.IGNORECASE
)


@dataclass(frozen=True)
class Fragmento:
    indice: int
    texto: str
    articulos: tuple[str, ...]


class Indexador(Protocol):
    """Puerto de vectorización: devuelve un vector por texto, o lanza si el servicio no está disponible."""

    async def vectorizar(self, textos: list[str], modelo: str) -> list[list[float]]: ...


def _plano(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in sin_tildes if not unicodedata.combining(c)).lower()


def normalizar_cita(cita: str) -> Optional[str]:
    """Una cita de artículo o de disposición («Art. N», «Disposición transitoria primera») → clave comparable, o None."""
    m = _ARTICULO.search(cita or "")
    if m:
        return f"art{m.group(1)}{(m.group(2) or '').lower()}"
    d = _DISPOSICION.search(_plano(cita or ""))
    if d:
        return f"disp_{d.group(1)}_{d.group(2)}"
    return None


def articulos_del_texto(texto: str) -> frozenset[str]:
    """Claves de todos los artículos y disposiciones que el texto de la resolución menciona."""
    claves = {f"art{m.group(1)}{(m.group(2) or '').lower()}" for m in _ARTICULO.finditer(texto)}
    claves |= {f"disp_{d.group(1).lower()}_{_plano(d.group(2))}" for d in _DISPOSICION.finditer(texto)}
    return frozenset(claves)


def extraer_texto(pdf: bytes) -> str:
    """Texto plano del PDF. Falla cerrada: un PDF ilegible devuelve cadena vacía, nunca texto inventado."""
    try:
        from pypdf import PdfReader

        lector = PdfReader(io.BytesIO(pdf))
        paginas = lector.pages[:MAXIMO_PAGINAS]
        return "\n".join((p.extract_text() or "") for p in paginas).strip()
    except Exception:  # noqa: BLE001 — el PDF es externo; el motivo no se filtra
        return ""


def fragmentar(texto: str, largo: int = LARGO_FRAGMENTO, solape: int = SOLAPE) -> list[Fragmento]:
    """Fragmentos de hasta `largo` caracteres con `solape`, cortados en espacio para no partir palabras."""
    if largo <= solape:
        raise ValueError("largo debe superar al solape")
    limpio = re.sub(r"[ \t]+", " ", texto).strip()
    fragmentos: list[Fragmento] = []
    inicio = 0
    while inicio < len(limpio):
        fin = min(inicio + largo, len(limpio))
        if fin < len(limpio):
            corte = limpio.rfind(" ", inicio + largo // 2, fin)
            fin = corte if corte > inicio else fin
        trozo = limpio[inicio:fin].strip()
        if trozo:
            fragmentos.append(Fragmento(len(fragmentos), trozo, tuple(sorted(articulos_del_texto(trozo)))))
        if fin >= len(limpio):
            break
        inicio = max(fin - solape, inicio + 1)
    return fragmentos


async def indexar(fragmentos: list[Fragmento], indexador: Optional[Indexador]) -> int:
    """Vectoriza con el modelo de vectores del pasillo; devuelve cuántos vectores obtuvo (0 si no hay indexador o falla)."""
    if indexador is None or not fragmentos:
        return 0
    try:
        vectores = await indexador.vectorizar([f.texto for f in fragmentos], MODELO_EMBEDDING)
    except Exception:  # noqa: BLE001 — la indexación es auxiliar; el análisis no depende de ella
        return 0
    return len(vectores)
