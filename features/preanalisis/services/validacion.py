"""Reglas deterministas de integridad (2-4) como funciones puras. Son la defensa real contra alucinación e inyección."""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence

from features.preanalisis.domain.models import (
    ESTADO_SIN_SUSTENTO,
    ESTADOS_VALIDOS,
    LIMITACIONES,
    Cita,
    CitaModelo,
    Fragmento,
    PropuestaModelo,
    PropuestaValidada,
)

LONGITUD_MINIMA_CITA = 30
MAX_CITAS_EVALUADAS = 10
MAX_CARACTERES_RAZONAMIENTO = 2000
MAX_CARACTERES_MOTIVO = 500
_COMILLAS = "\"'`“”‘’«»„"
_ESPACIOS = re.compile(r"\s+")
_TERMINADORES = ".;:!?"
_SALTOS = "\n\r\u2028\u2029\x0b\x0c"
_FIN_ORACION = re.compile(r"[.;:!?](?=\s|$)")
_PALABRA = re.compile(r"[^\W\d_]+")
_NEGACIONES = frozenset(
    {"no", "nunca", "jamás", "jamas", "sin", "ni", "tampoco", "excepto", "salvo", "aunque", "pero"}
)
PALABRAS_CONTEXTO_IZQ = 6
PALABRAS_CONTEXTO_DER = 3


def normalizar_cita(texto: str) -> str:
    """NFKC, minúsculas, espacios colapsados y sin comillas envolventes."""
    t = unicodedata.normalize("NFKC", texto).lower()
    t = _ESPACIOS.sub(" ", t).strip()
    t = t.strip(_COMILLAS + " ")
    return _ESPACIOS.sub(" ", t).strip()


def normalizar_estado(valor: str) -> str:
    """Regla 2: solo Conforme/Parcial/Sin sustento; cualquier otro valor (p. ej. No Conforme) => Sin sustento."""
    limpio = _ESPACIOS.sub(" ", (valor or "").strip()).casefold()
    for estado in ESTADOS_VALIDOS:
        if limpio == estado.casefold():
            return estado
    return ESTADO_SIN_SUSTENTO


def _normalizar_con_saltos(texto: str) -> tuple[str, list[bool]]:
    """Normaliza como ``normalizar_cita`` (sin quitar comillas) y marca qué espacios colapsados contenían un salto de línea."""
    t = unicodedata.normalize("NFKC", texto).lower()
    salida: list[str] = []
    salto: list[bool] = []
    en_espacio = False
    for ch in t:
        if ch.isspace():
            if not en_espacio and salida:
                salida.append(" ")
                salto.append(False)
            en_espacio = True
            if ch in _SALTOS and salto:
                salto[-1] = True
        else:
            en_espacio = False
            salida.append(ch)
            salto.append(False)
    while salida and salida[-1] == " ":
        salida.pop()
        salto.pop()
    return "".join(salida), salto


def _hay_negacion(texto: str, palabras: int, desde_final: bool) -> bool:
    encontradas = _PALABRA.findall(texto)
    ventana = encontradas[-palabras:] if desde_final else encontradas[:palabras]
    return any(p in _NEGACIONES for p in ventana)


def _ocurrencia_valida(b: str, salto: list[bool], s: int, e: int) -> bool:
    """Límites de oración/línea y guarda de negación para la cita ``b[s:e]``."""
    termina_en_terminador = b[e - 1] in _TERMINADORES
    # (b) límite izquierdo: inicio, tras terminador o inicio de línea original.
    if s > 0:
        if b[s - 1] != " ":
            return False
        if not (salto[s - 1] or (s >= 2 and b[s - 2] in _TERMINADORES)):
            return False
    # (b) límite derecho: fin, terminador (incluido o no) o fin de línea original.
    if e < len(b) and not termina_en_terminador:
        if b[e] == " ":
            if not salto[e]:
                return False
        elif not (b[e] in _TERMINADORES and (e + 1 == len(b) or b[e + 1] == " ")):
            return False
    # (c) negación en el contexto de la misma oración.
    previo = b[:s]
    cortes = list(_FIN_ORACION.finditer(previo))
    if cortes:
        previo = previo[cortes[-1].end() :]
    if _hay_negacion(previo, PALABRAS_CONTEXTO_IZQ, desde_final=True):
        return False
    if not termina_en_terminador:
        posterior = b[e:]
        corte = _FIN_ORACION.search(posterior)
        if corte:
            posterior = posterior[: corte.start()]
        if _hay_negacion(posterior, PALABRAS_CONTEXTO_DER, desde_final=False):
            return False
    return True


def _cita_en_fragmento(n: str, b: str, salto: list[bool]) -> bool:
    inicio = b.find(n)
    while inicio != -1:
        if _ocurrencia_valida(b, salto, inicio, inicio + len(n)):
            return True
        inicio = b.find(n, inicio + 1)
    return False


def verificar_citas(citas: Sequence[CitaModelo], fragmentos: Sequence[Fragmento]) -> tuple[list[Cita], int]:
    """Regla 3: una cita es válida solo si es literal (normalizada), completa (límites de oración/línea) y sin negación cercana."""
    base = [_normalizar_con_saltos(f.texto) for f in fragmentos]
    verificadas: list[Cita] = []
    vistas: set[str] = set()
    descartadas = 0
    for c in citas[:MAX_CITAS_EVALUADAS]:
        n = normalizar_cita(c.fragmento)
        if len(n) < LONGITUD_MINIMA_CITA or not any(_cita_en_fragmento(n, b, sl) for b, sl in base):
            descartadas += 1
            continue
        if n in vistas:
            continue
        vistas.add(n)
        verificadas.append(Cita(fragmento=c.fragmento.strip(), motivo=c.motivo.strip()[:MAX_CARACTERES_MOTIVO]))
    descartadas += max(0, len(citas) - MAX_CITAS_EVALUADAS)
    return verificadas, descartadas


def validar_propuesta(
    propuesta: PropuestaModelo, fragmentos: Sequence[Fragmento], modelo: str
) -> PropuestaValidada:
    """Aplica reglas 2-4 a la salida del modelo."""
    estado = normalizar_estado(propuesta.estado)
    citas, descartadas = verificar_citas(propuesta.citas, fragmentos)
    razonamiento = propuesta.razonamiento.strip()[:MAX_CARACTERES_RAZONAMIENTO]
    if estado != ESTADO_SIN_SUSTENTO and not citas:
        estado = ESTADO_SIN_SUSTENTO
        razonamiento = (
            "Estado ajustado a 'Sin sustento': la propuesta no incluyó ninguna cita verificable en el documento. "
            + razonamiento
        ).strip()
    nivel = 1 if (citas and estado != ESTADO_SIN_SUSTENTO) else 0
    return PropuestaValidada(
        estado=estado,  # type: ignore[arg-type]
        nivel_evidencia_maximo=nivel,  # type: ignore[arg-type]
        citas=citas,
        citas_descartadas=descartadas,
        razonamiento=razonamiento,
        limitaciones=list(LIMITACIONES),
        modelo=modelo,
    )
