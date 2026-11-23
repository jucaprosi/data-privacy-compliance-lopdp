# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"""CI-29 · Sin archivos generados compartidos en los PR de fichas (especificaciones/CI-29.md)."""
import importlib.util
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _cargar(nombre: str):
    spec = importlib.util.spec_from_file_location(nombre, RAIZ / "scripts" / f"{nombre}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod
    spec.loader.exec_module(mod)
    return mod


git = _cargar("generar_indice_tareas")


def _t(tid, depende=(), propiedad=("x.py",)):
    return git.Tarea(id=tid, titulo=f"Tarea {tid}", ola="A", estado="pendiente", sala="sala",
                     depende_de=tuple(depende), propiedad=tuple(propiedad), arbitro="pytest")


def test_indice_valida_sin_committear():
    assert git.INICIO not in (RAIZ / "governance/artefactos/TASKS.md").read_text(encoding="utf-8")
    ignorados = (RAIZ / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "governance/artefactos/_generado/" in ignorados
    # CI-35 R3: muestra sintética fija con 0 fichas no hechas, contra un árbol sintético
    hechas = [git.Tarea(**{**_t("A-1").__dict__, "estado": "hecha"})]
    assert git.validar(hechas, {"sala"}, arbol={"x.py"}, leer=lambda r: "", base="HEAD abc1234") == []
    # y el generador real sale con 0, tenga main 0 o más fichas pendientes
    ok = subprocess.run([sys.executable, str(RAIZ / "scripts" / "generar_indice_tareas.py")],
                        cwd=RAIZ, capture_output=True, text=True)
    assert ok.returncode == 0, ok.stdout
    # m4: una dependencia inexistente lo hace fallar
    assert any("NOEXISTE" in e for e in git.validar([_t("A-1", depende=("NOEXISTE",))], {"sala"}))


def test_orden_por_archivo_compartido():
    sin_orden = git.validar([_t("A-1", propiedad=("c.py",)), _t("A-2", propiedad=("c.py",))], {"sala"})
    assert sin_orden, "dos fichas con un archivo común sin orden deben fallar"
    con_orden = git.validar([_t("A-1", propiedad=("c.py",)), _t("A-2", depende=("A-1",), propiedad=("c.py",))],
                            {"sala"})
    assert con_orden == []


TASKS = "governance/artefactos/TASKS.md"


def _duenas(tareas, ruta):
    return [t.id for t in tareas if t.estado != "hecha" and any(p.partition("#")[0] == ruta for p in t.propiedad)]


def test_ortogonalidad_gobernanza():
    tareas, _ = git.cargar_tareas()
    assert not _duenas(tareas, TASKS)
    # mutación: una ficha pendiente dueña de TASKS.md rompe el invariante
    from types import SimpleNamespace as F
    assert _duenas([F(id="A-1", estado="pendiente", propiedad=[TASKS])], TASKS) == ["A-1"]


def test_verificar_reparto_carpeta():
    res = subprocess.run([sys.executable, str(RAIZ / "scripts" / "verificar_reparto.py")],
                         cwd=RAIZ, capture_output=True, text=True)
    assert res.returncode == 0, res.stdout[-800:]
    assert "REPARTO OK" in res.stdout
