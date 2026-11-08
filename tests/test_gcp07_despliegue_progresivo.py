# ¤¤qa-engineer
"""GCP-07: escalones crecientes hasta 100 % con reversión por SLO, y migraciones expand/contract
(INV_PROGRESSIVE_DELIVERY_EXPAND_CONTRACT)."""
import importlib.util
import json
import sys
from pathlib import Path

import re

import pytest

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("verificar_migracion_compatible",
                                               RAIZ / "scripts" / "verificar_migracion_compatible.py")
vmc = importlib.util.module_from_spec(_spec)
sys.modules["verificar_migracion_compatible"] = vmc
_spec.loader.exec_module(vmc)

def _escalar(valor: str):
    valor = valor.strip()
    if valor.startswith("[") and valor.endswith("]"):
        return [v.strip() for v in valor[1:-1].split(",") if v.strip()]
    return int(valor) if valor.isdigit() else valor


def _leer_yaml(texto: str):
    """Lector mínimo del subconjunto de YAML del manifiesto (el CI no instala PyYAML):
    mapas por sangría, listas de mapas con «- » y listas en línea [a, b]."""
    lineas = [(len(l) - len(l.lstrip(" ")), l.strip()) for l in texto.splitlines()
              if l.strip() and not l.lstrip().startswith("#")]

    def bloque(i: int, sangria: int):
        if lineas[i][1].startswith("- "):
            lista = []
            while i < len(lineas) and lineas[i][0] == sangria and lineas[i][1].startswith("- "):
                lineas[i] = (sangria + 2, lineas[i][1][2:])
                elemento, i = bloque(i, sangria + 2)
                lista.append(elemento)
            return lista, i
        mapa = {}
        while i < len(lineas) and lineas[i][0] == sangria and not lineas[i][1].startswith("- "):
            clave, _, valor = lineas[i][1].partition(":")
            i += 1
            if valor.strip():
                mapa[clave.strip()] = _escalar(valor)
            else:
                mapa[clave.strip()], i = bloque(i, lineas[i][0])
        return mapa, i

    return bloque(0, 0)[0]


MANIFIESTO = _leer_yaml((RAIZ / "governance" / "operaciones" / "despliegue_progresivo.yaml").read_text(encoding="utf-8"))
ALERTAS = json.loads((RAIZ / "governance" / "operaciones" / "monitoreo" / "alertas.json").read_text(encoding="utf-8"))


def test_cubre_los_servicios_de_cloud_run():
    assert set(MANIFIESTO["servicios"]) == {"evydentia-backend", "evydentia-web"}
    for servicio in MANIFIESTO["servicios"].values():
        assert (RAIZ / servicio["manifiesto"]).is_file()


@pytest.mark.parametrize("nombre", ["evydentia-backend", "evydentia-web"])
def test_escalones_crecientes_hasta_100_con_observacion(nombre):
    escalones = MANIFIESTO["servicios"][nombre]["escalones"]
    porcentajes = [e["porcentaje"] for e in escalones]
    assert porcentajes == sorted(set(porcentajes)) and porcentajes[0] > 0 and porcentajes[-1] == 100
    assert porcentajes[:-1] == [10, 50]
    assert all(e["observacion_min"] > 0 for e in escalones)


@pytest.mark.parametrize("nombre", ["evydentia-backend", "evydentia-web"])
def test_la_reversion_se_liga_a_las_alertas_de_ops07(nombre):
    reversion = MANIFIESTO["servicios"][nombre]["reversion"]
    assert reversion["accion"]
    assert {"disponibilidad", "errores_5xx"} <= set(reversion["si_dispara"])
    assert set(reversion["si_dispara"]) <= set(ALERTAS["politicas"])


def test_los_servicios_son_los_neg_serverless_del_balanceador():
    texto = (RAIZ / "governance" / "operaciones" / "cloud_load_balancer.yaml").read_text(encoding="utf-8")
    negs = set(re.findall(r"^\s*neg_serverless:\s*([\w-]+)", texto, flags=re.M))
    assert set(MANIFIESTO["servicios"]) <= negs


def test_el_verificador_va_antes_del_primer_escalon_desde_la_revision_en_servicio():
    previo = MANIFIESTO["previo"]["migraciones"]
    assert "scripts/verificar_migracion_compatible.py" in previo
    assert "--desde-revision" in previo and "--base" not in previo


ADITIVA = '''
def upgrade():
    op.add_column("users", sa.Column("alias", sa.String(), nullable=True))
    op.add_column("users", sa.Column("nivel", sa.Integer(), nullable=False, server_default="0"))
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
    'op.add_column("users", sa.Column("alias", sa.String(), nullable=False))',
    'op.alter_column("users", "alias", type_=sa.Text())',
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


def test_la_contraccion_admite_cambio_de_tipo_y_columna_obligatoria():
    codigo = ('CONTRACCION = True\n\ndef upgrade():\n    op.alter_column("u", "a", type_=sa.Text())\n'
              '    op.add_column("u", sa.Column("b", sa.String(), nullable=False))\n')
    assert vmc.verificar(codigo) == []


def _migracion(directorio, rev, abajo, cuerpo):
    (directorio / f"{rev}.py").write_text(
        f"revision = {rev!r}\ndown_revision = {abajo!r}\nbranch_labels = None\ndepends_on = None\n\n"
        f"def upgrade():\n    {cuerpo}\n\ndef downgrade():\n    pass\n", encoding="utf-8")


def test_desde_revision_detecta_la_destructiva_posterior(tmp_path, capsys, monkeypatch):
    (tmp_path / "versions").mkdir()
    _migracion(tmp_path / "versions", "r1", None, 'op.drop_column("u", "vieja")')
    _migracion(tmp_path / "versions", "r2", "r1", 'op.add_column("u", sa.Column("x", sa.String()))')
    _migracion(tmp_path / "versions", "r3", "r2", 'op.drop_column("u", "x")')
    original = vmc.migraciones_desde_revision
    assert {p.name for p in original("r1", tmp_path)} == {"r2.py", "r3.py"}  # r1 ya está en la base
    monkeypatch.setattr(vmc, "migraciones_desde_revision", lambda rev: original(rev, tmp_path))
    assert vmc.main(["--desde-revision", "r1"]) == 1
    assert "INCOMPATIBLE: r3.py" in capsys.readouterr().out
    assert vmc.main(["--desde-revision", "r3"]) == 0


def test_desde_revision_recorre_el_grafo_real_del_repositorio():
    assert vmc.migraciones_desde_revision("heads") == []
    assert len(vmc.migraciones_desde_revision("001")) > 10
