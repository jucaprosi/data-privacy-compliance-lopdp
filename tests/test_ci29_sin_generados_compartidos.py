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


def _bloque_sintetico(tid, tanda):
    return (f"### {tid} · n  (tanda {tanda})\n\n**Objetivo** (en este orden):\n\n1. `{tid}` — x\n\n"
            f"**Escribe** (lista):\n\n  - `{tid}.py`\n\n**No hagas:**\n\n")


def _ida_y_vuelta(portada: str, bloques: dict[str, str]) -> None:
    nueva_portada, separados = rep.repartir(rep.combinar(portada, bloques))
    assert nueva_portada == portada and separados == bloques


def test_reparto_sin_perdidas():
    # muestra sintética fija: siempre se prueba, esté o no la carpeta real
    bloques = {"A-1": _bloque_sintetico("A-1", 1), "B-1": _bloque_sintetico("B-1", 2)}
    portada, bloques = rep.repartir(rep.combinar("# Portada\n\n## Briefs\n\n## Fin\n", bloques))
    _ida_y_vuelta(portada, bloques)
    # con la carpeta real, si tiene briefs (vacía o ausente, no exige nada)
    archivos = {p.stem: p.read_bytes().decode("utf-8")
                for p in sorted((RAIZ / rep.DIR_BRIEFS).glob("*.md"))}
    if archivos:
        _ida_y_vuelta((RAIZ / rep.PORTADA).read_bytes().decode("utf-8"), archivos)
    # mutación: perder una letra en un bloque cambia la unión
    nombre = next(iter(bloques))
    # `combinar` repone el salto de línea final si falta: la letra perdida es la primera, nunca la última
    roto = dict(bloques, **{nombre: bloques[nombre][1:]})
    assert rep.combinar(portada, roto) != rep.combinar(portada, bloques)


def test_alcance_un_brief_por_ficha():
    pr = ["governance/apoyo/briefs/X-1.md", "governance/apoyo/briefs/Y-1.md",
          "governance/artefactos/TASKS.md", "governance/apoyo/BRIEFS_POR_BLOQUE.md"]
    fuera = vap.fuera_de_alcance(pr, "X-1", (), _Indice)
    assert fuera == pr[1:]
    # mutación: admitir el brief ajeno sacaría Y-1 de la lista
    assert "governance/apoyo/briefs/Y-1.md" in fuera


PORTADA = "governance/apoyo/BRIEFS_POR_BLOQUE.md"
TASKS = "governance/artefactos/TASKS.md"


def _duenas(tareas, ruta):
    return [t.id for t in tareas if t.estado != "hecha" and any(p.partition("#")[0] == ruta for p in t.propiedad)]


def _ortogonal(tareas):
    return len(_duenas(tareas, PORTADA)) <= 1 and not _duenas(tareas, TASKS)


def test_ortogonalidad_gobernanza():
    tareas, _ = git.cargar_tareas()
    assert _ortogonal(tareas), (_duenas(tareas, PORTADA), _duenas(tareas, TASKS))
    # mutación: dos fichas pendientes dueñas de la portada rompen el invariante
    from types import SimpleNamespace as F
    dos = [F(id="A-1", estado="pendiente", propiedad=[PORTADA]), F(id="B-1", estado="pendiente", propiedad=[PORTADA])]
    assert not _ortogonal(dos)
    assert not _ortogonal([F(id="A-1", estado="pendiente", propiedad=[TASKS])])


def test_verificar_reparto_carpeta():
    res = subprocess.run([sys.executable, str(RAIZ / "scripts" / "verificar_reparto.py")],
                         cwd=RAIZ, capture_output=True, text=True)
    assert res.returncode == 0, res.stdout[-800:]
    assert "REPARTO OK" in res.stdout
