# ¤¤qa-engineer
"""El paso de CI compara base y repositorio, solo lee y no imprime la conexión."""
import importlib.util
import sqlite3
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("verificar_revision_alembic", RAIZ / "scripts" / "verificar_revision_alembic.py")
vra = importlib.util.module_from_spec(_spec)
sys.modules["verificar_revision_alembic"] = vra
_spec.loader.exec_module(vra)


def _base(tmp_path: Path, revision: str | None) -> str:
    ruta = tmp_path / "b.db"
    with sqlite3.connect(ruta) as conexion:
        conexion.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
        if revision:
            conexion.execute("INSERT INTO alembic_version VALUES (?)", (revision,))
    return f"sqlite:///{ruta}"


def test_el_repositorio_tiene_una_sola_cabeza():
    assert len(vra.cabezas_del_repositorio()) == 1


def test_coinciden_pasa_e_imprime_las_dos(tmp_path, monkeypatch, capsys):
    cabeza = next(iter(vra.cabezas_del_repositorio()))
    monkeypatch.setenv("TEST_DATABASE_URL", _base(tmp_path, cabeza))
    assert vra.main() == 0
    salida = capsys.readouterr().out
    assert f"alembic current: {cabeza}" in salida and f"alembic heads:   {cabeza}" in salida


def test_revision_ajena_falla_y_la_nombra(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("TEST_DATABASE_URL", _base(tmp_path, "revision_que_no_existe"))
    assert vra.main() == 1
    assert "revision_que_no_existe" in capsys.readouterr().out


def test_base_sin_revision_falla(tmp_path, monkeypatch):
    monkeypatch.setenv("TEST_DATABASE_URL", _base(tmp_path, None))
    assert vra.main() == 1


def test_sin_url_no_se_puede_comprobar(monkeypatch):
    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)
    assert vra.main() == 2


def test_un_error_de_conexion_no_imprime_la_url(monkeypatch, capsys):
    secreto = "postgresql://usuario:clave-secreta@host-invisible:1/base"
    monkeypatch.setenv("TEST_DATABASE_URL", secreto)

    def falla(_url):
        raise RuntimeError(secreto)

    monkeypatch.setattr(vra, "revision_de_la_base", falla)
    assert vra.main() == 2
    salida = capsys.readouterr().out
    assert "clave-secreta" not in salida and "host-invisible" not in salida


def test_el_paso_va_antes_de_pytest_y_no_migra():
    flujo = (RAIZ / ".github" / "workflows" / "zero-regression-pipeline.yml").read_text(encoding="utf-8")
    assert flujo.index("scripts/verificar_revision_alembic.py") < flujo.index("run: pytest tests/ -v")
    assert "alembic upgrade" not in flujo
