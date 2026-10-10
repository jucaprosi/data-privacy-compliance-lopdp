"""Comprueba que el interprete actual tiene instalados los requisitos de requirements.txt.

Uso:  python scripts/verificar_entorno.py
Codigo de salida: 0 si estan todos; 1 si falta alguno (se listan y se indica como resolverlo).

Solo comprueba PRESENCIA, no versiones: el fallo que evita es el de ejecutar el arnes, la
aplicacion o las pruebas con un interprete al que le faltan paquetes, que se manifiesta lejos
de su causa (por ejemplo, un router que no carga y un /health en 503).
Los mensajes son ASCII a proposito: se imprimen desde cmd con cualquier pagina de codigos.
"""
from __future__ import annotations

import re
import sys
from importlib import metadata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def normalizar(nombre: str) -> str:
    """Forma canonica de un nombre de paquete (PEP 503): minusculas y guiones."""
    return re.sub(r"[-_.]+", "-", nombre).lower()


def nombres_requeridos(texto: str) -> list[str]:
    """Nombres de paquete de un requirements.txt, sin extras, versiones ni marcadores."""
    nombres: list[str] = []
    for linea in texto.replace("\r\n", "\n").split("\n"):
        linea = linea.split("#", 1)[0].strip()
        if not linea or linea.startswith("-"):
            continue
        nombre = re.split(r"[\[<>=!~;@ ]", linea, maxsplit=1)[0]
        if nombre:
            nombres.append(nombre)
    return nombres


def faltantes(texto: str, instalados: list[str]) -> list[str]:
    presentes = {normalizar(n) for n in instalados}
    return [n for n in nombres_requeridos(texto) if normalizar(n) not in presentes]


def instalados_ahora() -> list[str]:
    return [d.metadata["Name"] for d in metadata.distributions() if d.metadata["Name"]]


def main() -> int:
    texto = (RAIZ / "requirements.txt").read_text(encoding="utf-8-sig")
    falta = faltantes(texto, instalados_ahora())
    version = sys.version.split()[0]
    if not falta:
        print(f"[ENTORNO] OK: {sys.executable} (Python {version}) tiene los requisitos del proyecto.")
        return 0
    print(f"[ENTORNO] FALLO: el interprete {sys.executable} (Python {version}) no tiene: {', '.join(falta)}.")
    print("          Use el entorno virtual del proyecto (carpeta .venv) o instale los requisitos con:")
    print(f'          "{sys.executable}" -m pip install -r requirements.txt')
    return 1


if __name__ == "__main__":
    sys.exit(main())
