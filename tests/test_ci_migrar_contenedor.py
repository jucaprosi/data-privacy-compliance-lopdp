# ¤¤qa-engineer
# ¤arbitro
"""CI-17 / CI-18: en el CI la migración es un único paso local, sin secretos y siempre.

Estas guardias vivían junto al verificador de revisión que CI-18 retiró; la comprobación pasó a verificar_cloudsql_conexion.py.
"""
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent


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
def test_migrar_va_antes_de_pytest_en_los_dos_arneses():
    for trabajo, siguiente, pytest_del_trabajo in (("arnes-salas:", "arnes-completo:", "pytest $PRUEBAS -v"),
                                                   ("arnes-completo:", "zero-regression:", "run: pytest tests/ -v")):
        texto = FLUJO[FLUJO.index(f"  {trabajo}"):FLUJO.index(f"  {siguiente}")]
        assert texto.index("*migrar_contenedor") < texto.index(pytest_del_trabajo), trabajo


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
    (URL_DEL_PASO, "MIGRATION_DATABASE_URL: postgresql://rol:clave@base-remota.example:5432/lopdp", "servicio local"),
    ("        name: Migrar el contenedor a la cabeza de Alembic\n        env:\n",
     "        name: Migrar el contenedor a la cabeza de Alembic\n        if: needs.alcance.outputs.hacia_main == 'false'\n        env:\n",
     "condición"),
    ("      - name: Install Frontend Dependencies\n", PASO_COPIADO + "      - name: Install Frontend Dependencies\n", "pasos migran"),
])
def test_la_guarda_falla_si_el_paso_de_migrar_apunta_a_una_base_remota(viejo, nuevo, motivo):
    assert viejo in FLUJO
    assert any(motivo in fallo for fallo in fallos_al_migrar(FLUJO.replace(viejo, nuevo, 1)))
