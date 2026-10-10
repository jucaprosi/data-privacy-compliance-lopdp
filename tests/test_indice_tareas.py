"""Las especificaciones de tareas son válidas, independientes y su índice está al día."""
import importlib.util
import sys
from pathlib import Path

import pytest

_RUTA = Path(__file__).resolve().parent.parent / "scripts" / "generar_indice_tareas.py"
_spec = importlib.util.spec_from_file_location("generar_indice_tareas", _RUTA)
git = importlib.util.module_from_spec(_spec)
sys.modules["generar_indice_tareas"] = git  # las clases de datos lo exigen antes de ejecutar el módulo
_spec.loader.exec_module(git)


def _t(tid, depende=(), propiedad=("x.py",), estado="pendiente", ola="A"):
    return git.Tarea(id=tid, titulo=f"Tarea {tid}", ola=ola, estado=estado, sala="sala",
                     depende_de=tuple(depende), propiedad=tuple(propiedad), arbitro="pytest")


# ----------------------------------------------------------------- las tareas reales

def test_las_especificaciones_reales_son_validas_e_independientes():
    tareas, errores = git.cargar_tareas()
    errores += git.validar(tareas)
    assert errores == []
    assert len(tareas) >= 1


def test_el_indice_de_tasks_md_esta_al_dia():
    tareas, _ = git.cargar_tareas()
    texto = git.TASKS_MD.read_text(encoding="utf-8")
    assert git.extraer_indice(texto) == git.generar_indice(tareas), (
        "Ejecute: python scripts/generar_indice_tareas.py --escribir"
    )


# ----------------------------------------------------------------- solapamiento de rutas

@pytest.mark.parametrize("a,b,esperado", [
    ("a/b.py", "a/b.py", True),
    ("a/b.py", "a/c.py", False),
    ("a/b.py", "a/**", True),
    ("a/b.py", "x/**", False),
    ("a/*.py", "a/b.py", True),
    ("a/*.py", "a/b/c.py", False),
    ("alembic/versions/*_audit_events.py", "alembic/versions/*_tamano_check.py", False),
    ("alembic/versions/*_audit_events.py", "alembic/versions/*.py", True),
    ("features/roadmap/**", "features/roadmap/services/x.py", True),
    ("features/roadmap/**", "features/organizacion/**", False),
])
def test_solapamiento_de_rutas(a, b, esperado):
    assert git.rutas_se_solapan(a, b) is esperado
    assert git.rutas_se_solapan(b, a) is esperado


def test_secciones_distintas_de_un_mismo_archivo_no_chocan():
    assert not git.propiedades_se_solapan("g.py#RM-07", "g.py#RM-08")
    assert git.propiedades_se_solapan("g.py#RM-07", "g.py#RM-07")
    assert git.propiedades_se_solapan("g.py#RM-07", "g.py")  # el archivo entero abarca la sección


# ----------------------------------------------------------------- validación

def test_dos_tareas_paralelas_con_el_mismo_archivo_se_detectan():
    errores = git.validar([_t("A-1"), _t("A-2")])
    assert any("A-1 y A-2" in e for e in errores)


def test_tareas_con_archivos_distintos_son_independientes():
    assert git.validar([_t("A-1", propiedad=("a.py",)), _t("A-2", propiedad=("b.py",))]) == []


def test_una_tarea_que_espera_a_otra_puede_compartir_archivos():
    assert git.validar([_t("A-1"), _t("A-2", depende=("A-1",))]) == []


def test_la_dependencia_indirecta_tambien_cuenta():
    tareas = [_t("A-1"), _t("A-2", depende=("A-1",), propiedad=("y.py",)), _t("A-3", depende=("A-2",))]
    assert git.validar(tareas) == []


def test_ciclo_detectado():
    errores = git.validar([_t("A-1", depende=("A-2",), propiedad=("a",)), _t("A-2", depende=("A-1",), propiedad=("b",))])
    assert any("ciclo" in e for e in errores)


def test_dependencia_inexistente_detectada():
    assert any("no existe" in e for e in git.validar([_t("A-1", depende=("Z-9",))]))


def test_estado_y_ola_invalidos_detectados():
    errores = git.validar([_t("A-1", estado="medio", ola="Z")])
    assert any("estado inválido" in e for e in errores) and any("ola inválida" in e for e in errores)


def test_id_duplicado_detectado():
    assert any("duplicado" in e for e in git.validar([_t("A-1", propiedad=("a",)), _t("A-1", propiedad=("b",))]))


# ----------------------------------------------------------------- índice

def test_el_indice_se_aplica_entre_las_marcas_sin_tocar_el_resto():
    tareas = [_t("A-1", propiedad=("a",)), _t("A-2", propiedad=("b",), estado="hecha")]
    texto = f"antes\n{git.INICIO}\nviejo\n{git.FIN}\ndespués\n"
    nuevo = git.aplicar_indice(texto, git.generar_indice(tareas))
    assert nuevo.startswith("antes\n") and nuevo.endswith("\ndespués\n")
    assert "viejo" not in nuevo and "A-2" in nuevo


def test_el_indice_no_incluye_el_estado_para_no_forzar_ediciones_comunes():
    pendiente = git.generar_indice([_t("A-1", estado="pendiente")])
    hecha = git.generar_indice([_t("A-1", estado="hecha")])
    assert pendiente == hecha


def test_el_resumen_de_estado_cuenta_por_estado():
    resumen = git.resumen_estado([_t("A-1", propiedad=("a",)), _t("A-2", propiedad=("b",), estado="hecha")])
    assert "1 pendiente" in resumen and "1 hecha" in resumen
