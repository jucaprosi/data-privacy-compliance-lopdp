# ¤adpa ¤implementacion ¤conservacion
"""ADPA-09: las salas del catálogo del PRD §7.1 existen en features/ con su compuerta canónica."""
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
    texto = PRD.read_text(encoding="utf-8")
    bloque = texto.split("### 7.1 Catálogo de Salas ADPA", 1)[1].split("\n**", 1)[0]
    filas = []
    for linea in bloque.splitlines():
        m = re.match(r"\| `([a-z0-9_]+)` \| `([^`]+)` \| `?([a-z0-9_]+_service\.py)?`?[^|]*\|[^|]*\| ([^|]*)\|", linea)
        if m and m.group(2).startswith("features/"):
            filas.append((m.group(1), m.group(2), m.group(3) or "", m.group(4).strip()))
    return filas


SALAS = [f for f in _catalogo() if f[3].startswith("existe") or f[0] in NUEVAS]


def test_catalogo_incluye_las_salas_nuevas():
    assert NUEVAS <= {f[0] for f in SALAS}


@pytest.mark.parametrize("sala,ubicacion,compuerta,estado", SALAS, ids=[f[0] for f in SALAS])
def test_sala_existe_con_su_compuerta(sala, ubicacion, compuerta, estado):
    assert ubicacion == f"features/{sala}"
    assert compuerta == f"{sala}_service.py"
    assert (RAIZ / ubicacion / compuerta).is_file()


@pytest.mark.parametrize("sala", sorted(NUEVAS))
def test_salas_nuevas_importan_y_registran(sala):
    importlib.import_module(f"features.{sala}.{sala}_service")
    errores = importlib.import_module(f"features.{sala}.domain.errores")
    assert callable(errores.registrar)
    pasillo = RAIZ / "app_core" / "pasillo" / f"{sala}.py"
    for nodo in ast.parse(pasillo.read_text(encoding="utf-8")).body:
        if isinstance(nodo, (ast.Import, ast.ImportFrom)):
            nombres = [nodo.module or ""] if isinstance(nodo, ast.ImportFrom) else [a.name for a in nodo.names]
            assert not any(n.startswith("features") for n in nombres)
    importlib.import_module(f"app_core.pasillo.{sala}")
