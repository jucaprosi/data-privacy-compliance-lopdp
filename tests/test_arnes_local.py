# ¤¤qa-engineer
"""El arnés rápido solo conoce una base local; sin --base corre todas las pruebas y con --base declara su alcance."""
import importlib.util
import re
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


def test_cada_worktree_tiene_su_base_y_es_estable():
    uno = Path("C:/repo/.claude/worktrees/ci-09-6bef26")
    otro = Path("C:/repo/.claude/worktrees/ci-07-71bcde")
    assert arnes.nombre_de_base(uno) == arnes.nombre_de_base(uno)
    assert arnes.nombre_de_base(uno) != arnes.nombre_de_base(otro)
    assert arnes.nombre_de_base(uno) != arnes.nombre_de_base(Path("D:/copia/.claude/worktrees/ci-09-6bef26"))
    assert arnes.nombre_de_base(RAIZ) == arnes.BASE and f"/{arnes.BASE}" in arnes.URL_LOCAL


def test_el_nombre_es_valido_y_deja_sitio_al_sufijo_del_clon():
    largo = Path("C:/Plataforma LOPDP 360/" + "Carpeta Ñandú-" * 12)
    nombre = arnes.nombre_de_base(largo)
    assert re.fullmatch(r"[a-z][a-z0-9_]*", nombre)
    assert len(nombre) <= arnes.LARGO_MAXIMO_DE_BASE
    assert len(f"{nombre}_gw127_abcdef01") <= 63


def test_el_barrido_no_toca_bases_de_otros_worktrees(monkeypatch):
    base = arnes.BASE
    sentencias = []

    def psql(carpeta, sentencia):
        sentencias.append(sentencia)
        if sentencia.startswith("SELECT"):
            return "\n".join(["postgres", "lopdp", base, f"{base}_gw3_abc", "lopdp_otro_12345678", "lopdp_otro_12345678_gw0_abc"])
        return ""

    monkeypatch.setattr(arnes, "_psql", psql)
    arnes.borrar_clones_huerfanos(Path("."))
    assert sentencias[1:] == [f'DROP DATABASE IF EXISTS "{base}_gw3_abc" WITH (FORCE)']


def test_limpiar_borra_solo_lo_de_este_worktree(monkeypatch):
    base = arnes.BASE
    sentencias = []
    monkeypatch.setattr(arnes, "iniciar_servidor", lambda carpeta: None)
    monkeypatch.setattr(arnes, "_psql", lambda c, s: sentencias.append(s) or ("lopdp_otro_12345678" if s.startswith("SELECT") else ""))
    assert arnes.limpiar(Path(".")) == 0
    assert sentencias[1:] == [f'DROP DATABASE IF EXISTS "{base}" WITH (FORCE)']


def test_el_entorno_activa_el_paralelo_sin_perder_las_opciones_heredadas():
    assert arnes.entorno_de_pruebas({})["PYTEST_ADDOPTS"] == arnes.OPCIONES_PARALELO
    assert "-n auto" in arnes.OPCIONES_PARALELO
    assert arnes.entorno_de_pruebas({"PYTEST_ADDOPTS": "-x"})["PYTEST_ADDOPTS"] == f"-x {arnes.OPCIONES_PARALELO}"


def test_xdist_se_instala_solo_si_falta(monkeypatch):
    llamadas = []
    monkeypatch.setattr(arnes.subprocess, "run", lambda orden, **_: llamadas.append(orden))
    monkeypatch.setattr(arnes.importlib.util, "find_spec", lambda nombre: object())
    arnes.preparar_xdist()
    assert llamadas == []
    monkeypatch.setattr(arnes.importlib.util, "find_spec", lambda nombre: None)
    arnes.preparar_xdist()
    assert llamadas == [[sys.executable, "-m", "pip", "install", "pytest-xdist"]]


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
