# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤arbitro
"""Lector común de las rutas de un `git diff` para los árbitros de alcance y de reparto (CI-26).

Con la configuración por defecto (`core.quotepath=true`) git cita las rutas no ASCII con escapes
octales, y una ruta con tilde deja de casar con la `propiedad` de su ficha. Este lector las devuelve
literales: `-c core.quotepath=off` y `-z`, salida en bytes, decodificada en UTF-8 y partida por NUL.
CI-33: `lineas_cambiadas` da las líneas que una rama cambia en un archivo, y `contenido_en` lee un archivo tal
como está en una revisión; los usa la R5 del reparto para las secciones por sembrar y la ficha propia.
Solo importa la biblioteca estándar.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path


# ¤adpa
def archivos_del_diff(base: str, cabeza: str, raiz: Path) -> list[str]:
    """git -c core.quotepath=off diff --name-only -z base...cabeza, en bytes, decodificado en UTF-8 y partido por NUL."""
    salida = subprocess.run(
        ["git", "-c", "core.quotepath=off", "diff", "--name-only", "-z", f"{base}...{cabeza}"],
        cwd=raiz, capture_output=True, check=True,
    ).stdout
    return [ruta for ruta in salida.decode("utf-8").split("\0") if ruta]


_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


# ¤adpa
def lineas_cambiadas(base: str, cabeza: str, raiz: Path, ruta: str) -> list[int]:
    """Líneas del lado de `cabeza` que el diff `base...cabeza` añade o modifica en `ruta` (CI-33).

    Un bloque que solo borra da la línea siguiente al borrado, para que un borrado fuera de una sección cuente.
    """
    salida = subprocess.run(
        ["git", "-c", "core.quotepath=off", "diff", "-U0", f"{base}...{cabeza}", "--", ruta],
        cwd=raiz, capture_output=True, check=True,
    ).stdout.decode("utf-8", errors="replace")
    lineas: list[int] = []
    for linea in salida.splitlines():
        m = _HUNK.match(linea)
        if not m:
            continue
        inicio, cuantas = int(m.group(1)), int(m.group(2) or "1")
        lineas += list(range(inicio, inicio + cuantas)) if cuantas else [inicio + 1]
    return lineas


# ¤adpa
def contenido_en(revision: str, raiz: Path, ruta: str) -> str | None:
    """El texto de `ruta` en `revision` (`git show revision:ruta`), o None si ahí no existe."""
    salida = subprocess.run(["git", "-c", "core.quotepath=off", "show", f"{revision}:{ruta}"],
                            cwd=raiz, capture_output=True)
    return salida.stdout.decode("utf-8") if salida.returncode == 0 else None
