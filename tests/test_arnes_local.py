# ¤¤qa-engineer
"""El arnés rápido solo conoce una base local; sin --base corre todas las pruebas y con --base declara su alcance."""
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

RAIZ = Path(__file__).resolve().parent.parent


def _cargar(nombre):
    spec = importlib.util.spec_from_file_location(nombre, RAIZ / "verificadores" / f"{nombre}.py")
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo
    spec.loader.exec_module(modulo)
    return modulo


arnes = _cargar("arnes_local")
runner = _cargar("arnes_cero_regresiones")


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
    assert arnes.main([]) == 2
    assert "verificadores/README.md" in capsys.readouterr().out


def test_sin_alcance_el_runner_corre_toda_la_carpeta_de_pruebas():
    assert runner.pruebas_a_correr({}) == ["tests/"]
    assert runner.pruebas_a_correr({"ARNES_PRUEBAS": ""}) == ["tests/"]
    assert "arnes_cero_regresiones.py" in (RAIZ / "verificadores" / "arnes_local.py").read_text(encoding="utf-8")


def test_con_alcance_el_runner_corre_solo_la_lista_y_el_certificado_lo_declara():
    assert runner.pruebas_a_correr({"ARNES_PRUEBAS": "tests/test_a.py tests/test_b.py"}) == ["tests/test_a.py", "tests/test_b.py"]
    por_salas = SimpleNamespace(modo="salas", etiqueta="salas: rat", pruebas=["tests/test_a.py", "tests/test_b.py"])
    entorno = arnes.entorno_con_alcance({"X": "1"}, por_salas)
    assert entorno == {"X": "1", "ARNES_ALCANCE": "salas: rat", "ARNES_PRUEBAS": "tests/test_a.py tests/test_b.py"}
    completo = SimpleNamespace(modo="completo", etiqueta="completo", pruebas=[])
    assert arnes.entorno_con_alcance({}, completo) == {"ARNES_ALCANCE": "completo"}
    fuente = (RAIZ / "verificadores" / "arnes_cero_regresiones.py").read_text(encoding="utf-8")
    assert '"alcance": os.environ.get("ARNES_ALCANCE", "completo")' in fuente
