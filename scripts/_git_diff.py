# -*- coding: utf-8 -*-
# ¤arbitro
"""Lector común de las rutas de un `git diff` para los árbitros de alcance y de reparto (CI-26).

Con la configuración por defecto (`core.quotepath=true`) git cita las rutas no ASCII con escapes
octales, y una ruta con tilde deja de casar con la `propiedad` de su ficha. Este lector las devuelve
literales: `-c core.quotepath=off` y `-z`, salida en bytes, decodificada en UTF-8 y partida por NUL.
Solo importa la biblioteca estándar.
"""
from __future__ import annotations

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
