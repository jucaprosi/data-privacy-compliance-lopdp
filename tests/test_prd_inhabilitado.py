# -*- coding: utf-8 -*-
# ¤triaje
# ¤arbitro
"""PRD-03: los cuatro artefactos anteriores llevan el aviso de inhabilitado y ningún .py de scripts/ ni tests/ los abre.

El análisis es con `ast`: se buscan las cuatro rutas en las constantes de cadena que no son docstring. Los .txt y .md
quedan fuera, y una ruta dentro de un docstring no cuenta (la prueba m3 fija ese falso positivo).

Mutaciones documentadas:
  m1  quitar el aviso de uno de los cuatro archivos: la primera prueba da rojo.
  m2  un .py simulado con Path('governance/artefactos/PRD.md').read_text(): da rojo.
  m3  la misma ruta en un docstring: NO da rojo.
  m4  un quinto archivo en las excepciones: la prueba de la lista cerrada da rojo.
"""
from __future__ import annotations

import ast
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
NOMBRES = ("PRD", "INVARIANTS", "TASKS", "VPA_MAP")
RUTAS = tuple(f"governance/artefactos/{n}.md" for n in NOMBRES)
AVISO = "Inhabilitado desde 2026-11-11"
EXCEPCIONES = {
    "tests/test_prd_inhabilitado.py": "esta prueba nombra las cuatro rutas",
    "scripts/verificar_alcance_pr.py": "trata TASKS.md como archivo de cierre",
    "tests/test_verificar_alcance_pr.py": "prueba ese comportamiento",
    "tests/test_inv_citados_existen.py": "las saca del barrido con «:!ruta»; no las abre",
}


@pytest.mark.parametrize("ruta", RUTAS)
def test_el_archivo_lleva_el_aviso_de_inhabilitado(ruta):
    cabecera = (RAIZ / ruta).read_text(encoding="utf-8").split("\n---", 1)[0]
    assert AVISO in cabecera, f"{ruta} no lleva el aviso en su cabecera"
    assert "PRD_EVYDENTIA_REVENTA_NUBE.md" in cabecera


def _constantes_que_no_son_docstring(codigo: str) -> list[str]:
    arbol = ast.parse(codigo)
    docstrings = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            cuerpo = nodo.body
            if cuerpo and isinstance(cuerpo[0], ast.Expr) and isinstance(cuerpo[0].value, ast.Constant):
                docstrings.add(id(cuerpo[0].value))
    return [
        n.value for n in ast.walk(arbol)
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docstrings
    ]


def _abre_alguno(codigo: str) -> bool:
    return any(r in c for c in _constantes_que_no_son_docstring(codigo) for r in RUTAS)


def _archivos_py() -> list[str]:
    salida = subprocess.run(
        ["git", "ls-files", "scripts", "tests"], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
    )
    return [f for f in salida.stdout.split() if f.endswith(".py")]


def test_ningun_py_abre_los_inhabilitados():
    leen = []
    for relativa in _archivos_py():
        if relativa in EXCEPCIONES:
            continue
        ruta = RAIZ / relativa
        if ruta.exists() and _abre_alguno(ruta.read_text(encoding="utf-8-sig")):
            leen.append(relativa)
    assert not leen, f"Abren un artefacto inhabilitado: {leen}"


def test_las_excepciones_son_exactamente_las_cuatro_aprobadas():
    assert sorted(EXCEPCIONES) == sorted([
        "scripts/verificar_alcance_pr.py",
        "tests/test_inv_citados_existen.py",
        "tests/test_prd_inhabilitado.py",
        "tests/test_verificar_alcance_pr.py",
    ])
    assert all(motivo.strip() for motivo in EXCEPCIONES.values())


def test_m2_una_lectura_con_la_ruta_da_rojo():
    assert _abre_alguno("from pathlib import Path\nPath('governance/artefactos/PRD.md').read_text()\n")


def test_m3_la_ruta_en_un_docstring_no_da_rojo():
    assert not _abre_alguno('"""Cita governance/artefactos/PRD.md."""\nx = 1\n')
