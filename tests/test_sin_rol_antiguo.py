# ¤seguridad
# ¤arbitro
"""Árbitro permanente: el rol antiguo «encargado» no vuelve (ORG-08 / QA-13).

La regla de rechazo del rol en API vive en tests/test_rol_coordinador.py.
Este archivo preserva el árbitro de repositorio del núcleo contra restos de ROLE_ALIASES.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def test_sin_rol_antiguo():
    """El repositorio no contiene referencias activas a ROLE_ALIASES en código rastreado."""
    salida = subprocess.run(
        ["git", "ls-files", "-z"], cwd=RAIZ, capture_output=True, check=True
    ).stdout.decode("utf-8")
    archivos = [r for r in salida.split("\0") if r.endswith((".py", ".ts", ".tsx")) and not r.startswith("alembic/")]
    violaciones = []
    for r in archivos:
        if r in ("tests/test_sin_rol_antiguo.py", "tests/test_rol_coordinador.py"):
            continue
        p = RAIZ / r
        if p.is_file() and "ROLE_ALIASES" in p.read_text(encoding="utf-8", errors="replace"):
            violaciones.append(r)
    assert not violaciones, f"Archivos con ROLE_ALIASES: {violaciones}"
