"""Recuperación léxica determinista (BM25) de pasajes relevantes para un control. Sin ML ni red."""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter

from features.preanalisis.domain.models import ControlContexto, FragmentoRelevante, Segmento

PASAJE_MIN = 600
PASAJE_MAX = 1000
TOP_K_DEFECTO = 6
_K1 = 1.5
_B = 0.75

_STOPWORDS = frozenset(
    (
        "a al algo ante como con contra cual cuando de del desde donde durante e el ella ellos en entre era es "
        "esta estan este esto estos fue ha han hasta hay la las le les lo los mas me mi muy no nos o para pero "
        "por que se sea ser si sin sobre su sus te tiene tienen tambien todo un una uno unos y ya the and of to in"
    ).split()
)
_TOKEN = re.compile(r"[a-z0-9]{3,}")


def normalizar_texto(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")


def tokenizar(texto: str) -> list[str]:
    return [t for t in _TOKEN.findall(normalizar_texto(texto)) if t not in _STOPWORDS]


def _trocear_parrafo(parrafo: str) -> list[str]:
    if len(parrafo) <= PASAJE_MAX:
        return [parrafo]
    partes: list[str] = []
    actual = ""
    for oracion in re.split(r"(?<=[.!?;])\s+", parrafo):
        while len(oracion) > PASAJE_MAX:
            if actual:
                partes.append(actual)
                actual = ""
            partes.append(oracion[:PASAJE_MAX])
            oracion = oracion[PASAJE_MAX:]
        if actual and len(actual) + 1 + len(oracion) > PASAJE_MAX:
            partes.append(actual)
            actual = oracion
        else:
            actual = f"{actual} {oracion}".strip()
    if actual:
        partes.append(actual)
    return partes


def trocear(segmentos: list[Segmento]) -> list[tuple[str, str]]:
    """Devuelve pasajes (origen, texto) de ~600-1000 caracteres, agrupando párrafos contiguos."""
    pasajes: list[tuple[str, str]] = []
    for seg in segmentos:
        actual = ""
        for parrafo in (p.strip() for p in re.split(r"\n+", seg.texto)):
            if not parrafo:
                continue
            for trozo in _trocear_parrafo(parrafo):
                if actual and (len(actual) + 1 + len(trozo) > PASAJE_MAX or len(actual) >= PASAJE_MIN):
                    pasajes.append((seg.origen, actual))
                    actual = trozo
                else:
                    actual = f"{actual}\n{trozo}".strip()
        if actual:
            pasajes.append((seg.origen, actual))
    return pasajes


def seleccionar_relevantes(
    segmentos: list[Segmento], control: ControlContexto, k: int = TOP_K_DEFECTO
) -> list[FragmentoRelevante]:
    pasajes = trocear(segmentos)
    consulta = set(tokenizar(f"{control.control} {control.enunciado} {control.evidencia_esperada}"))
    if not pasajes or not consulta:
        return []
    docs = [Counter(tokenizar(texto)) for _, texto in pasajes]
    largos = [sum(d.values()) for d in docs]
    n = len(docs)
    promedio = (sum(largos) / n) or 1.0
    puntajes: list[float] = []
    for d, largo in zip(docs, largos):
        s = 0.0
        for termino in consulta:
            f = d.get(termino, 0)
            if not f:
                continue
            df = sum(1 for x in docs if termino in x)
            idf = math.log(1.0 + (n - df + 0.5) / (df + 0.5))
            s += idf * f * (_K1 + 1) / (f + _K1 * (1 - _B + _B * largo / promedio))
        puntajes.append(s)
    maximo = max(puntajes)
    if maximo <= 0:
        return []
    orden = sorted(range(n), key=lambda i: (-puntajes[i], i))[:k]
    return [
        FragmentoRelevante(texto=pasajes[i][1], origen=pasajes[i][0], relevancia=round(puntajes[i] / maximo, 4))
        for i in orden
        if puntajes[i] > 0
    ]
