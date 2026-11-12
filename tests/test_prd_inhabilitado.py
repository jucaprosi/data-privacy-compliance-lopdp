# -*- coding: utf-8 -*-
# ¤triaje
# ¤arbitro
"""PRD-03: los cuatro artefactos anteriores llevan el aviso de inhabilitado y nada de scripts/ ni tests/ los abre.

Mutación documentada: quitar el aviso de uno de los cuatro archivos hace fallar la primera prueba.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
NOMBRES = ("PRD", "INVARIANTS", "TASKS", "VPA_MAP")
RUTAS = tuple(f"governance/artefactos/{n}.md" for n in NOMBRES)
AVISO = "Inhabilitado desde 2026-11-11"
PERMITIDOS = {"tests/test_prd_inhabilitado.py", "scripts/verificar_alcance_pr.py"}


@pytest.mark.parametrize("ruta", RUTAS)
def test_el_archivo_lleva_el_aviso_de_inhabilitado(ruta):
    texto = (RAIZ / ruta).read_text(encoding="utf-8")
    assert AVISO in texto.split("\n---", 1)[0], f"{ruta} no lleva el aviso en su cabecera"
    assert "PRD_EVYDENTIA_REVENTA_NUBE.md" in texto.split("\n---", 1)[0]


def test_ningun_script_ni_prueba_abre_los_inhabilitados():
    salida = subprocess.run(
        ["git", "grep", "-l", "-F", *sum((["-e", r] for r in RUTAS), []), "--", "scripts", "tests"],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
    )
    leen = sorted(set(salida.stdout.split()) - PERMITIDOS)
    assert not leen, f"Leen o citan un artefacto inhabilitado: {leen}"
