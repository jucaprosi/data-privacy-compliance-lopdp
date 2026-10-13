# ¤roadmap
"""Script de exportación del contrato OpenAPI para el módulo Hoja de Ruta Inteligente.

Genera governance/contratos/hoja_de_ruta.openapi.json a partir del esquema OpenAPI
de la aplicación FastAPI en main.py.
"""
from pathlib import Path
import json
import sys

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from main import app

CONTRATOS_DIR = RAIZ / "governance" / "contratos"
CONTRATO_FILE = CONTRATOS_DIR / "hoja_de_ruta.openapi.json"


def exportar_contrato() -> Path:
    """Exporta el esquema OpenAPI completo al archivo congelado de contrato."""
    CONTRATOS_DIR.mkdir(parents=True, exist_ok=True)
    schema = app.openapi()
    contenido = json.dumps(schema, indent=2, ensure_ascii=False) + "\n"
    CONTRATO_FILE.write_text(contenido, encoding="utf-8")
    return CONTRATO_FILE


if __name__ == "__main__":
    destino = exportar_contrato()
    print(f"Contrato OpenAPI exportado exitosamente a: {destino}")
