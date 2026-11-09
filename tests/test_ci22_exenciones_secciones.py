# ¤¤qa-engineer
# ¤arbitro
"""CI-22: secciones de governance/tareas/_exenciones_propiedad.txt (governance/tareas/CI-22.md).

Mutaciones de `validar_secciones` (cada una deja en rojo su prueba):
- M1: aceptar una sección sin par              -> test_regla1_*
- M2: aceptar una línea de otro ID dentro       -> test_regla3_*
- M3: no comprobar «hecha y vacía»              -> test_regla5_seccion_vacia_de_ficha_hecha
- M4: aceptar una línea X| fuera de su sección  -> test_regla4_linea_fuera_de_su_seccion
- M5: aceptar un ID inexistente                 -> test_regla2_id_inexistente
"""
import importlib.util
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _cargar(nombre: str):
    spec = importlib.util.spec_from_file_location(nombre, RAIZ / "scripts" / f"{nombre}.py")
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo  # las clases de datos lo exigen antes de ejecutar el módulo
    spec.loader.exec_module(modulo)
    return modulo


git = _cargar("generar_indice_tareas")
alcance = _cargar("verificar_alcance_pr")


def _t(tid, estado="en_curso"):
    return git.Tarea(id=tid, titulo=tid, ola="backlog", estado=estado, sala="s",
                     depende_de=(), propiedad=("x.py",), arbitro="pytest")


TAREAS = [_t("A-1"), _t("B-2"), _t("C-3", estado="hecha")]


def _sec(sid, *lineas):
    return [f"# --- INICIO {sid} ---", *lineas, f"# --- FIN {sid} ---"]


def _validar(tmp_path, *lineas):
    ruta = tmp_path / "_exenciones_propiedad.txt"
    ruta.write_text("\n".join(["# cabecera", *lineas]) + "\n", encoding="utf-8")
    return git.validar_secciones(ruta.read_text(encoding="utf-8"), TAREAS)


def test_un_archivo_valido_pasa(tmp_path):
    assert _validar(tmp_path, *_sec("A-1", "A-1|a.py#A-1|m"), "B-2|b.py#B-2|m") == []


# Regla 1 · M1
def test_regla1_seccion_sin_fin(tmp_path):
    assert any("no tiene FIN" in e for e in _validar(tmp_path, "# --- INICIO A-1 ---", "A-1|a|m"))


def test_regla1_fin_sin_inicio(tmp_path):
    assert any("sin su INICIO" in e for e in _validar(tmp_path, "A-1|a|m", "# --- FIN A-1 ---"))


def test_regla1_pares_cruzados(tmp_path):
    assert _validar(tmp_path, "# --- INICIO A-1 ---", "# --- INICIO B-2 ---",
                    "# --- FIN A-1 ---", "# --- FIN B-2 ---")


# Regla 2 · M5
def test_regla2_id_inexistente(tmp_path):
    assert any("ninguna ficha" in e for e in _validar(tmp_path, *_sec("Z-99", "Z-99|z|m")))


# Regla 3 · M2
def test_regla3_linea_ajena_dentro(tmp_path):
    assert _validar(tmp_path, *_sec("A-1", "A-1|a|m", "B-2|b|m")) == [
        "exenciones l.4: línea de B-2 dentro de la sección A-1"]


# Regla 4 · M4
def test_regla4_linea_fuera_de_su_seccion(tmp_path):
    assert _validar(tmp_path, *_sec("A-1", "A-1|a|m"), "A-1|otra|m") == [
        "exenciones l.5: línea de A-1 fuera de su sección"]


def test_regla4_ficha_sin_seccion_sigue_libre(tmp_path):
    assert _validar(tmp_path, *_sec("A-1", "A-1|a|m"), "B-2|b|m") == []


# Regla 5 · M3
def test_regla5_seccion_vacia_de_ficha_hecha(tmp_path):
    assert any("C-3 está vacía" in e for e in _validar(tmp_path, *_sec("C-3")))


def test_regla5_seccion_vacia_de_ficha_no_hecha_es_valida(tmp_path):
    assert _validar(tmp_path, *_sec("A-1")) == []


def test_validar_aplica_las_secciones():
    assert git.validar(TAREAS, texto_exenciones="# --- INICIO A-1 ---\n")


def test_el_archivo_real_de_main_pasa():
    tareas, errores = git.cargar_tareas()
    assert errores == []
    assert git.validar_secciones(git.EXENCIONES.read_text(encoding="utf-8"), tareas) == []


def test_borrar_el_par_de_marcas_queda_fuera_de_alcance():
    diff = ("--- a/governance/tareas/_exenciones_propiedad.txt\n"
            "+++ b/governance/tareas/_exenciones_propiedad.txt\n"
            "@@ -3,3 +2,0 @@\n-# --- INICIO A-1 ---\n-A-1|a|m\n-# --- FIN A-1 ---\n")
    assert not alcance.retira_solo_exenciones_propias(diff, "A-1")
    assert alcance.retira_solo_exenciones_propias("@@ -4 +3,0 @@\n-A-1|a|m\n", "A-1")
