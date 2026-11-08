"""TEST-05: el medidor de pruebas redundantes marca candidatas, mutantes, duraciones y rutas sin tocar pruebas."""
# ¤arbitro
# ¤¤qa-engineer
import importlib.util
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("medir_redundancia_pruebas", RAIZ / "scripts" / "medir_redundancia_pruebas.py")
m = importlib.util.module_from_spec(_spec)
sys.modules["medir_redundancia_pruebas"] = m
_spec.loader.exec_module(m)


def L(archivo, *nums):
    return {(archivo, n) for n in nums}


def test_sala_de_archivo():
    assert m.sala_de_archivo("features/rat/service.py") == "rat"
    assert m.sala_de_archivo("app_core/db/session.py") == "app_core"
    assert m.sala_de_archivo("api/v1.py") == "api"
    assert m.sala_de_archivo("scripts/x.py") == "scripts"
    assert m.sala_de_archivo("main.py") == "otros"


def test_sala_de_prueba_es_la_de_mas_lineas():
    lineas = L("features/rat/a.py", 1, 2, 3) | L("app_core/x.py", 1)
    assert m.sala_de_prueba(lineas) == "rat"
    assert m.sala_de_prueba(set()) == "sin-cobertura"


def test_nodo_de_contexto():
    assert m.nodo_de_contexto("tests/t.py::C::p[1]|run") == "tests/t.py::C::p[1]"
    assert m.nodo_de_contexto("") == ""


def test_candidata_contenida_en_otra_de_la_misma_sala():
    datos = {
        "t::chica": L("features/rat/a.py", 1, 2),
        "t::grande": L("features/rat/a.py", 1, 2, 3),
        "t::otra_sala": L("features/terceros/b.py", 1, 2, 3, 4),
    }
    c = m.buscar_candidatas(datos)
    assert [(x.prueba, x.contenedora, x.sala) for x in c] == [("t::chica", "t::grande", "rat")]
    assert c[0].recomendacion == "pendiente de mutación"


def test_iguales_marca_solo_una():
    datos = {"t::a": L("features/rat/a.py", 1), "t::b": L("features/rat/a.py", 1)}
    c = m.buscar_candidatas(datos)
    assert [(x.prueba, x.contenedora) for x in c] == [("t::b", "t::a")]


def test_no_cruza_salas_ni_marca_sin_cobertura():
    datos = {"t::a": L("features/rat/a.py", 1), "t::b": L("features/terceros/a.py", 1), "t::vacia": set()}
    assert m.buscar_candidatas(datos) == []


def test_recomendaciones_segun_el_criterio():
    c = m.Candidata("p", "q", "rat", 2, 2, mutaciones_probadas=3)
    assert c.recomendacion == "retirar"
    c.lineas = 1
    assert c.recomendacion == "fusionar"
    c.mutaciones_exclusivas.append("features/rat/a.py:1")
    assert c.recomendacion == "conservar"
    assert m.Candidata("p", "q", "rat", 1, 2, mutaciones_probadas=3, error_real=True).recomendacion == "conservar"


def test_mutantes_cambian_un_operador_y_respetan_sangria():
    mutantes = m.mutantes_de_linea("    if a == b and c:  # nota\n")
    assert "    if a != b and c:\n" in mutantes
    assert "    if a == b or c:\n" in mutantes
    assert all(x.startswith("    ") and x.endswith("\n") for x in mutantes)
    assert m.mutantes_de_linea("def f(x):\n") == []
    assert m.mutantes_de_linea("# solo comentario\n") == []
    assert "    return None\n" in m.mutantes_de_linea("    return total\n")


def test_resultados_de_salida():
    salida = "PASSED tests/a.py::t1\nFAILED tests/a.py::t2 - assert\n"
    assert m.resultados_de_salida(salida, ["tests/a.py::t1", "tests/a.py::t2"]) == {
        "tests/a.py::t1": True, "tests/a.py::t2": False}


def test_duraciones_desde_list_de_un_log_de_ci():
    log = (
        "Playwright\t2026-11-07T22:57:30Z   ✓    1 [produccion] › tests/api/x.spec.ts:36:7 › a › b (35ms)\n"
        "Playwright\t2026-11-07T22:57:32Z   ✓    4 [produccion] › tests/api/x.spec.ts:22:5 › c (1.8s)\n"
        "  ✘    9 [desarrollo] › tests/roadmap/y.spec.ts:1:1 › d (1.5m)\n"
        "ruido sin duración\n"
    )
    d = m.duraciones_desde_list(log)
    assert d["tests/api/x.spec.ts"]["pruebas"] == 2
    assert abs(d["tests/api/x.spec.ts"]["duracion_s"] - 1.835) < 1e-9
    assert d["tests/roadmap/y.spec.ts"]["duracion_s"] == 90.0


def test_duraciones_desde_json():
    datos = {"suites": [{"specs": [], "suites": [{"specs": [
        {"file": "roadmap/y.spec.ts", "tests": [{"results": [{"duration": 1500}, {"duration": 500}]}]}]}]}]}
    assert m.duraciones_desde_json(datos) == {"tests/roadmap/y.spec.ts": {"duracion_s": 2.0, "pruebas": 1}}


def test_rutas_de_spec_y_recorridos_repetidos():
    texto = "await page.goto(`/roadmap/${id}?x=1`);\nawait page.goto('/');\nexpect(page).toHaveURL('/login');\n" \
            "await page.goto('https://externo.invalid/');"
    assert m.rutas_de_spec(texto) == ["/", "/login", "/roadmap/:param"]
    grupos = m.recorridos_repetidos({"a": ["/x"], "b": ["/x"], "c": ["/y"], "d": []})
    assert grupos == [["a", "b"]]
    assert m.sala_de_spec("tests/biblioteca/ficha.spec.ts") == "biblioteca"
    assert m.sala_de_spec("tests/commandPalette.spec.ts") == "raiz"


def test_informe_lista_pytest_y_playwright_por_sala():
    c = m.Candidata("t::chica", "t::grande", "rat", 2, 3, mutaciones_probadas=2,
                    mutaciones_exclusivas=["features/rat/a.py:7"])
    texto = m.escribir_informe([c], 2, {"rat": 2}, {"tests/rat/x.spec.ts": {"duracion_s": 4.0, "pruebas": 2}},
                               {"tests/rat/x.spec.ts": ["/rat"]}, "registro de prueba")
    assert "### Sala `rat`" in texto and "`features/rat/a.py:7`" in texto and "| conservar |" in texto
    assert "`tests/rat/x.spec.ts` | 2 | 4.0 | `/rat`" in texto


def test_nacio_por_error_real_lee_docstring(tmp_path, monkeypatch):
    (tmp_path / "t.py").write_text('def test_x():\n    """Regresión del 2026: fallaba."""\n', encoding="utf-8")
    (tmp_path / "u.py").write_text('def test_y():\n    """Comprueba la suma."""\n', encoding="utf-8")
    monkeypatch.setattr(m, "RAIZ", tmp_path)
    assert m.nacio_por_error_real("t.py::test_x") is True
    assert m.nacio_por_error_real("u.py::test_y") is False
    assert m.nacio_por_error_real("no_existe.py::t") is False


def test_variante_parametrizada_se_conserva():
    c = m.Candidata("t.py::f[b]", "t.py::f[a]", "rat", 3, 3, mutaciones_probadas=3)
    assert c.recomendacion == "conservar (variante parametrizada)"
