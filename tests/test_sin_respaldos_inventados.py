"""Impide que la capa HTTP convierta fallos reales en datos literales inventados."""

from pathlib import Path
import re


API_TS = Path(__file__).parents[1] / "frontend" / "src" / "lib" / "api.ts"
EXPORTADA = re.compile(r"\bexport\s+(?:async\s+)?function\s+(?P<nombre>[A-Za-z_$][\w$]*)\s*\(")
CATCH = re.compile(r"\bcatch\s*(?:\([^)]*\))?\s*\{")
RETORNO_LITERAL = re.compile(r"\breturn\s*(?:\[|\{|['\"`])")


def _cierre_llave(texto: str, apertura: int) -> int:
    """Encuentra la llave pareja ignorando cadenas y comentarios de JS/TS."""
    profundidad = 0
    i = apertura
    cadena: str | None = None
    while i < len(texto):
        caracter = texto[i]
        siguiente = texto[i + 1] if i + 1 < len(texto) else ""
        if cadena:
            if caracter == "\\":
                i += 2
                continue
            if caracter == cadena:
                cadena = None
        elif caracter in "'\"`":
            cadena = caracter
        elif caracter == "/" and siguiente == "/":
            salto = texto.find("\n", i + 2)
            i = len(texto) if salto < 0 else salto
            continue
        elif caracter == "/" and siguiente == "*":
            cierre = texto.find("*/", i + 2)
            i = len(texto) if cierre < 0 else cierre + 2
            continue
        elif caracter == "{":
            profundidad += 1
        elif caracter == "}":
            profundidad -= 1
            if profundidad == 0:
                return i
        i += 1
    raise AssertionError(f"Llave sin cerrar en {API_TS}:{texto.count(chr(10), 0, apertura) + 1}")


def test_funciones_exportadas_no_devuelven_literales_en_catch() -> None:
    texto = API_TS.read_text(encoding="utf-8")
    hallazgos: list[str] = []

    for exportada in EXPORTADA.finditer(texto):
        apertura_funcion = texto.find("{", exportada.end())
        cierre_funcion = _cierre_llave(texto, apertura_funcion)
        cuerpo = texto[apertura_funcion + 1 : cierre_funcion]
        for captura in CATCH.finditer(cuerpo):
            apertura_catch = apertura_funcion + 1 + captura.end() - 1
            cierre_catch = _cierre_llave(texto, apertura_catch)
            retorno = RETORNO_LITERAL.search(texto, apertura_catch + 1, cierre_catch)
            if retorno:
                linea = texto.count("\n", 0, retorno.start()) + 1
                hallazgos.append(f"{API_TS.relative_to(API_TS.parents[2])}:{linea} ({exportada.group('nombre')})")

    assert not hallazgos, "Retorno literal dentro de catch:\n" + "\n".join(hallazgos)
