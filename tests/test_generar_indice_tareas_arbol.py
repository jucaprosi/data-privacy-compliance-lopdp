"""ADPA-10 · R-PROP-EXISTE: la propiedad de cada ficha se comprueba contra el árbol (¤arbitro).

Árbol sintético inyectado: ninguna prueba toca el disco ni git. Diseño en
governance/apoyo/DISENO_PROPIEDAD_CONTRA_ARBOL.md (§2, reglas 1 a 4; §7, pruebas y mutaciones).

Mutaciones que estas pruebas matan (comprobadas a mano al implementar ADPA-10):
- M1: si validar_contra_arbol devuelve siempre [] o ignora las entradas con «#»,
  falla test_m1_ruta_equivocada_con_seccion_sugiere_la_real (y la prueba 1a).
- M2: si acepta como creadora a una ficha que no es ancestro, falla la prueba 2c.
- M3: si compara la marca solo por el nombre de archivo y no por la ruta, falla la prueba 1a
  (otro archivo con el mismo nombre sí tiene la marca).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_RUTA = Path(__file__).resolve().parent.parent / "scripts" / "generar_indice_tareas.py"
if "generar_indice_tareas" in sys.modules:
    git = sys.modules["generar_indice_tareas"]
else:
    _spec = importlib.util.spec_from_file_location("generar_indice_tareas", _RUTA)
    git = importlib.util.module_from_spec(_spec)
    sys.modules["generar_indice_tareas"] = git
    _spec.loader.exec_module(git)


def _t(tid, propiedad, depende=(), crea=(), siembra=(), estado="pendiente"):
    return git.Tarea(id=tid, titulo=tid, ola="A", estado=estado, sala="s", depende_de=tuple(depende),
                     propiedad=tuple(propiedad), arbitro="pytest", crea=tuple(crea), siembra=tuple(siembra))


def _errores(tareas, archivos):
    """archivos: {ruta: contenido}. Devuelve los mensajes de error (sin avisos)."""
    hallazgos = git.validar_contra_arbol(tareas, set(archivos), lambda r: archivos.get(r, ""), "HEAD abc1234")
    return [h.mensaje for h in hallazgos if h.nivel == "error"]


# 1 · sección en un archivo que existe ---------------------------------------------------------

def test_1a_seccion_sin_marca_rechaza():
    # M3: «otro/y.py» tiene la marca, pero «x/y.py» no; comparar por nombre la daría por buena
    archivos = {"x/y.py": "codigo\n", "otro/y.py": "# === A ===\n# === fin A ===\n"}
    errores = _errores([_t("A", ["x/y.py#A"])], archivos)
    assert errores and "marca" in errores[0] and "x/y.py" in errores[0]


def test_1b_seccion_con_marca_acepta():
    assert _errores([_t("A", ["x/y.py#A"])], {"x/y.py": "# === A ===\n# === fin A ===\n"}) == []


def test_1c_ancestro_que_siembra_acepta():
    u = _t("U", ["x/y.py"], siembra=["x/y.py#A"])
    a = _t("A", ["x/y.py#A"], depende=["U"])
    assert _errores([u, a], {"x/y.py": "codigo\n"}) == []


def test_1d_siembra_de_ficha_sin_relacion_rechaza():
    u = _t("U", ["x/y.py"], siembra=["x/y.py#A"])
    a = _t("A", ["x/y.py#A"])
    errores = _errores([u, a], {"x/y.py": "codigo\n"})
    assert any(e.startswith("A:") and "marca" in e for e in errores)
    assert any(e.startswith("U:") and "no depende" in e for e in errores)


# 2 · sección en un archivo que no existe --------------------------------------------------------

def test_2a_sin_creadora_rechaza():
    errores = _errores([_t("A", ["nuevo/z.py#A"])], {"otro.py": ""})
    assert errores and "no existe" in errores[0] and "HEAD abc1234" in errores[0]


def test_2b_ancestro_que_crea_y_siembra_acepta():
    u = _t("U", ["nuevo/z.py"], crea=["nuevo/z.py"], siembra=["nuevo/z.py#A"])
    a = _t("A", ["nuevo/z.py#A"], depende=["U"])
    assert _errores([u, a], {"otro.py": ""}) == []


def test_2c_creadora_sin_relacion_rechaza():  # M2
    u = _t("U", ["nuevo/z.py"], crea=["nuevo/z.py"], siembra=["nuevo/z.py#A"])
    a = _t("A", ["nuevo/z.py#A"])
    errores = _errores([u, a], {"otro.py": ""})
    assert any(e.startswith("A:") and "no existe" in e for e in errores)


# 3 · ruta equivocada con sugerencia -------------------------------------------------------------

def test_3_ruta_equivocada_sugiere_la_real():
    errores = _errores([_t("A", ["a/pantallas/i.tsx"])], {"a/layout/pantallas/i.tsx": ""})
    assert len(errores) == 1 and "¿quiso decir «a/layout/pantallas/i.tsx»?" in errores[0]


def test_m1_ruta_equivocada_con_seccion_sugiere_la_real():
    real = "frontend/src/components/layout/pantallas/index.tsx"
    archivos = {real: "// === MUT-01 ===\n// === fin MUT-01 ===\n"}
    errores = _errores([_t("MUT-01", ["frontend/src/components/pantallas/index.tsx#MUT-01"])], archivos)
    assert len(errores) == 1 and f"¿quiso decir «{real}»?" in errores[0]


def test_creacion_implicita_solo_avisa_en_fase_1():
    hallazgos = git.validar_contra_arbol([_t("A", ["sala_nueva/x.py", "sala_nueva/**"])], {"otro.py"},
                                         lambda r: "")
    assert hallazgos and all(h.nivel == "aviso" for h in hallazgos)


# 4 · coherencia de «crea» ----------------------------------------------------------------------

def test_4a_crea_de_ruta_existente_rechaza():
    errores = _errores([_t("A", ["x.py"], crea=["x.py"])], {"x.py": ""})
    assert any("ya existe" in e for e in errores)


def test_4b_dos_creadoras_rechaza():
    errores = _errores([_t("A", ["n.py"], crea=["n.py"]), _t("B", ["n.py"], crea=["n.py"], depende=["A"])],
                       {"otro.py": ""})
    assert any("varias creadoras" in e for e in errores)


# 5 · la lista de exenciones solo decrece --------------------------------------------------------

def test_5a_exencion_nueva_rechaza():
    previas = [("A", "x/y.py#A", "sin marca")]
    despues = previas + [("B", "z.py#B", "sin marca")]
    assert git.exenciones_nuevas(previas, despues) and not git.exenciones_nuevas(despues, previas)


def test_5b_exencion_resuelta_rechaza():
    archivos = {"x/y.py": "codigo\n"}
    hallazgos = git.validar_contra_arbol([_t("A", ["x/y.py#A"])], set(archivos), archivos.get)
    assert git.aplicar_exenciones(hallazgos, [("A", "x/y.py#A", "sin marca")]) == []
    resuelto = {"x/y.py": "# === A ===\n"}
    hallazgos = git.validar_contra_arbol([_t("A", ["x/y.py#A"])], set(resuelto), resuelto.get)
    errores = git.aplicar_exenciones(hallazgos, [("A", "x/y.py#A", "sin marca")])
    assert len(errores) == 1 and "retírela" in errores[0]


def test_5c_formato_de_la_lista():
    assert git.leer_exenciones("# comentario\n\nA|x.py#A|motivo con | barra\n") == [
        ("A", "x.py#A", "motivo con | barra")]


# 6 · cero fichas -------------------------------------------------------------------------------

def test_6_cero_fichas_falla_e_informa_la_base():
    errores = git.validar([], arbol={"x.py"}, leer=lambda r: "", base="HEAD abc1234")
    assert len(errores) == 1 and "Base: HEAD abc1234" in errores[0]
    hechas = git.validar([_t("A", ["x.py"], estado="hecha")], arbol={"x.py"}, leer=lambda r: "", base="HEAD abc1234")
    assert any("0 fichas no hechas" in e for e in hechas)


def test_validar_sin_arbol_no_cambia():
    assert git.validar([_t("A", ["no/existe.py#A"])]) == []
