# ¤adpa ¤implementacion ¤conservacion
"""ADPA-09: las salas del catálogo del PRD §5.2 llevan su compuerta canónica y, si existen en features/, el archivo está."""
from __future__ import annotations

import ast
import importlib
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
PRD = RAIZ / "governance" / "artefactos" / "PRD.md"
NUEVAS = {"formacion", "conservacion"}


def _catalogo() -> list[tuple[str, str, str, str]]:
    """Filas `features/<sala>/` del catálogo del PRD §5.2 (sala, ubicación, compuerta, existe)."""
    texto = PRD.read_text(encoding="utf-8")
    bloque = texto.split("### 5.2 Catálogo Constitucional", 1)[1].split("\n### 5.3", 1)[0]
    filas = []
    for linea in bloque.splitlines():
        m = re.match(r"\| `([a-z0-9_]+)` \| `([^`]+)`[^|]*\| `?([a-z0-9_]+_service\.py)?`?[^|]*\|", linea)
        if m and m.group(2).startswith("features/"):
            ubicacion = m.group(2).rstrip("/")
            filas.append((m.group(1), ubicacion, m.group(3) or "", "existe" if (RAIZ / ubicacion).is_dir() else "planificada"))
    return filas


SALAS = _catalogo()


def test_catalogo_incluye_las_salas_nuevas():
    assert NUEVAS <= {f[0] for f in SALAS}


@pytest.mark.parametrize("sala,ubicacion,compuerta,estado", SALAS, ids=[f[0] for f in SALAS])
def test_sala_existe_con_su_compuerta(sala, ubicacion, compuerta, estado):
    assert ubicacion == f"features/{sala}"
    assert compuerta == f"{sala}_service.py"
    if estado == "existe":
        assert (RAIZ / ubicacion / compuerta).is_file()
