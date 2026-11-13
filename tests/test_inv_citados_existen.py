# -*- coding: utf-8 -*-
# ¤invariantes
# ¤arbitro
"""PRD-02: todo `INV_` citado fuera de los archivos inhabilitados y de los aportes existe en el archivo de EVYDENTIA.

Mutación documentada: borrar de `INVARIANTS.md` uno de los invariantes heredados
(por ejemplo `INV_LOPDP_MULTIDIMENSIONAL_METRICS`) hace fallar la primera prueba.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO = "governance/artefactos/INVARIANTS.md"
EXCLUIDOS = (
    "governance/artefactos/INVARIANTS.md",
    "governance/artefactos/PRD.md",
    "governance/artefactos/TASKS.md",
    "governance/artefactos/VPA_MAP.md",
    "governance/artefactos/APORTES_INEDITOS.md",
    ARCHIVO,
)
PATRON = r"INV_[A-Z0-9_]*[A-Z0-9]"
PREFIJOS = {"INV_LOPDP"}  # prefijo escrito en prosa, no un invariante


def _citados() -> set[str]:
    pathspec = [".", *(f":!{e}" for e in EXCLUIDOS)]
    salida = subprocess.run(
        ["git", "grep", "-h", "-o", "-E", PATRON, "--", *pathspec],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
    )
    return set(salida.stdout.split()) - PREFIJOS


def _definidos(texto: str) -> set[str]:
    return set(re.findall(PATRON, texto))


def test_todo_inv_citado_existe_en_el_archivo_de_evydentia():
    definidos = _definidos((RAIZ / ARCHIVO).read_text(encoding="utf-8"))
    faltan = sorted(_citados() - definidos)
    assert not faltan, f"INV citados que no están en {ARCHIVO}: {faltan}"


def test_la_prueba_detecta_un_heredado_borrado():
    heredado = "INV_LOPDP_" + "MULTIDIMENSIONAL_METRICS"
    texto = (RAIZ / ARCHIVO).read_text(encoding="utf-8")
    mutado = texto.replace(heredado, "SIN_ID")
    assert heredado in _citados()
    assert heredado in _definidos(texto)
    assert heredado in _citados() - _definidos(mutado)
