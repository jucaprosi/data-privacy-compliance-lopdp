# ¤¤qa-engineer
"""Un PR de tarea no toca archivos ajenos; en las tareas estrictas eso lo rechaza el CI."""
import importlib.util
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("verificar_alcance_pr", RAIZ / "scripts" / "verificar_alcance_pr.py")
vap = importlib.util.module_from_spec(_spec)
sys.modules["verificar_alcance_pr"] = vap
_spec.loader.exec_module(vap)
indice = vap._cargar_indice()


@pytest.mark.parametrize("rama, esperado", [
    ("tarea/juan-carlos/adpa-03-roadmap", "ADPA-03"),
    ("tarea/jose/firma-03", "FIRMA-03"),
    ("feat/fe-24-tablero-sin-cifra-unica", "FE-24"),
    ("tarea/juan-carlos/soporte-arnes", None),
    ("tarea/juan-carlos/adpa-t0-pasillo", None),
    ("dev/juan-carlos", None),
])
def test_la_tarea_sale_del_nombre_de_la_rama(rama, esperado):
    assert vap.id_de_rama(rama) == esperado


def test_lo_ajeno_queda_fuera_y_lo_propio_dentro():
    propiedad = ("features/rat/**", "tests/test_rat.py", "features/rat/rat_service.py#ADPA-03")
    archivos = ["features/rat/services/x.py", "tests/test_rat.py", "features/roadmap/y.py"]
    assert vap.fuera_de_alcance(archivos, "ADPA-03", propiedad, indice) == ["features/roadmap/y.py"]


def test_los_archivos_de_cierre_no_cuentan_pero_la_ficha_ajena_si():
    archivos = ["governance/tareas/ADPA-03.md", "governance/artefactos/TASKS.md", "governance/tareas/ADPA-04.md"]
    assert vap.fuera_de_alcance(archivos, "ADPA-03", (), indice) == ["governance/tareas/ADPA-04.md"]


def test_solo_las_tareas_adpa_son_estrictas():
    assert vap.es_estricta("ADPA-03")
    assert not vap.es_estricta("FIRMA-03")


def _simular(monkeypatch, propiedad, archivos):
    tarea = type("Tarea", (), {"id": propiedad[0], "propiedad": propiedad[1]})
    falso = type("Indice", (), {
        "cargar_tareas": staticmethod(lambda: ([tarea], [])),
        "rutas_se_solapan": staticmethod(indice.rutas_se_solapan),
    })
    monkeypatch.setattr(vap, "_cargar_indice", lambda: falso)
    monkeypatch.setattr(vap, "_archivos_del_diff", lambda base, cabeza: archivos)


def test_una_tarea_estricta_con_archivo_ajeno_falla(monkeypatch, capsys):
    _simular(monkeypatch, ("ADPA-03", ("a.py",)), ["a.py", "ajeno.py"])
    assert vap.main(["--rama", "tarea/juan-carlos/adpa-03-x", "--base", "b", "--cabeza", "c"]) == 1
    assert "ajeno.py" in capsys.readouterr().out


def test_otra_tarea_con_archivo_ajeno_solo_avisa(monkeypatch, capsys):
    _simular(monkeypatch, ("FIRMA-03", ("a.py",)), ["ajeno.py"])
    assert vap.main(["--rama", "tarea/jose/firma-03", "--base", "b", "--cabeza", "c"]) == 0
    assert "solo aviso" in capsys.readouterr().out


def test_una_rama_sin_ficha_no_se_comprueba(monkeypatch):
    _simular(monkeypatch, ("ADPA-03", ("a.py",)), ["ajeno.py"])
    assert vap.main(["--rama", "tarea/juan-carlos/soporte-arnes", "--base", "b", "--cabeza", "c"]) == 0


def test_el_ci_ejecuta_el_arbitro_en_cada_pr_con_historial_completo():
    flujo = (RAIZ / ".github" / "workflows" / "zero-regression-pipeline.yml").read_text(encoding="utf-8")
    assert "scripts/verificar_alcance_pr.py" in flujo
    assert "fetch-depth: 0" in flujo
    assert "github.event_name == 'pull_request'" in flujo
