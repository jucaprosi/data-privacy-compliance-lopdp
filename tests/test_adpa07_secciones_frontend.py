# ¤adpa ¤frontend-ide
"""ADPA-07: secciones `INICIO <ID>` / `FIN <ID>` sembradas en registros y componentes compartidos del frontend.

Cada ficha escribe solo entre sus marcas; esta prueba comprueba que existen, que están equilibradas
y que cada INICIO precede a su FIN.
"""
from pathlib import Path
import re

import pytest

RAIZ = Path(__file__).resolve().parents[1] / "frontend" / "src"
REGISTROS = ["CAPA-04", "DIAG-07", "DPO-03", "FIRMA-02", "FOR-01", "INC-02", "MTGE-03", "ORG-18", "ORG-20", "CON-01"]

ESPERADO = {
    "components/layout/menus/index.ts": REGISTROS,
    "components/layout/pantallas/index.tsx": REGISTROS,
    "components/layout/DashboardHeader.tsx": ["FE-25"],
    "store/useBibliotecaStore.ts": ["BIB-110"],
    "components/DiagnosticCanvas.tsx": ["EVI-01", "DIAG-05", "DIAG-07"],
    "components/modules/EvidenciasModule.tsx": ["EVI-01", "EVI-02"],
}

MARCA = re.compile(r"(?://|\{/\*) --- (INICIO|FIN) ([A-Z]+-\d+[a-z]?) ---")

CASOS = [(archivo, ident) for archivo, ids in ESPERADO.items() for ident in ids]


def _marcas(archivo: str) -> list[tuple[str, str]]:
    return MARCA.findall((RAIZ / archivo).read_text(encoding="utf-8"))


@pytest.mark.parametrize("archivo,ident", CASOS)
def test_seccion_sembrada(archivo: str, ident: str) -> None:
    marcas = _marcas(archivo)
    assert ("INICIO", ident) in marcas, f"falta INICIO {ident} en {archivo}"
    assert ("FIN", ident) in marcas, f"falta FIN {ident} en {archivo}"


@pytest.mark.parametrize("archivo", list(ESPERADO))
def test_secciones_equilibradas_y_sin_anidar(archivo: str) -> None:
    abierta = None
    for tipo, ident in _marcas(archivo):
        if tipo == "INICIO":
            assert abierta is None, f"{ident} se abre dentro de {abierta} en {archivo}"
            abierta = ident
        else:
            assert abierta == ident, f"FIN {ident} sin su INICIO en {archivo}"
            abierta = None
    assert abierta is None, f"{abierta} queda abierta en {archivo}"
