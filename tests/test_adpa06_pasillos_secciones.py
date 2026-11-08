# ¤adpa
"""ADPA-06: los pasillos tienen sus secciones reservadas y no importan features/ en el nivel superior."""
from __future__ import annotations

import ast
import importlib
import re
import tomllib
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
FICHA = tomllib.loads((RAIZ / "governance" / "tareas" / "ADPA-06.md").read_text(encoding="utf-8").split("+++")[1])
SECCIONES = FICHA["siembra"] + [p for p in FICHA["propiedad"] if p.endswith("#ADPA-06")] + [
    f"{c}#ADPA-06" for c in FICHA["crea"] if c.startswith("app_core/")
]
PASILLOS = sorted({s.split("#")[0] for s in SECCIONES})


@pytest.mark.parametrize("entrada", SECCIONES)
def test_seccion_existe_y_cierra(entrada):
    ruta, ident = entrada.split("#")
    texto = (RAIZ / ruta).read_text(encoding="utf-8")
    assert texto.count(f"# === {ident} ===") == 1, entrada
    assert texto.count(f"# === fin {ident} ===") == 1, entrada
    assert texto.index(f"# === {ident} ===") < texto.index(f"# === fin {ident} ===")


@pytest.mark.parametrize("ruta", PASILLOS)
def test_secciones_no_anidadas_y_sin_import_superior_de_features(ruta):
    texto = (RAIZ / ruta).read_text(encoding="utf-8")
    abierta = None
    for linea in texto.splitlines():
        if m := re.fullmatch(r"# === fin ([A-Za-z0-9-]+) ===", linea):
            assert abierta == m.group(1), linea
            abierta = None
        elif m := re.fullmatch(r"# === ([A-Za-z0-9-]+) ===", linea):
            assert abierta is None, linea
            abierta = m.group(1)
    assert abierta is None
    for nodo in ast.parse(texto).body:
        if isinstance(nodo, ast.ImportFrom):
            assert not (nodo.module or "").startswith("features"), ruta
        elif isinstance(nodo, ast.Import):
            assert not any(a.name.startswith("features") for a in nodo.names), ruta
    importlib.import_module(ruta[:-3].replace("/", "."))
