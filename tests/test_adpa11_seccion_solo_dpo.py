# ¤adpa ¤frontend-ide
"""ADPA-11: sección #DIAG-14 alrededor de los botones de nivel y de evidencia en DiagnosticCanvas.tsx.

1. Los bloques existen, están equilibrados y contienen los dos grupos de botones, el rango sugerido y el criterio del nivel.
2. Las marcas #DIAG-14 están balanceadas y en orden (mutación: borrar un FIN la hace fallar).
   La comparación contra main era una comprobación del PR de ADPA-11 (#511) y ya cumplió.
3. Las marcas ajenas (#EVI-01, #DIAG-05, #DIAG-07, #DIAG-11) siguen presentes y balanceadas, sin git (el CI clona sin historia).
"""
from pathlib import Path
import re

import pytest

RAIZ = Path(__file__).resolve().parents[1]
RUTA = "frontend/src/components/DiagnosticCanvas.tsx"
MARCA = re.compile(r"(?://|\{/\*) --- (INICIO|FIN) ([A-Z]+-\d+[a-z]?) ---(?: \*/\})?")
AJENAS = ["EVI-01", "DIAG-05", "DIAG-07", "DIAG-11"]


def _bloques(texto: str) -> list[str]:
    return re.findall(r"--- INICIO DIAG-14 ---(.*?)--- FIN DIAG-14 ---", texto, re.S)


def test_bloques_diag14_contienen_los_dos_grupos_de_botones() -> None:
    texto = (RAIZ / RUTA).read_text(encoding="utf-8")
    bloques = _bloques(texto)
    assert any('aria-labelledby="etiqueta-nivel"' in b and "handleSeleccionarNivel" in b for b in bloques)
    assert any('aria-labelledby="etiqueta-evidencia"' in b and "handleSeleccionarEvidencia" in b for b in bloques)


def test_textos_que_invitan_a_elegir_nivel_quedan_dentro_de_diag14() -> None:
    """La nota de DIAG-14 sustituye estos textos para un rol que no es DPO."""
    bloques = _bloques((RAIZ / RUTA).read_text(encoding="utf-8"))
    for marca in ("Elige el nivel", 'data-testid="criterio-nivel"', 'data-testid="rango-sugerido"'):
        assert any(marca in b for b in bloques), f"{marca} queda fuera de #DIAG-14"


def test_secciones_diag14_balanceadas_y_en_orden() -> None:
    """Invariante permanente: cada INICIO DIAG-14 tiene su FIN después, sin anidar."""
    texto = (RAIZ / RUTA).read_text(encoding="utf-8")
    marcas = [tipo for tipo, ident in MARCA.findall(texto) if ident == "DIAG-14"]
    assert len(marcas) >= 4, "faltan las secciones #DIAG-14 de los grupos de nivel y de evidencia"
    assert marcas == ["INICIO", "FIN"] * (len(marcas) // 2), f"secciones #DIAG-14 desbalanceadas: {marcas}"


def test_marcas_ajenas_intactas() -> None:
    """Las secciones ajenas sembradas siguen presentes, balanceadas y sin anidarse con #DIAG-14."""
    texto = (RAIZ / RUTA).read_text(encoding="utf-8")
    abierta = None
    for tipo, ident in MARCA.findall(texto):
        if tipo == "INICIO":
            assert abierta is None, f"{ident} se abre dentro de {abierta}"
            abierta = ident
        else:
            assert abierta == ident, f"FIN {ident} sin su INICIO"
            abierta = None
    assert abierta is None
    for ident in AJENAS:
        if ident == "DIAG-11":  # todavía sin sembrar: no debe aparecer a medias
            assert texto.count(f"--- INICIO {ident} ---") == texto.count(f"--- FIN {ident} ---")
            continue
        assert f"--- INICIO {ident} ---" in texto and f"--- FIN {ident} ---" in texto, ident
