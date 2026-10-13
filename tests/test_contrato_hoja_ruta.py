# ¤roadmap
"""Prueba de integridad del contrato OpenAPI congelado para la Hoja de Ruta Inteligente.

Falla si el contrato OpenAPI expuesto por FastAPI en main.py difiere del archivo
congelado en governance/contratos/hoja_de_ruta.openapi.json.
Esto asegura que cualquier cambio en rutas, esquemas o parámetros deba sincronizarse
explícitamente mediante scripts/exportar_contrato_hoja_ruta.py para los agentes de frontend.
"""
import json
from pathlib import Path

from main import app

RAIZ = Path(__file__).resolve().parent.parent
CONTRATO_FILE = RAIZ / "governance" / "contratos" / "hoja_de_ruta.openapi.json"


def test_contrato_hoja_de_ruta_sincronizado():
    """Valida que governance/contratos/hoja_de_ruta.openapi.json refleje exactamente app.openapi()."""
    assert CONTRATO_FILE.exists(), (
        f"El archivo de contrato no existe en {CONTRATO_FILE}. "
        "Ejecuta: python scripts/exportar_contrato_hoja_ruta.py"
    )

    contrato_guardado = json.loads(CONTRATO_FILE.read_text(encoding="utf-8"))
    esquema_actual = app.openapi()

    assert esquema_actual == contrato_guardado, (
        "El contrato OpenAPI actual difiere de governance/contratos/hoja_de_ruta.openapi.json. "
        "Ejecuta python scripts/exportar_contrato_hoja_ruta.py para sincronizar el contrato."
    )
