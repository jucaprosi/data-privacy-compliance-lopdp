"""DER-07 · Los textos de la interfaz de derechos no llevan artículo, unidad ni plazo equivocados.

`¤regulation-code` `¤frontend-ide` `¤arbitro`

Lee los tres archivos de la ficha como texto: sin base de datos ni navegador. La mutación es
reponer cualquiera de las cadenas viejas en un archivo: la prueba falla y nombra cuál.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
ARCHIVOS = (
    "frontend/src/types/arco.ts",
    "frontend/src/components/modules/ArcoModule.tsx",
    "frontend/src/components/CommandPalette.tsx",
)
# Cadenas viejas: artículo equivocado (el 37 es de seguridad), unidad laborable, SLA y 72 h.
PROHIBIDAS = {
    "Art. 37": re.compile(r"Art\.? ?37"),
    "laborables": re.compile(r"laborables?", re.IGNORECASE),
    "SLA": re.compile(r"\bSLA\b"),
    "72h": re.compile(r"72 ?h", re.IGNORECASE),
}


def _texto(ruta: str) -> str:
    return (RAIZ / ruta).read_text(encoding="utf-8")


@pytest.mark.parametrize("ruta", ARCHIVOS)
@pytest.mark.parametrize("nombre", PROHIBIDAS)
def test_sin_cadenas_equivocadas(ruta: str, nombre: str):
    hallazgos = [
        f"{i}: {linea.strip()}"
        for i, linea in enumerate(_texto(ruta).splitlines(), start=1)
        if PROHIBIDAS[nombre].search(linea)
    ]
    assert not hallazgos, f"{ruta} aún dice «{nombre}»: {hallazgos}"


def test_el_modulo_muestra_plazo_estimado_y_aviso():
    modulo = _texto("frontend/src/components/modules/ArcoModule.tsx")
    assert "Plazo legal estimado" in modulo
    assert "arts. 13 a 16" in modulo and "Art. 62" not in modulo
    assert 'data-testid="aviso-plazo-provisional"' in modulo
    assert 'role="note"' in modulo
    assert "ShieldAlert" in modulo and 'aria-hidden="true"' in modulo


def test_la_paleta_no_promete_cifras_de_incidentes():
    paleta = _texto("frontend/src/components/CommandPalette.tsx")
    assert "Ir al Playbook de Incidentes" in paleta
    assert "con plazo legal estimado" in paleta
