# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
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
    archivos = ["governance/tareas/ADPA-03.md", "governance/apoyo/briefs/ADPA-03.md", "governance/tareas/ADPA-04.md"]
    assert vap.fuera_de_alcance(archivos, "ADPA-03", (), indice) == ["governance/tareas/ADPA-04.md"]


def test_alcance_un_brief_por_ficha_y_tasks_ya_no_es_de_cierre():
    archivos = ["governance/artefactos/TASKS.md", "governance/apoyo/BRIEFS_POR_BLOQUE.md", "governance/apoyo/briefs/ADPA-04.md"]
    assert vap.fuera_de_alcance(archivos, "ADPA-03", (), indice) == archivos


def test_la_portada_solo_entra_en_el_alcance_de_su_dueña():
    # CI-31 R6. Mutación m3: admitir la portada para cualquier ficha vaciaría la lista de la ficha ajena.
    portada = "governance/apoyo/BRIEFS_POR_BLOQUE.md"
    assert vap.fuera_de_alcance([portada], "ADPA-03", ("features/rat/**",), indice) == [portada]
    assert vap.fuera_de_alcance([portada], "ADPA-03", ("governance/apoyo/**",), indice) == [portada]  # un comodín no basta
    assert vap.fuera_de_alcance([portada], "CI-31", (portada, "scripts/x.py"), indice) == []


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


def test_el_brief_propio_es_de_cierre_pero_el_ajeno_no():
    # CI-29: el brief de la ficha vive en governance/apoyo/briefs/<ID>.md
    archivos = ["governance/apoyo/briefs/ADPA-03.md", "governance/apoyo/briefs/ADPA-04.md"]
    assert vap.fuera_de_alcance(archivos, "ADPA-03", (), indice) == ["governance/apoyo/briefs/ADPA-04.md"]

import os
import subprocess

def test_ci26_m1_ruta_con_tilde_en_repo_temporal_no_excede_alcance(tmp_path, monkeypatch):
    # R4 y §5: repo temporal con commit que añade "governance/Metodología de trabajo.md"
    env = dict(os.environ, GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@e.com',
               GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@e.com')
    subprocess.run(['git', 'init'], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(['git', 'checkout', '-b', 'main'], cwd=tmp_path, check=True, capture_output=True)
    f = tmp_path / 'governance' / 'Metodología de trabajo.md'
    f.parent.mkdir(parents=True)
    f.write_text('v1', encoding='utf-8')
    subprocess.run(['git', 'add', '.'], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(['git', 'commit', '-m', 'base'], cwd=tmp_path, env=env, check=True, capture_output=True)
    subprocess.run(['git', 'checkout', '-b', 'tarea/juan-carlos/adpa-26'], cwd=tmp_path, check=True, capture_output=True)
    f.write_text('v2', encoding='utf-8')
    subprocess.run(['git', 'commit', '-am', 'mod'], cwd=tmp_path, env=env, check=True, capture_output=True)

    ruta_tilde = "governance/Metodología de trabajo.md"
    tarea = type("Tarea", (), {"id": "ADPA-26", "propiedad": (ruta_tilde,), "estado": "en_curso"})
    falso = type("Indice", (), {
        "cargar_tareas": staticmethod(lambda: ([tarea], [])),
        "rutas_se_solapan": staticmethod(indice.rutas_se_solapan),
    })
    monkeypatch.setattr(vap, "_cargar_indice", lambda: falso)
    monkeypatch.setattr(vap, "RAIZ", tmp_path)

    # Con el lector real CI-26, no hay exceso de alcance
    assert vap.main(["--rama", "tarea/juan-carlos/adpa-26", "--base", "main", "--cabeza", "tarea/juan-carlos/adpa-26"]) == 0

    # Mutación m1: un lector sin core.quotepath=off produce ruta entre comillas con escapes octales y falla
    def _lector_sin_quotepath_off(base, cabeza, raiz):
        salida = subprocess.run(["git", "diff", "--name-only", f"{base}...{cabeza}"],
                                cwd=raiz, capture_output=True, text=True, check=True).stdout
        return [l.strip() for l in salida.splitlines() if l.strip()]

    monkeypatch.setattr(vap, "_archivos_del_diff", lambda b, c: _lector_sin_quotepath_off(b, c, tmp_path))
    assert vap.main(["--rama", "tarea/juan-carlos/adpa-26", "--base", "main", "--cabeza", "tarea/juan-carlos/adpa-26"]) == 1


def test_ci26_m3_rutas_con_espacio_y_salto_de_linea(tmp_path, monkeypatch):
    _git_diff = vap._cargar_git_diff()
    # Simula salida en bytes de git con rutas conteniendo espacio y salto de línea separadas por NUL
    salida_bytes = b"governance/Metodologia de trabajo.md\x00documentos/archivo\ncon\nsalto.txt\x00"
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: type("Res", (), {"stdout": salida_bytes})())

    rutas = _git_diff.archivos_del_diff("base", "cabeza", tmp_path)
    assert rutas == ["governance/Metodologia de trabajo.md", "documentos/archivo\ncon\nsalto.txt"]

    # Mutación m3: si partiera por '\n' en lugar de '\0', la lista se rompe
    rutas_partidas_por_nl = [r for r in salida_bytes.decode("utf-8").split("\n") if r]
    assert rutas_partidas_por_nl != rutas
