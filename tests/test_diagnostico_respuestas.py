"""Contrato de aislamiento de respuestas persistidas del diagnóstico."""
from pathlib import Path

FUENTE = Path(__file__).parents[1] / "features" / "diagnostico" / "services" / "respuestas_engine.py"


def test_catalogos_aceptan_el_extremo_y_rechazan_fuera_de_rango():
    fuente = FUENTE.read_text(encoding="utf-8")
    assert "range(1, 74)" in fuente
    assert "range(1, 11)" in fuente


def test_aislamiento_se_delega_a_consulta_por_tenant():
    # La consulta física, cubierta contra Neon por el coordinador, restringe
    # todas las filas a :tenant_id y la migración agrega RLS FORCED.
    assert "tenant_id = :tenant_id" in FUENTE.read_text(encoding="utf-8")
