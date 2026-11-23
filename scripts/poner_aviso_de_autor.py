# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤ip
# ¤arbitro
"""Pone la línea de aviso de derechos de autor en cada archivo de código versionado (LEG-06).

Uso: ``python scripts/poner_aviso_de_autor.py [--verificar]``.

- R1: recorre ``git ls-files`` con las extensiones de ``EXTENSIONES``, salvo ``.github/``.
- R2: el aviso es la primera línea de contenido, con el comentario del lenguaje, después del BOM, del shebang, de la
  línea ``coding`` de Python (PEP 263) y de ``@echo off``. En TypeScript va antes de ``"use client"``.
- Es idempotente: una segunda pasada no cambia nada. Con ``--verificar`` solo lista los archivos sin aviso en su sitio
  y sale con código 1 si hay alguno.

El final de línea del archivo se respeta: si usa ``\\r\\n``, el aviso también.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
AVISO = ("© 2026 Juan Carlos Proaño. Todos los derechos reservados. "
         "Uso, copia o distribución prohibidos sin autorización escrita.")
BOM = "﻿"
EXCLUIDOS = (".github/",)

# R2: el comentario de línea de cada extensión de R1 («{}» es el aviso).
EXTENSIONES = {
    ".py": "# {}", ".yaml": "# {}", ".yml": "# {}", ".toml": "# {}", ".sh": "# {}", ".ps1": "# {}",
    ".ini": "; {}",
    ".ts": "// {}", ".tsx": "// {}", ".js": "// {}", ".jsx": "// {}", ".mjs": "// {}", ".cjs": "// {}",
    ".go": "// {}",
    ".css": "/* {} */",
    ".sql": "-- {}",
    ".bat": "REM {}",
}

_CODING = re.compile(r"^[ \t\f]*#.*?coding[:=][ \t]*[-_.a-zA-Z0-9]+")  # PEP 263
_TROZOS = re.compile(r"(?<=\n)")


# ¤ip
def linea_de_aviso(extension: str) -> str:
    """La línea exacta que hay que pegar en un archivo de esa extensión (R3), sin final de línea."""
    return EXTENSIONES[extension.lower()].format(AVISO)


# ¤ip
def extension_de(ruta: str) -> str:
    return Path(ruta).suffix.lower()


# ¤ip
def es_de_r1(ruta: str) -> bool:
    """R1: extensión de la lista y fuera de ``.github/``."""
    ruta = ruta.replace("\\", "/")
    return extension_de(ruta) in EXTENSIONES and not ruta.startswith(EXCLUIDOS)


# ¤ip
def archivos_de_r1(raiz: Path = RAIZ) -> list[str]:
    salida = subprocess.run(["git", "-c", "core.quotepath=off", "ls-files", "-z"], cwd=raiz,
                            capture_output=True, check=True).stdout
    return sorted(r for r in salida.decode("utf-8").split("\0") if r and es_de_r1(r))


# ¤ip
def trozos(texto: str) -> list[str]:
    """Las líneas con su final; sin el trozo vacío que deja un texto terminado en salto."""
    return [t for t in _TROZOS.split(texto) if t]


# ¤ip
def posicion_de_aviso(lineas: list[str], extension: str) -> int:
    """R2: índice donde va el aviso en ``lineas`` (sin BOM, sin el aviso): tras shebang, ``coding`` y ``@echo off``."""
    extension = extension.lower()
    limpias = [linea.rstrip("\r\n") for linea in lineas]
    pos = 0
    if limpias and limpias[0].startswith("#!"):
        pos = 1
    if extension == ".py":
        # PEP 263: la línea coding vale en la primera o la segunda línea del archivo.
        for i in range(pos, min(2, len(limpias))):
            if _CODING.match(limpias[i]):
                pos = i + 1
                break
    if extension == ".bat" and len(limpias) > pos and limpias[pos].strip().lower() == "@echo off":
        pos += 1
    return pos


# ¤ip
def _final_de_linea(texto: str) -> str:
    return "\r\n" if "\r\n" in texto else "\n"


# ¤ip
def poner_aviso(texto: str, extension: str) -> str:
    """El texto con el aviso en su sitio (R2). Si ya estaba en las primeras líneas, se recoloca; si estaba bien, no cambia."""
    bom = BOM if texto.startswith(BOM) else ""
    cuerpo = texto[len(bom):]
    aviso = linea_de_aviso(extension)
    lineas = trozos(cuerpo)
    cabeza = [i for i, linea in enumerate(lineas[:5]) if linea.rstrip("\r\n") == aviso]
    for i in reversed(cabeza):
        del lineas[i]
    pos = posicion_de_aviso(lineas, extension)
    nl = _final_de_linea(cuerpo)
    if pos > 0 and not lineas[pos - 1].endswith("\n"):
        lineas[pos - 1] += nl  # la línea previa era la última y no tenía salto
    lineas.insert(pos, aviso + nl)
    return bom + "".join(lineas)


# ¤ip
def tiene_aviso(texto: str, extension: str) -> bool:
    return poner_aviso(texto, extension) == texto


# ¤ip
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--verificar", action="store_true", help="solo lista los archivos sin aviso; sale con 1 si hay")
    ap.add_argument("--raiz", default=str(RAIZ), help="raíz del repositorio (por defecto, la de este script)")
    args = ap.parse_args(argv)
    raiz = Path(args.raiz)
    pendientes = []
    for ruta in archivos_de_r1(raiz):
        archivo = raiz / ruta
        if not archivo.is_file():
            continue
        texto = archivo.read_bytes().decode("utf-8")
        nuevo = poner_aviso(texto, extension_de(ruta))
        if nuevo == texto:
            continue
        pendientes.append(ruta)
        if not args.verificar:
            archivo.write_bytes(nuevo.encode("utf-8"))
    if args.verificar:
        for ruta in pendientes:
            print(f"SIN AVISO: {ruta} → pega como primera línea de contenido: {linea_de_aviso(extension_de(ruta))}")
        print(f"AVISO DE AUTOR: {len(pendientes)} archivo(s) sin aviso.")
        return 1 if pendientes else 0
    print(f"AVISO DE AUTOR: puesto en {len(pendientes)} archivo(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
