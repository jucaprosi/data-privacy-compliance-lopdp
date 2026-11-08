# ¤¤qa-engineer
"""GCP-07: escalones crecientes hasta 100 % con reversión por SLO, y migraciones expand/contract
(INV_PROGRESSIVE_DELIVERY_EXPAND_CONTRACT)."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("verificar_migracion_compatible",
                                               RAIZ / "scripts" / "verificar_migracion_compatible.py")
vmc = importlib.util.module_from_spec(_spec)
sys.modules["verificar_migracion_compatible"] = vmc
_spec.loader.exec_module(vmc)

MANIFIESTO = yaml.safe_load((RAIZ / "governance" / "operaciones" / "despliegue_progresivo.yaml").read_text(encoding="utf-8"))
ALERTAS = json.loads((RAIZ / "governance" / "operaciones" / "monitoreo" / "alertas.json").read_text(encoding="utf-8"))


def test_cubre_los_servicios_de_cloud_run():
    assert set(MANIFIESTO["servicios"]) == {"evydentia-api", "evydentia-web"}
    for servicio in MANIFIESTO["servicios"].values():
        assert (RAIZ / servicio["manifiesto"]).is_file()


@pytest.mark.parametrize("nombre", ["evydentia-api", "evydentia-web"])
def test_escalones_crecientes_hasta_100_con_observacion(nombre):
    escalones = MANIFIESTO["servicios"][nombre]["escalones"]
    porcentajes = [e["porcentaje"] for e in escalones]
    assert porcentajes == sorted(set(porcentajes)) and porcentajes[0] > 0 and porcentajes[-1] == 100
    assert porcentajes[:-1] == [10, 50]
    assert all(e["observacion_min"] > 0 for e in escalones)


@pytest.mark.parametrize("nombre", ["evydentia-api", "evydentia-web"])
def test_la_reversion_se_liga_a_las_alertas_de_ops07(nombre):
    reversion = MANIFIESTO["servicios"][nombre]["reversion"]
    assert reversion["accion"]
    assert {"disponibilidad", "errores_5xx"} <= set(reversion["si_dispara"])
    assert set(reversion["si_dispara"]) <= set(ALERTAS["politicas"])


def test_el_verificador_de_migraciones_va_antes_del_primer_escalon():
    assert "scripts/verificar_migracion_compatible.py" in MANIFIESTO["previo"]["migraciones"]


ADITIVA = '''
def upgrade():
    op.add_column("users", sa.Column("alias", sa.String(), nullable=True))
    op.create_table("notas", sa.Column("id", sa.Integer()))
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_x")

def downgrade():
    op.drop_column("users", "alias")
    op.drop_table("notas")
'''


@pytest.mark.parametrize("cuerpo", [
    'op.drop_column("users", "google_sub")',
    'op.drop_table("notas")',
    'op.rename_table("notas", "apuntes")',
    'op.alter_column("users", "alias", new_column_name="apodo")',
    'op.execute("ALTER TABLE users DROP COLUMN alias")',
    'op.execute("ALTER TABLE users RENAME COLUMN alias TO apodo")',
    'op.execute("DROP TABLE notas")',
])
def test_rechaza_una_migracion_destructiva(cuerpo):
    assert vmc.verificar(f"def upgrade():\n    {cuerpo}\n")


def test_acepta_una_aditiva_aunque_su_downgrade_borre():
    assert vmc.verificar(ADITIVA) == []


def test_acepta_la_contraccion_declarada_aparte():
    assert vmc.verificar('CONTRACCION = True\n\ndef upgrade():\n    op.drop_column("users", "alias")\n') == []


def test_main_devuelve_1_ante_una_destructiva(tmp_path, capsys):
    destructiva = tmp_path / "m1.py"
    destructiva.write_text('def upgrade():\n    op.drop_column("users", "alias")\n', encoding="utf-8")
    aditiva = tmp_path / "m2.py"
    aditiva.write_text(ADITIVA, encoding="utf-8")
    assert vmc.main([str(aditiva)]) == 0
    assert vmc.main([str(destructiva)]) == 1
    assert "INCOMPATIBLE: m1.py" in capsys.readouterr().out
