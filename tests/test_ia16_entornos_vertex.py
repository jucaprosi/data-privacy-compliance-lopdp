# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤qa-engineer
# ¤gemini-vertex
# ¤arbitro
"""IA-16: el entorno de la demo y el brief del propietario fijan Vertex AI en `us` (generar) y `us-central1` (vectores)."""
from __future__ import annotations

from pathlib import Path

from tests._lector_yaml import leer_yaml

RAIZ = Path(__file__).resolve().parent.parent
YAML_DEMO = RAIZ / "governance" / "operaciones" / "entornos" / "demo" / "cloudrun_backend.yaml"
BRIEF = RAIZ / "governance" / "operaciones" / "BRIEF_PROPIETARIO_VERTEX.md"
PRUEBAS = RAIZ / "governance" / "operaciones" / "PRUEBAS_EN_FISICO.md"


def _env_demo() -> dict[str, str]:
    doc = leer_yaml(YAML_DEMO.read_text(encoding="utf-8"))
    if isinstance(doc, list):  # varios documentos `---`: el servicio de Cloud Run
        doc = next(d for d in doc if isinstance(d, dict) and d.get("kind") == "Service")
    entorno = doc["spec"]["template"]["spec"]["containers"][0]["env"]
    return {e["name"]: e["value"] for e in entorno if "value" in e}


def test_demo_declara_generacion_en_us():
    assert _env_demo().get("VERTEX_LOCATION") == "us"


def test_demo_declara_vectores_en_us_central1():
    assert _env_demo().get("VERTEX_LOCATION_EMBEDDING") == "us-central1"


def test_brief_cubre_los_tres_entornos_y_las_dos_variables():
    texto = BRIEF.read_text(encoding="utf-8")
    for proyecto in ("evydentia-demo", "evydentia-pruebas", "evydentia"):
        assert proyecto in texto
    assert "VERTEX_LOCATION=us" in texto
    assert "VERTEX_LOCATION_EMBEDDING=us-central1" in texto
    assert "aiplatform.googleapis.com" in texto
    assert "roles/aiplatform.user" in texto
    assert "3 passed" in texto


def test_brief_no_conserva_la_region_antigua_para_generar():
    assert "VERTEX_LOCATION=us-central1" not in BRIEF.read_text(encoding="utf-8")


def test_pruebas_en_fisico_documenta_el_humo_en_dos_regiones():
    texto = PRUEBAS.read_text(encoding="utf-8")
    assert "VERTEX_LOCATION=us" in texto or '$env:VERTEX_LOCATION = "us"' in texto
    assert "VERTEX_LOCATION_EMBEDDING" in texto
    assert "VERTEX_LOCATION=us-central1" not in texto
