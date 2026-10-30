# ¤¤qa-engineer
"""El arnés rápido solo conoce una base local y no omite ninguna prueba."""
import importlib.util
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("arnes_local", RAIZ / "verificadores" / "arnes_local.py")
arnes = importlib.util.module_from_spec(_spec)
sys.modules["arnes_local"] = arnes
_spec.loader.exec_module(arnes)


def test_la_url_es_siempre_local():
    assert "@127.0.0.1:" in arnes.URL_LOCAL
    assert "listen_addresses=127.0.0.1" in arnes.AJUSTES_SERVIDOR


def test_el_entorno_sustituye_cualquier_base_heredada():
    heredado = {"TEST_DATABASE_URL": "postgresql://remota/x", "MIGRATION_DATABASE_URL": "postgresql://remota/y", "OTRA": "1"}
    entorno = arnes.entorno_de_pruebas(heredado)
    assert entorno["TEST_DATABASE_URL"] == arnes.URL_LOCAL
    assert entorno["MIGRATION_DATABASE_URL"] == arnes.URL_LOCAL
    assert entorno["OTRA"] == "1" and entorno["ARNES_BASE"] == "postgresql_local"


def test_sin_postgres_termina_con_un_mensaje_claro(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("LOPDP_PG_DIR", str(tmp_path))
    assert arnes.main() == 2
    assert "verificadores/README.md" in capsys.readouterr().out


def test_el_arnes_rapido_corre_la_suite_completa():
    fuente = (RAIZ / "verificadores" / "arnes_cero_regresiones.py").read_text(encoding="utf-8")
    assert '"pytest", "tests/", "-v"' in fuente
    assert "arnes_cero_regresiones.py" in (RAIZ / "verificadores" / "arnes_local.py").read_text(encoding="utf-8")
