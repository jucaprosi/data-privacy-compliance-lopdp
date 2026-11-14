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
rep = _cargar("verificar_reparto")
vap = _cargar("verificar_alcance_pr")


class _Indice:
    @staticmethod
    def rutas_se_solapan(a, b):
        return a == b


def _t(tid, depende=(), propiedad=("x.py",)):
    return git.Tarea(id=tid, titulo=f"Tarea {tid}", ola="A", estado="pendiente", sala="sala",
                     depende_de=tuple(depende), propiedad=tuple(propiedad), arbitro="pytest")


def test_indice_valida_sin_committear():
    assert git.INICIO not in (RAIZ / "governance/artefactos/TASKS.md").read_text(encoding="utf-8")
    ignorados = (RAIZ / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "governance/artefactos/_generado/" in ignorados
    ok = subprocess.run([sys.executable, str(RAIZ / "scripts" / "generar_indice_tareas.py")],
                        cwd=RAIZ, capture_output=True, text=True)
    assert ok.returncode == 0, ok.stdout
    # mutación: una dependencia inexistente lo hace fallar
    assert any("NOEXISTE" in e for e in git.validar([_t("A-1", depende=("NOEXISTE",))], {"sala"}))


def test_orden_por_archivo_compartido():
    sin_orden = git.validar([_t("A-1", propiedad=("c.py",)), _t("A-2", propiedad=("c.py",))], {"sala"})
    assert sin_orden, "dos fichas con un archivo común sin orden deben fallar"
    con_orden = git.validar([_t("A-1", propiedad=("c.py",)), _t("A-2", depende=("A-1",), propiedad=("c.py",))],
                            {"sala"})
    assert con_orden == []


def test_reparto_sin_perdidas():
    portada = (RAIZ / rep.PORTADA).read_bytes().decode("utf-8")
    archivos = {p.stem: p.read_bytes().decode("utf-8")
                for p in (RAIZ / rep.DIR_BRIEFS).glob("*.md")}
    assert archivos, "la carpeta de briefs no puede estar vacía"
    unido = rep.combinar(portada, archivos)
    nueva_portada, bloques = rep.repartir(unido)
    assert nueva_portada == portada and bloques == archivos
    # mutación: perder una letra en un bloque cambia la unión
    nombre = next(iter(archivos))
    roto = dict(archivos, **{nombre: archivos[nombre][:-1]})
    assert rep.combinar(portada, roto) != unido


def test_alcance_un_brief_por_ficha():
    pr = ["governance/apoyo/briefs/X-1.md", "governance/apoyo/briefs/Y-1.md",
          "governance/artefactos/TASKS.md", "governance/apoyo/BRIEFS_POR_BLOQUE.md"]
    fuera = vap.fuera_de_alcance(pr, "X-1", (), _Indice)
    assert fuera == pr[1:]
    # mutación: admitir el brief ajeno sacaría Y-1 de la lista
    assert "governance/apoyo/briefs/Y-1.md" in fuera


def test_ortogonalidad_gobernanza():
    tareas, _ = git.cargar_tareas()
    for t in tareas:
        if t.estado == "hecha" or t.id == "CI-29":
            continue
        for p in t.propiedad:
            ruta = p.partition("#")[0]
            assert ruta not in {"governance/artefactos/TASKS.md", "governance/apoyo/BRIEFS_POR_BLOQUE.md"}, (
                f"{t.id} posee un archivo común de gobernanza: {ruta}")


def test_verificar_reparto_carpeta():
    res = subprocess.run([sys.executable, str(RAIZ / "scripts" / "verificar_reparto.py")],
                         cwd=RAIZ, capture_output=True, text=True)
    assert res.returncode == 0, res.stdout[-800:]
    assert "REPARTO OK" in res.stdout
