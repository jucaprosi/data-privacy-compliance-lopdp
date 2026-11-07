# ¤¤qa-engineer
# ¤arbitro
"""El verificador de revisión de Alembic solo lee y no imprime la conexión; en el CI la migración es local."""
import importlib.util
import re
import sqlite3
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("verificar_revision_alembic", RAIZ / "scripts" / "verificar_revision_alembic.py")
vra = importlib.util.module_from_spec(_spec)
sys.modules["verificar_revision_alembic"] = vra
_spec.loader.exec_module(vra)


# ¤arbitro
def _base(tmp_path: Path, revision: str | None) -> str:
    ruta = tmp_path / "b.db"
    with sqlite3.connect(ruta) as conexion:
        conexion.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
        if revision:
            conexion.execute("INSERT INTO alembic_version VALUES (?)", (revision,))
    return f"sqlite:///{ruta}"


# ¤arbitro
def test_el_repositorio_tiene_una_sola_cabeza():
    assert len(vra.cabezas_del_repositorio()) == 1


# ¤arbitro
def test_coinciden_pasa_e_imprime_las_dos(tmp_path, monkeypatch, capsys):
    cabeza = next(iter(vra.cabezas_del_repositorio()))
    monkeypatch.setenv("TEST_DATABASE_URL", _base(tmp_path, cabeza))
    assert vra.main() == 0
    salida = capsys.readouterr().out
    assert f"alembic current: {cabeza}" in salida and f"alembic heads:   {cabeza}" in salida


# ¤arbitro
def test_revision_ajena_falla_y_la_nombra(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("TEST_DATABASE_URL", _base(tmp_path, "revision_que_no_existe"))
    assert vra.main() == 1
    assert "revision_que_no_existe" in capsys.readouterr().out


# ¤arbitro
def test_base_sin_revision_falla(tmp_path, monkeypatch):
    monkeypatch.setenv("TEST_DATABASE_URL", _base(tmp_path, None))
    assert vra.main() == 1


# ¤arbitro
def test_sin_url_no_se_puede_comprobar(monkeypatch):
    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)
    assert vra.main() == 2


# ¤arbitro
def test_un_error_de_conexion_no_imprime_la_url(monkeypatch, capsys):
    secreto = "postgresql://usuario:clave-secreta@host-invisible:1/base"
    monkeypatch.setenv("TEST_DATABASE_URL", secreto)

    def falla(_url):
        raise RuntimeError(secreto)

    monkeypatch.setattr(vra, "revision_de_la_base", falla)
    assert vra.main() == 2
    salida = capsys.readouterr().out
    assert "clave-secreta" not in salida and "host-invisible" not in salida


FLUJO = (RAIZ / ".github" / "workflows" / "zero-regression-pipeline.yml").read_text(encoding="utf-8")


# ¤arbitro
def _pasos(flujo: str) -> list[str]:
    """Texto de cada paso sin comentarios: se lee a mano porque PyYAML no es dependencia del proyecto."""
    sin_comentarios = "\n".join(l for l in flujo.splitlines() if not l.strip().startswith("#"))
    return [re.split(r"\n {0,5}\S", p)[0] for p in re.split(r"(?m)^      - ", sin_comentarios)[1:]]


# ¤arbitro
def fallos_al_migrar(flujo: str) -> list[str]:
    """CI-17: migrar solo es admisible en un único paso anclado, siempre y contra el servicio local del runner."""
    pasos = [p for p in _pasos(flujo) if "alembic upgrade" in p]
    if len(pasos) != 1:
        return [f"{len(pasos)} pasos migran; debe haber uno"]
    paso, fallos = pasos[0], []
    if re.search(r"(?m)^\s*if:", paso):
        fallos.append("la condición excluye corridas: el contenedor debe migrarse siempre")
    if "secrets." in paso or "TEST_DATABASE_URL" in paso:
        fallos.append("nombra un secreto o la URL de pruebas externa")
    if "${{" in paso.split("run:")[0].split("env:")[-1]:
        fallos.append("su env no es literal")
    urls = re.findall(r"postgresql://\S+", paso)
    if not urls or not all(re.search(r"@(localhost|127\.0\.0\.1):", u) for u in urls):
        fallos.append("no apunta solo al servicio local")
    return fallos


# ¤arbitro
def test_verificar_va_antes_de_pytest_en_los_trabajos_que_pueden_correr_contra_neon():
    for trabajo, siguiente, pytest_del_trabajo in (("arnes-salas:", "arnes-completo:", "pytest $PRUEBAS -v"),
                                                   ("arnes-completo:", "zero-regression:", "run: pytest tests/ -v")):
        texto = FLUJO[FLUJO.index(f"  {trabajo}"):FLUJO.index(f"  {siguiente}")]
        assert texto.index("*migrar_contenedor") < texto.index(pytest_del_trabajo), trabajo
    assert "scripts/verificar_revision_alembic.py" not in FLUJO


# ¤arbitro
def test_migrar_es_un_solo_paso_local_y_nunca_hacia_main():
    assert fallos_al_migrar(FLUJO) == []
    assert FLUJO.count("&migrar_contenedor") == 1 and FLUJO.count("*migrar_contenedor") == 2


URL_DEL_PASO = "MIGRATION_DATABASE_URL: postgresql://lopdp_beta_owner:solo-en-este-runner@localhost:5432/lopdp"
PASO_COPIADO = "      - name: Otra migracion\n        run: python -m alembic upgrade head\n"


# ¤arbitro
@pytest.mark.parametrize("viejo, nuevo, motivo", [
    (URL_DEL_PASO, "MIGRATION_DATABASE_URL: ${{ secrets.TEST_DATABASE_URL_JUAN_CARLOS }}", "secreto"),
    (URL_DEL_PASO, "MIGRATION_DATABASE_URL: ${{ secrets.OTRA_BASE }}", "secreto"),
    (URL_DEL_PASO, "MIGRATION_DATABASE_URL: ${{ env.TEST_DATABASE_URL }}", "secreto"),
    (URL_DEL_PASO, "MIGRATION_DATABASE_URL: ${{ env.OTRA_BASE }}", "literal"),
    (URL_DEL_PASO, "MIGRATION_DATABASE_URL: postgresql://rol:clave@rama-de-prueba.neon.tech:5432/lopdp", "servicio local"),
    ("        name: Migrar el contenedor a la cabeza de Alembic\n        env:\n",
     "        name: Migrar el contenedor a la cabeza de Alembic\n        if: needs.alcance.outputs.hacia_main == 'false'\n        env:\n",
     "condición"),
    ("      - name: Install Frontend Dependencies\n", PASO_COPIADO + "      - name: Install Frontend Dependencies\n", "pasos migran"),
])
def test_la_guarda_falla_si_el_paso_de_migrar_apunta_a_neon(viejo, nuevo, motivo):
    assert viejo in FLUJO
    assert any(motivo in fallo for fallo in fallos_al_migrar(FLUJO.replace(viejo, nuevo, 1)))
