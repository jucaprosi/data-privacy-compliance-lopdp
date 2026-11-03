# ¤ci-cd
# ¤¤qa-engineer
"""La medición de la variación del CI: cálculos con datos sintéticos, sin red."""
import importlib.util
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("medir_variacion_ci", RAIZ / "scripts" / "medir_variacion_ci.py")
mv = importlib.util.module_from_spec(_spec)
sys.modules["medir_variacion_ci"] = mv
_spec.loader.exec_module(mv)

REGISTRO = """\
2026-11-02T16:16:21.1391826Z ##[group]Runner Image Provisioner
2026-11-02T16:16:21.1397943Z Azure Region: westus
2026-11-02T16:17:00.0000000Z tests/test_a.py::uno PASSED [ 10%]
2026-11-02T16:17:02.0000000Z tests/test_a.py::dos[x y] PASSED [ 20%]
2026-11-02T16:17:02.5000000Z tests/test_b.py::uno FAILED [ 30%]
2026-11-02T16:17:03.5000000Z tests/test_b.py::dos SKIPPED [ 40%]
2026-11-02T16:17:03.6000000Z tests/test_c.py::uno PASSED [ 50%]
2026-11-02T16:17:03.8000000Z tests/test_c.py::dos PASSED [ 60%]
2026-11-02T16:17:04.0000000Z ===== 6 passed =====
"""


def _trabajo(nombre="Arnés completo", pytest_="success", turno="success"):
    pasos = [
        {"name": mv.PASO_TURNO, "conclusion": turno},
        {"name": mv.PASOS_PYTEST[0], "conclusion": pytest_, "started_at": "2026-11-02T10:00:00Z",
         "completed_at": "2026-11-02T10:30:00Z"},
    ]
    return {"name": nombre, "steps": pasos}


def _corrida(id_, rama_neon, inicio, fin):
    return mv.Corrida(id_, inicio, fin, 0.0, "Arnés completo", "push", "main", rama_neon, True)


def test_solapadas_cuenta_cruces_y_no_los_bordes():
    otros = [
        ("2026-11-02T09:00:00Z", "2026-11-02T10:30:00Z"),  # entra por la izquierda
        ("2026-11-02T10:10:00Z", "2026-11-02T10:20:00Z"),  # queda dentro
        ("2026-11-02T08:00:00Z", "2026-11-02T10:00:00Z"),  # termina justo al empezar
        ("2026-11-02T11:00:00Z", "2026-11-02T11:30:00Z"),  # después
    ]
    assert mv.solapadas("2026-11-02T10:00:00Z", "2026-11-02T11:00:00Z", otros) == 2


def test_cada_corrida_cuenta_aparte_su_rama_y_las_demas_sin_contarse_a_si_misma():
    a = _corrida(1, "test-main", "2026-11-02T10:00:00Z", "2026-11-02T11:00:00Z")
    b = _corrida(2, "test-main", "2026-11-02T10:30:00Z", "2026-11-02T11:30:00Z")
    c = _corrida(3, "test-jose", "2026-11-02T10:45:00Z", "2026-11-02T10:50:00Z")
    mv.asignar_solapamientos([a, b, c])
    assert (a.solapadas_misma_rama, a.solapadas_otra_rama) == (1, 1)
    assert (c.solapadas_misma_rama, c.solapadas_otra_rama) == (0, 2)


def test_el_registro_da_region_mediana_y_control_sin_base():
    r = mv.analizar_registro(REGISTRO, {"tests/test_c.py"})
    assert r.region == "westus"
    assert r.pruebas == 6
    assert r.mediana_con_consulta_ms == 1000.0  # 2,0 s, 0,5 s y 1,0 s
    assert r.media_sin_base_ms == 150.0  # 0,1 s y 0,2 s
    assert r.primera_con_consulta_s == 2.0


def test_una_prueba_que_no_llega_a_neon_no_cuenta_como_consulta():
    texto = "2026-11-02T16:17:00.0000000Z tests/test_a.py::uno PASSED\n2026-11-02T16:17:00.0100000Z tests/test_a.py::dos PASSED\n"
    assert mv.analizar_registro(texto, set()).mediana_con_consulta_ms is None


def test_un_registro_sin_datos_no_inventa_cifras():
    r = mv.analizar_registro("nada que ver", set())
    assert (r.region, r.pruebas, r.mediana_con_consulta_ms, r.media_sin_base_ms) == (None, 0, None, None)


@pytest.mark.parametrize(("rama", "esperada"), [
    ("main", "test-main"), ("dev/jose", "test-jose"), ("tarea/juan-carlos/ci-12", "test-juan-carlos"), ("otra", "test-main"),
])
def test_la_rama_neon_sigue_la_regla_del_flujo(rama, esperada):
    assert mv.rama_neon(rama) == esperada


def test_un_pr_hacia_main_cuenta_como_hacia_main():
    run = {"id": 1, "event": "pull_request", "head_branch": "dev/jose", "pull_requests": [{"base": {"ref": "main"}}]}
    corrida = mv.corrida_del_trabajo(run, _trabajo())
    assert (corrida.hacia_main, corrida.minutos) == (True, 30.0)


@pytest.mark.parametrize("trabajo", [
    _trabajo(pytest_="skipped"), _trabajo(turno="skipped"), _trabajo(nombre="Playwright Frontend"),
])
def test_se_descartan_contenedor_y_otros_trabajos(trabajo):
    assert mv.corrida_del_trabajo({"id": 1, "event": "push", "head_branch": "main"}, trabajo) is None


@pytest.mark.parametrize("trabajo", [_trabajo(pytest_="failure"), _trabajo(nombre="Arnés por salas")])
def test_fallos_y_salas_ocupan_la_rama_pero_no_se_miden(trabajo):
    corrida = mv.corrida_del_trabajo({"id": 1, "event": "push", "head_branch": "main"}, trabajo)
    assert corrida is not None and corrida.medible is False


def test_el_reposo_es_el_tiempo_desde_la_ultima_corrida_de_esa_rama():
    a = _corrida(1, "test-main", "2026-11-02T10:00:00Z", "2026-11-02T10:30:00Z")
    b = _corrida(2, "test-main", "2026-11-02T11:00:00Z", "2026-11-02T11:30:00Z")
    c = _corrida(3, "test-jose", "2026-11-02T10:45:00Z", "2026-11-02T10:50:00Z")
    mv.asignar_solapamientos([a, b, c])
    assert (a.reposo_min, b.reposo_min, c.reposo_min) == (None, 30.0, None)


def test_la_varianza_explicada_separa_grupos_de_ruido():
    assert mv.varianza_explicada([[1.0, 1.0], [5.0, 5.0]]) == pytest.approx(1.0)
    assert mv.varianza_explicada([[1.0, 5.0], [1.0, 5.0]]) == pytest.approx(0.0)
    assert mv.varianza_explicada([[2.0, 2.0]]) is None


def test_las_relativas_descuentan_la_mediana_de_cada_region():
    def corrida(region, minutos):
        c = _corrida(1, "test-main", "2026-11-02T10:00:00Z", "2026-11-02T10:30:00Z")
        c.region, c.minutos, c.pruebas = region, minutos, 60
        return c

    pares = mv.relativas([corrida("este", 5), corrida("este", 10), corrida("oeste", 30), corrida("oeste", 60)])
    assert sorted(round(r, 2) for _, r in pares) == [0.67, 0.67, 1.33, 1.33]


def test_el_paso_de_turno_no_existia_en_las_corridas_antiguas():
    trabajo = _trabajo(nombre="Arnés Físico Determinista")
    trabajo["steps"].pop(0)
    assert mv.corrida_del_trabajo({"id": 1, "event": "push", "head_branch": "main"}, trabajo) is not None


def test_spearman_ve_el_orden_con_empates_y_rechaza_lo_constante():
    assert mv.spearman([1, 2, 3, 4], [10, 20, 30, 1000]) == pytest.approx(1.0)
    assert mv.spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    assert mv.spearman([1, 1, 2, 3], [1, 1, 2, 3]) == pytest.approx(1.0)
    assert mv.spearman([1, 2, 3], [5, 5, 5]) is None
