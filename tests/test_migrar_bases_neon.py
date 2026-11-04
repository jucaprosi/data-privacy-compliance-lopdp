# ¤¤qa-engineer
"""Migrar las bases de Neon solo desde main: omite lo que no debe tocar y nunca imprime una conexión."""
import importlib.util
import sqlite3
import sys
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

RAIZ = Path(__file__).resolve().parent.parent
for _nombre in ("verificar_revision_alembic", "migrar_bases_neon"):
    _spec = importlib.util.spec_from_file_location(_nombre, RAIZ / "scripts" / f"{_nombre}.py")
    _modulo = importlib.util.module_from_spec(_spec)
    sys.modules[_nombre] = _modulo
    _spec.loader.exec_module(_modulo)
mbn = sys.modules["migrar_bases_neon"]
vra = sys.modules["verificar_revision_alembic"]

CABEZA = next(iter(vra.cabezas_del_repositorio()))
# La primera revisión de la cadena: main la conoce, pero no es la cabeza. Una base ahí está atrasada.
_config = Config(str(RAIZ / "alembic.ini"))
_config.set_main_option("script_location", str(RAIZ / "alembic"))
RAIZ_DE_LA_CADENA = ScriptDirectory.from_config(_config).get_base()
EN_MAIN = {"GITHUB_ACTIONS": "true", "GITHUB_REF": "refs/heads/main"}


def _base(tmp_path: Path, nombre: str, revision: str | None) -> str:
    ruta = tmp_path / f"{nombre}.db"
    with sqlite3.connect(ruta) as conexion:
        conexion.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
        if revision:
            conexion.execute("INSERT INTO alembic_version VALUES (?)", (revision,))
    return f"sqlite:///{ruta}"


def _llevar_a(url: str, revision: str) -> None:
    ruta = url.removeprefix("sqlite:///")
    with sqlite3.connect(ruta) as conexion:
        conexion.execute("DELETE FROM alembic_version")
        conexion.execute("INSERT INTO alembic_version VALUES (?)", (revision,))


class MigrarSimulado:
    """Hace de alembic: anota qué URL migró y deja la base en la revisión que se le indique."""

    def __init__(self, resultado: int = 0, texto: str = "", destino: str = CABEZA):
        self.urls: list[str] = []
        self.resultado, self.texto, self.destino = resultado, texto, destino

    def __call__(self, url: str) -> tuple[int, str]:
        self.urls.append(url)
        if self.resultado == 0:
            _llevar_a(url, self.destino)
        return self.resultado, self.texto


def test_el_repositorio_tiene_una_sola_cabeza():
    assert len(vra.cabezas_del_repositorio()) == 1


def test_sin_secretos_no_hace_nada(capsys):
    migrar = MigrarSimulado()
    assert mbn.main(entorno={}, migrar=migrar) == 0
    assert migrar.urls == []
    assert "no hay nada que migrar" in capsys.readouterr().out


def test_base_al_dia_no_se_migra(tmp_path, capsys):
    url = _base(tmp_path, "uno", CABEZA)
    migrar = MigrarSimulado()
    assert mbn.main(entorno={"NEON_MIGRACION_URL_JOSE": url}, migrar=migrar) == 0
    assert migrar.urls == []
    assert "test-jose: AL DÍA" in capsys.readouterr().out


def test_base_atrasada_se_migra_a_la_cabeza(tmp_path, capsys):
    url = _base(tmp_path, "atrasada", "revision_vieja_que_main_no_tiene")
    raiz = RAIZ_DE_LA_CADENA
    _llevar_a(url, raiz)
    migrar = MigrarSimulado()
    assert mbn.main(entorno={"NEON_MIGRACION_URL_ALECZANDRA": url}, migrar=migrar) == 0
    assert migrar.urls == [url]
    assert f"test-aleczandra: MIGRADA: {raiz} a {CABEZA}" in capsys.readouterr().out


def test_base_por_delante_de_main_no_se_toca(tmp_path, capsys):
    url = _base(tmp_path, "adelante", "revision_de_un_pr_que_main_no_conoce")
    migrar = MigrarSimulado()
    assert mbn.main(entorno={"NEON_MIGRACION_URL_JUAN_CARLOS": url}, migrar=migrar) == 0
    assert migrar.urls == []
    assert "OMITIDA" in capsys.readouterr().out


def test_base_sin_revision_no_se_crea_desde_cero(tmp_path, capsys):
    url = _base(tmp_path, "vacia", None)
    migrar = MigrarSimulado()
    assert mbn.main(entorno={"NEON_MIGRACION_URL_MAIN": url}, migrar=migrar) == 0
    assert migrar.urls == []
    assert "no tiene revisión de Alembic" in capsys.readouterr().out


def test_un_fallo_sale_con_1_y_no_imprime_la_conexion(tmp_path, capsys):
    raiz = RAIZ_DE_LA_CADENA
    url = _base(tmp_path, "falla", raiz)
    secreta = "postgresql://lopdp_beta_owner:contrasena-secreta@ep-ejemplo.neon.tech/db"
    migrar = MigrarSimulado(resultado=1, texto=f"sqlalchemy.exc.OperationalError: no conecta a {secreta}\n")
    assert mbn.main(entorno={"NEON_MIGRACION_URL_JOSE": url}, migrar=migrar) == 1
    salida = capsys.readouterr().out
    assert "FALLO" in salida
    assert "contrasena-secreta" not in salida and "ep-ejemplo" not in salida


def test_migrar_que_no_llega_a_la_cabeza_es_fallo(tmp_path, capsys):
    raiz = RAIZ_DE_LA_CADENA
    url = _base(tmp_path, "incompleta", raiz)
    migrar = MigrarSimulado(destino=raiz)  # dice que migró pero la base sigue donde estaba
    if raiz == CABEZA:  # cadena de una sola revisión: no hay estado intermedio que simular
        return
    assert mbn.main(entorno={"NEON_MIGRACION_URL_MAIN": url}, migrar=migrar) == 1
    assert "tras migrar quedó en" in capsys.readouterr().out


def test_una_base_que_falla_no_impide_migrar_las_demas(tmp_path, capsys):
    raiz = RAIZ_DE_LA_CADENA
    mala = _base(tmp_path, "mala", raiz)
    buena = _base(tmp_path, "buena", raiz)

    def migrar(url: str) -> tuple[int, str]:
        if url == mala:
            return 1, "fallo simulado"
        _llevar_a(url, CABEZA)
        return 0, ""

    codigo = mbn.main(entorno={"NEON_MIGRACION_URL_MAIN": mala, "NEON_MIGRACION_URL_JOSE": buena}, migrar=migrar)
    salida = capsys.readouterr().out
    assert codigo == 1
    assert "test-main: FALLO" in salida and "test-jose: MIGRADA" in salida


def test_fuera_de_main_no_corre_ni_lee_nada(capsys):
    def leer(_url):
        raise AssertionError("no debe leer ninguna base")

    entorno = {"GITHUB_ACTIONS": "true", "GITHUB_REF": "refs/heads/dev/aleczandra", "NEON_MIGRACION_URL_JOSE": "x"}
    assert mbn.main(entorno=entorno, leer=leer, migrar=MigrarSimulado()) == 2
    assert "Solo corre sobre main" in capsys.readouterr().out


def test_en_main_si_corre(tmp_path):
    url = _base(tmp_path, "enmain", CABEZA)
    assert mbn.main(entorno={**EN_MAIN, "NEON_MIGRACION_URL_MAIN": url}, migrar=MigrarSimulado()) == 0


def test_las_conexiones_se_enmascaran():
    texto = "falló postgresql://u:p@h/db y también postgresql+psycopg://u:p@h2:5432/db?sslmode=require fin"
    limpio = mbn.sin_conexiones(texto)
    assert "u:p@" not in limpio and limpio.count("***") == 2 and limpio.endswith("fin")
