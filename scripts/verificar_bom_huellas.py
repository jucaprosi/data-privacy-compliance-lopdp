# -*- coding: utf-8 -*-
# ¤arbitro
"""Árbitro de codificación: ningún .py ni .md lleva BOM y ningún .py deja una huella abierta.

Una carpeta se excluye si su ruta contiene el texto de EXCLUSIONES en cualquier punto, no solo como nombre
completo: por eso `.git` también excluye `.github`. Un archivo que no se puede leer no se cuenta como fallo.
"""
from __future__ import annotations

import os
import sys

BOM = b"\xef\xbb\xbf"
HUELLA = chr(166)  # escrita por código: el carácter literal haría fallar a este mismo archivo
EXCLUSIONES = (".git", "node_modules", ".pytest_cache", "__pycache__", "verificadores")


def tiene_bom(ruta: str) -> bool:
    try:
        with open(ruta, "rb") as archivo:
            return archivo.read(3) == BOM
    except OSError:
        return False


def huellas_abiertas(ruta: str) -> list[str]:
    fallos: list[str] = []
    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            for numero, linea in enumerate(archivo, 1):
                if HUELLA in linea:
                    fallos.append(f"{ruta}:L{numero}")
    except (OSError, UnicodeDecodeError):
        pass
    return fallos


# ¤arbitro
def encontrar_fallos(raiz: str) -> list[str]:
    fallos: list[str] = []
    for carpeta, _, archivos in os.walk(raiz):
        if any(excluida in os.path.relpath(carpeta, raiz) for excluida in EXCLUSIONES):
            continue
        for nombre in archivos:
            ruta = os.path.join(carpeta, nombre)
            if nombre.endswith((".py", ".md")) and tiene_bom(ruta):
                fallos.append(ruta)
            if nombre.endswith(".py"):
                fallos.extend(huellas_abiertas(ruta))
    return fallos


def main() -> int:
    fallos = encontrar_fallos(".")
    if fallos:
        print(f"Invariante roto (BOM o huellas): {fallos}", file=sys.stderr)
        return 1
    print("Cero huellas abiertas y sin BOM.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
