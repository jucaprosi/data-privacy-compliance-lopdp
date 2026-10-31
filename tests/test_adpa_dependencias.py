# ¤¤qa-engineer
"""Grafo de dependencias entre salas ADPA (análisis AST, sin BD).

Invariante: las dependencias reales entre salas son exactamente las declaradas aquí, no forman
ciclos y app_core no depende de ninguna sala. Añadir una dependencia es una decisión de diseño:
se declara en este archivo y queda visible en la revisión del PR.
"""
import ast
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FEATURES = RAIZ / "features"

DEPENDENCIAS_PERMITIDAS = frozenset({
    ("ai_copilot", "niif18"),
    ("auditoria_capa", "evidencias"),
    ("auditoria_capa", "organizacion"),
    ("auditoria_capa", "roadmap"),
    ("plataforma", "organizacion"),
    ("rat", "organizacion"),
    ("riesgos_mtge", "organizacion"),
    ("riesgos_mtge", "rat"),
    ("roadmap", "diagnostico"),
    ("roadmap", "organizacion"),
    ("roadmap", "rat"),
})


def salas_importadas(fuente: str) -> set[str]:
    """Salas que nombra un módulo, también en imports dentro de funciones."""
    salas = set()
    for nodo in ast.walk(ast.parse(fuente)):
        if isinstance(nodo, ast.Import):
            modulos = [alias.name for alias in nodo.names]
        elif isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.level == 0:
            modulos = [nodo.module]
            if nodo.module == "features":
                modulos += [f"features.{alias.name}" for alias in nodo.names]
        else:
            continue
        salas.update(m.split(".")[1] for m in modulos if m.startswith("features."))
    return salas


def grafo_real() -> set[tuple[str, str]]:
    aristas = set()
    for ruta in FEATURES.rglob("*.py"):
        partes = ruta.relative_to(FEATURES).parts
        if len(partes) < 2:
            continue
        sala = partes[0]
        for destino in salas_importadas(ruta.read_text(encoding="utf-8")):
            if destino != sala:
                aristas.add((sala, destino))
    return aristas


def sala_en_ciclo(aristas: set[tuple[str, str]]) -> str | None:
    """Quita salas sin dependencias salientes; lo que no se puede quitar está en un ciclo."""
    pendientes = set(aristas)
    while True:
        con_salida = {a for a, _ in pendientes}
        sueltas = {(a, b) for a, b in pendientes if b not in con_salida}
        if not sueltas:
            return min(con_salida) if con_salida else None
        pendientes -= sueltas


def test_las_dependencias_reales_son_las_declaradas():
    real = grafo_real()
    assert not real - DEPENDENCIAS_PERMITIDAS, f"Dependencias sin declarar: {sorted(real - DEPENDENCIAS_PERMITIDAS)}"
    assert not DEPENDENCIAS_PERMITIDAS - real, f"Declaradas que ya no existen: {sorted(DEPENDENCIAS_PERMITIDAS - real)}"


def test_las_salas_no_forman_ciclos():
    assert sala_en_ciclo(grafo_real()) is None


def test_app_core_no_depende_de_ninguna_sala():
    violaciones = {
        os.fspath(ruta.relative_to(RAIZ)): sorted(salas)
        for ruta in (RAIZ / "app_core").rglob("*.py")
        if (salas := salas_importadas(ruta.read_text(encoding="utf-8")))
    }
    assert not violaciones, violaciones


def test_el_detector_ve_todas_las_formas_de_importar():
    fuente = (
        "import features.rat.rat_service\n"
        "from features.roadmap.roadmap_service import x\n"
        "from features import evidencias\n"
        "def f():\n"
        "    from features.organizacion import organizacion_service\n"
    )
    assert salas_importadas(fuente) == {"rat", "roadmap", "evidencias", "organizacion"}


def test_el_detector_de_ciclos_distingue_cadena_de_ciclo():
    assert sala_en_ciclo({("a", "b"), ("b", "c")}) is None
    assert sala_en_ciclo({("a", "b"), ("b", "a"), ("c", "a")}) == "a"
