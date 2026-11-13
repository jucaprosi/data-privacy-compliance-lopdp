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


IDS = ["ADPA-03", "ADPA-06", "FIRMA-03", "FE-24", "SEC-13", "SEC-13a", "DEMO-03a"]


@pytest.mark.parametrize("rama, esperado", [
    ("tarea/juan-carlos/adpa-03-roadmap", "ADPA-03"),
    ("tarea/juan-carlos/adpa-06", "ADPA-06"),
    ("tarea/juan-carlos/sec-13a", "SEC-13a"),
    ("tarea/juan-carlos/sec-13", "SEC-13"),
    ("tarea/jose/demo-03a-x", "DEMO-03a"),
    ("tarea/juan-carlos/sec-13ab", None),
    ("tarea/juan-carlos/sec-14", None),
    ("tarea/jose/firma-03", "FIRMA-03"),
    ("feat/fe-24-tablero-sin-cifra-unica", "FE-24"),
    ("tarea/juan-carlos/soporte-arnes", None),
    ("tarea/juan-carlos/adpa-t0-pasillo", None),
    ("dev/juan-carlos", None),
])
def test_la_tarea_sale_del_nombre_de_la_rama(rama, esperado):
    assert vap.id_de_rama(rama, IDS) == esperado


def test_lo_ajeno_queda_fuera_y_lo_propio_dentro():
    propiedad = ("features/rat/**", "tests/test_rat.py", "features/rat/rat_service.py#ADPA-03")
    archivos = ["features/rat/services/x.py", "tests/test_rat.py", "features/roadmap/y.py"]
    assert vap.fuera_de_alcance(archivos, "ADPA-03", propiedad, indice) == ["features/roadmap/y.py"]


def test_los_archivos_de_cierre_no_cuentan_pero_la_ficha_ajena_si():
    archivos = ["governance/tareas/ADPA-03.md", "governance/artefactos/TASKS.md", "governance/tareas/ADPA-04.md"]
    assert vap.fuera_de_alcance(archivos, "ADPA-03", (), indice) == ["governance/tareas/ADPA-04.md"]


def test_el_indice_de_tasks_evydentia_es_archivo_de_cierre():
    archivos = ["governance/artefactos/TASKS.md", "governance/tareas/ADPA-04.md"]
    assert vap.fuera_de_alcance(archivos, "ADPA-03", (), indice) == ["governance/tareas/ADPA-04.md"]


def test_solo_las_tareas_adpa_son_estrictas():
    assert vap.es_estricta("ADPA-03")
    assert not vap.es_estricta("FIRMA-03")


def test_es_estricta_con_sufijo():
    assert vap.es_estricta("ADPA-06a")
    assert not vap.es_estricta("SEC-13a")


_CAB = "diff --git a/x b/x\nindex 1..2 100644\n--- a/x\n+++ b/x\n@@ -3,1 +2,0 @@\n"


@pytest.mark.parametrize("cuerpo, tarea, esperado", [
    ("-ADPA-06|a.py#ADPA-06|motivo\n-ADPA-06|b.py#ADPA-06|motivo\n", "ADPA-06", True),
    ("-ADPA-05|a.py#ADPA-05|motivo\n", "ADPA-06", False),
    ("-ADPA-06|a.py#ADPA-06|m\n-ADPA-05|a.py#ADPA-05|m\n", "ADPA-06", False),
    ("+ADPA-06|nuevo.py#ADPA-06|motivo\n", "ADPA-06", False),
    ("-ADPA-06|a.py#ADPA-06|m\n+ADPA-06|a.py#ADPA-06|otro\n", "ADPA-06", False),
    ("-ADPA-10|a.py#ADPA-10|motivo\n", "ADPA-1", False),
    ("-# Formato: ficha|entrada|motivo.\n", "ADPA-06", False),
    ("", "ADPA-06", False),
])
def test_retira_solo_exenciones_propias(cuerpo, tarea, esperado):
    assert vap.retira_solo_exenciones_propias(_CAB + cuerpo, tarea) is esperado


_SIEMBRA = ("features/formacion/formacion_service.py#FOR-01",)


def test_ci25_m1_borrar_una_exencion_ajena_no_sembrada_queda_rojo():
    diff = _CAB + "-FOR-01|features/otra/x.py#FOR-01|motivo\n"
    assert not vap.retira_solo_exenciones_propias(diff, "ADPA-09", _SIEMBRA)
    assert not vap.retira_solo_exenciones_propias(diff, "ADPA-09")


def test_ci25_m2_borrar_una_ajena_sembrada_queda_verde():
    diff = _CAB + "-FOR-01|features/formacion/formacion_service.py#FOR-01|sección sin marca\n"
    assert vap.retira_solo_exenciones_propias(diff, "ADPA-09", _SIEMBRA)
    assert not vap.retira_solo_exenciones_propias(diff, "ADPA-09")


def test_ci25_m3_anadir_una_linea_queda_rojo_aunque_este_sembrada():
    diff = _CAB + "+FOR-01|features/formacion/formacion_service.py#FOR-01|nueva\n"
    assert not vap.retira_solo_exenciones_propias(diff, "ADPA-09", _SIEMBRA)
    mixto = _CAB + ("-FOR-01|features/formacion/formacion_service.py#FOR-01|m\n"
                    "+ADPA-09|b.py#ADPA-09|m\n")
    assert not vap.retira_solo_exenciones_propias(mixto, "ADPA-09", _SIEMBRA)


def test_ci25_caso_real_adpa09_retira_la_exencion_de_for01(monkeypatch):
    _simular(monkeypatch, ("ADPA-09", ("a.py",)), ["a.py", vap.EXENCIONES])
    tarea = vap._cargar_indice().cargar_tareas()[0][0]
    tarea.siembra = _SIEMBRA
    monkeypatch.setattr(vap, "_diff_de_exenciones", lambda b, c: _CAB
                        + "-FOR-01|features/formacion/formacion_service.py#FOR-01|sección sin marca\n")
    assert vap.main(["--rama", "tarea/juan-carlos/adpa-09", "--base", "b", "--cabeza", "c"]) == 0


@pytest.mark.parametrize("cabecera", ["deleted file mode 100644\n", "rename from x\nrename to y\n"])
def test_borrar_o_renombrar_las_exenciones_queda_fuera(cabecera):
    diff = "diff --git a/x b/x\n" + cabecera + "--- a/x\n+++ /dev/null\n-ADPA-06|a|m\n"
    assert not vap.retira_solo_exenciones_propias(diff, "ADPA-06")


def _simular(monkeypatch, propiedad, archivos):
    tarea = type("Tarea", (), {"id": propiedad[0], "propiedad": propiedad[1],
                               "estado": propiedad[2] if len(propiedad) > 2 else "en_curso"})
    falso = type("Indice", (), {
        "cargar_tareas": staticmethod(lambda: ([tarea], [])),
        "rutas_se_solapan": staticmethod(indice.rutas_se_solapan),
    })
    monkeypatch.setattr(vap, "_cargar_indice", lambda: falso)
    monkeypatch.setattr(vap, "_archivos_del_diff", lambda base, cabeza: archivos)


def test_una_estricta_puede_retirar_sus_exenciones(monkeypatch):
    _simular(monkeypatch, ("ADPA-06", ("a.py",)), ["a.py", vap.EXENCIONES])
    monkeypatch.setattr(vap, "_diff_de_exenciones", lambda b, c: _CAB + "-ADPA-06|a.py#ADPA-06|m\n")
    assert vap.main(["--rama", "tarea/juan-carlos/adpa-06", "--base", "b", "--cabeza", "c"]) == 0


def test_una_estricta_no_puede_tocar_exenciones_ajenas(monkeypatch, capsys):
    _simular(monkeypatch, ("ADPA-06", ("a.py",)), ["a.py", vap.EXENCIONES])
    monkeypatch.setattr(vap, "_diff_de_exenciones", lambda b, c: _CAB + "-ADPA-05|a.py#ADPA-05|m\n")
    assert vap.main(["--rama", "tarea/juan-carlos/adpa-06", "--base", "b", "--cabeza", "c"]) == 1
    assert vap.EXENCIONES in capsys.readouterr().out


def test_una_rama_con_sufijo_se_comprueba(monkeypatch, capsys):
    _simular(monkeypatch, ("SEC-13a", ("a.py",)), ["a.py"])
    assert vap.main(["--rama", "tarea/juan-carlos/sec-13a", "--base", "b", "--cabeza", "c"]) == 0
    assert "SEC-13a solo toca" in capsys.readouterr().out


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


# CI-23 · rama sin ficha: advertir de lo que no tiene dueña viva y opción estricta.
# Mutaciones: ignorar la rama sin id (quita la advertencia y el código 1); quitar la exclusión pmv/.
def _sin_ficha(monkeypatch, rama, opciones=()):
    _simular(monkeypatch, ("FIRMA-03", ("a.py",)), ["a.py", "huerfano.py"])
    return vap.main(["--rama", rama, "--base", "b", "--cabeza", "c", *opciones])


def test_rama_sin_ficha_advierte_del_archivo_sin_duena_y_sale_con_0(monkeypatch, capsys):
    assert _sin_ficha(monkeypatch, "fix/preanalisis") == 0
    salida = capsys.readouterr().out
    assert "::warning::" in salida and "huerfano.py" in salida
    assert "a.py»" not in salida


def test_rama_sin_ficha_con_estricto_sale_con_1(monkeypatch):
    assert _sin_ficha(monkeypatch, "fix/preanalisis", ("--estricto-sin-ficha",)) == 1


def test_rama_sin_ficha_con_todo_en_propiedad_viva_sale_con_0_aun_estricto(monkeypatch, capsys):
    _simular(monkeypatch, ("FIRMA-03", ("a.py",)), ["a.py"])
    assert vap.main(["--rama", "fix/x", "--base", "b", "--cabeza", "c", "--estricto-sin-ficha"]) == 0
    assert "::warning::" not in capsys.readouterr().out


def test_una_ficha_hecha_no_es_duena_viva(monkeypatch, capsys):
    _simular(monkeypatch, ("FIRMA-03", ("a.py",), "hecha"), ["a.py"])
    assert vap.main(["--rama", "fix/x", "--base", "b", "--cabeza", "c", "--estricto-sin-ficha"]) == 1
    assert "a.py" in capsys.readouterr().out


def test_pmv_hacia_pmv_consolidacion_no_se_marca_ni_con_estricto(monkeypatch, capsys):
    assert _sin_ficha(monkeypatch, "pmv/aleczandra/tema",
                      ("--estricto-sin-ficha", "--destino", "pmv/consolidacion")) == 0
    assert "::warning::" not in capsys.readouterr().out


def test_pmv_hacia_main_con_estricto_sale_con_1(monkeypatch, capsys):
    assert _sin_ficha(monkeypatch, "pmv/x", ("--estricto-sin-ficha", "--destino", "main")) == 1
    assert "huerfano.py" in capsys.readouterr().out


def test_pmv_sin_destino_advierte_y_con_estricto_sale_con_1(monkeypatch, capsys):
    assert _sin_ficha(monkeypatch, "pmv/x") == 0
    assert "::warning::" in capsys.readouterr().out
    assert _sin_ficha(monkeypatch, "pmv/x", ("--estricto-sin-ficha",)) == 1


def test_salida_sin_ficha_para_el_workflow(monkeypatch, tmp_path):
    salida = tmp_path / "salida.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(salida))
    _sin_ficha(monkeypatch, "fix/preanalisis")
    assert "sin_ficha=true" in salida.read_text(encoding="utf-8")


def test_una_rama_con_ficha_sigue_igual_con_la_opcion(monkeypatch):
    _simular(monkeypatch, ("FIRMA-03", ("a.py",)), ["ajeno.py"])
    assert vap.main(["--rama", "tarea/jose/firma-03", "--base", "b", "--cabeza", "c",
                     "--estricto-sin-ficha"]) == 0


# Regla del CTO (2026-11-13): cualquier ficha, estricta o no, solo puede BORRAR sus propias líneas.
@pytest.mark.parametrize("cuerpo, esperado", [
    ("-DPO-03|a.py#DPO-03|m\n", 0),                     # borrar la propia → verde
    ("+DPO-03|b.py#DPO-03|m\n", 1),                     # mutación: añadir línea → rojo
    ("-ORG-20|c.py#ORG-20|m\n", 1),                     # mutación: borrar la de otra ficha → rojo
])
def test_exenciones_no_estricta_solo_borra_las_propias(monkeypatch, cuerpo, esperado):
    _simular(monkeypatch, ("DPO-03", ("a.py",)), ["a.py", vap.EXENCIONES])
    monkeypatch.setattr(vap, "_diff_de_exenciones", lambda b, c: _CAB + cuerpo)
    assert vap.main(["--rama", "tarea/juan-carlos/dpo-03", "--base", "b", "--cabeza", "c"]) == esperado
