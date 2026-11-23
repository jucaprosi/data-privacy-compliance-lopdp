# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
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


def test_seccion_existe_y_cierra():
    fallos = []
    for entrada in SECCIONES:
        ruta, ident = entrada.split("#")
        texto = (RAIZ / ruta).read_text(encoding="utf-8")
        if texto.count(f"# === {ident} ===") != 1:
            fallos.append(f"{entrada}: marca # === {ident} === no aparece exactamente 1 vez (aparece {texto.count(f'# === {ident} ===')})")
        elif texto.count(f"# === fin {ident} ===") != 1:
            fallos.append(f"{entrada}: marca # === fin {ident} === no aparece exactamente 1 vez (aparece {texto.count(f'# === fin {ident} ===')})")
        elif texto.index(f"# === {ident} ===") >= texto.index(f"# === fin {ident} ==="):
            fallos.append(f"{entrada}: marca fin precede a marca inicio")
    assert not fallos, f"Fallos en seccion_existe_y_cierra ({len(fallos)}/{len(SECCIONES)}):\n" + "\n".join(fallos)


def test_secciones_no_anidadas_y_sin_import_superior_de_features():
    fallos = []
    for ruta in PASILLOS:
        texto = (RAIZ / ruta).read_text(encoding="utf-8")
        abierta = None
        for linea in texto.splitlines():
            if m := re.fullmatch(r"# === fin ([A-Za-z0-9-]+) ===", linea):
                if abierta != m.group(1):
                    fallos.append(f"{ruta}: fin {m.group(1)} no coincide con abierta {abierta}")
                abierta = None
            elif m := re.fullmatch(r"# === ([A-Za-z0-9-]+) ===", linea):
                if abierta is not None:
                    fallos.append(f"{ruta}: seccion {m.group(1)} abierta dentro de {abierta}")
                abierta = m.group(1)
        if abierta is not None:
            fallos.append(f"{ruta}: seccion {abierta} no se cerro")
        for nodo in ast.parse(texto).body:
            if isinstance(nodo, ast.ImportFrom):
                if (nodo.module or "").startswith("features"):
                    fallos.append(f"{ruta}: import de nivel superior de {nodo.module}")
            elif isinstance(nodo, ast.Import):
                for a in nodo.names:
                    if a.name.startswith("features"):
                        fallos.append(f"{ruta}: import de nivel superior de {a.name}")
        try:
            importlib.import_module(ruta[:-3].replace("/", "."))
        except Exception as exc:
            fallos.append(f"{ruta}: error al importar pasillo: {exc}")
    assert not fallos, f"Fallos en pasillos ({len(fallos)}/{len(PASILLOS)}):\n" + "\n".join(fallos)
