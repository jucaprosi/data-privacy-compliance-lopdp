# -*- coding: utf-8 -*-
# ¤¤qa-engineer
# ¤arbitro
"""CI-17: ningún workflow usa Neon y tanto PR como push a main usan el contenedor PostgreSQL 16 del runner."""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
WORKFLOWS = RAIZ / ".github" / "workflows"
FLUJO_CI = WORKFLOWS / "zero-regression-pipeline.yml"

NOMBRES_TRABAJOS_ESPERADOS = [
    ("alcance", "Alcance de la corrida"),
    ("humo", "Humo de extremo a extremo"),
    ("arnes-salas", "Arnés por salas"),
    ("arnes-completo", "Arnés completo"),
    ("zero-regression", "Arnés Físico Determinista"),
    ("playwright", "Playwright Frontend"),
]


# ¤arbitro
def test_ningun_workflow_referencia_neon_ni_test_main():
    archivos = sorted(WORKFLOWS.glob("*.yml"))
    assert archivos, "No se encontraron workflows en .github/workflows/"
    for ruta in archivos:
        texto = ruta.read_text(encoding="utf-8")
        assert not re.search(r"neon", texto, re.IGNORECASE), f"{ruta.name} menciona neon"
        assert "test-main" not in texto, f"{ruta.name} menciona test-main"
        assert "esperar_turno_neon" not in texto, f"{ruta.name} menciona esperar_turno_neon"
        assert "migrar_bases_neon" not in texto, f"{ruta.name} menciona migrar_bases_neon"
        assert "migrar-bases-neon" not in texto, f"{ruta.name} menciona migrar-bases-neon"


# ¤arbitro
def test_archivos_de_neon_retirados():
    retirados = (
        ".github/workflows/migrar-bases-neon.yml",
        "scripts/esperar_turno_neon.py",
        "tests/test_esperar_turno_neon.py",
        "scripts/migrar_bases_neon.py",
        "tests/test_migrar_bases_neon.py",
    )
    for relativo in retirados:
        assert not (RAIZ / relativo).exists(), f"Debe haberse borrado {relativo}"


# ¤arbitro
def test_el_push_a_main_y_los_pr_usan_el_mismo_contenedor_postgres16():
    flujo = FLUJO_CI.read_text(encoding="utf-8")
    assert "services: &postgres_de_las_ramas\n      postgres:\n        image: pgvector/pgvector:pg16\n" in flujo
    assert flujo.count("services: *postgres_de_las_ramas") == 2
    assert "env: &base_de_pruebas\n      TEST_DATABASE_URL: postgresql://lopdp_beta_owner:solo-en-este-runner@localhost:5432/lopdp\n" in flujo
    assert flujo.count("env: *base_de_pruebas") == 2
    assert "secrets.TEST_DATABASE_URL" not in flujo


# ¤arbitro
def test_nombres_de_trabajos_intactos():
    flujo = FLUJO_CI.read_text(encoding="utf-8")
    trabajos = re.findall(r"(?m)^  ([a-z-]+):\n(?:    #[^\n]*\n)*    name: ([^\n]+)$", flujo)
    assert trabajos == NOMBRES_TRABAJOS_ESPERADOS


# ¤arbitro
def test_documentos_historicos_de_neon_llevan_nota_ci17():
    for doc in ("VARIACION_NEON_CI.md", "RAMAS_NEON_DE_DESARROLLO.md"):
        ruta = RAIZ / "governance" / "operaciones" / doc
        encabezado = "\n".join(ruta.read_text(encoding="utf-8").splitlines()[:10])
        assert "CI-17" in encabezado, f"Falta nota de CI-17 al inicio de {doc}"
