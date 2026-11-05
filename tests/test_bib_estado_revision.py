# ¤rbac-tenant
"""El estado del documento solo cambia por funciones acotadas: lopdp_app no tiene UPDATE (estado)."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_servicio_no_actualiza_estado_del_documento_directamente():
    fuente = (ROOT / "features/biblioteca/services/revision_aprobacion.py").read_text(encoding="utf-8")
    assert not re.search(r"UPDATE\s+biblioteca_documentos\s+SET\s+estado", fuente)
    assert "biblioteca_enviar_documento_a_revision" in fuente
    assert "biblioteca_devolver_documento" in fuente


def test_migracion_concede_solo_ejecucion_de_las_funciones():
    sql = (ROOT / "alembic/versions/20261117_bib_estado_revision.py").read_text(encoding="utf-8")
    assert "SECURITY DEFINER" in sql and "GRANT UPDATE" not in sql
    assert sql.count("current_setting('app.current_tenant_id', true)") == 2
