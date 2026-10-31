# ¤¤qa-engineer
"""Grafo de dependencias entre salas ADPA (análisis AST, sin BD).

Invariante (ADPA §3): una sala solo depende del pasillo central. Si la sala A necesita una
capacidad de la sala B, app_core invoca ambas compuertas; ninguna sala importa a otra.

DEUDA_LATERAL no es una lista de permisos: registra las dependencias que incumplen esa regla y
solo puede encoger. Una excepción nueva exige un ADR (ADPA §7), no una línea aquí.
"""
import ast
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FEATURES = RAIZ / "features"

DEUDA_LATERAL = frozenset({
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
TOPE_DEUDA_LATERAL = 11


def modulos_de_salas(fuente: str) -> set[str]:
    """Módulos de features/ que nombra un archivo, también en imports dentro de funciones."""
    modulos = set()
    for nodo in ast.walk(ast.parse(fuente)):
        if isinstance(nodo, ast.Import):
            modulos.update(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.level == 0:
            if nodo.module == "features" or (nodo.module.startswith("features.") and nodo.module.count(".") == 1):
                modulos.update(f"{nodo.module}.{alias.name}" for alias in nodo.names)
            else:
                modulos.add(nodo.module)
    return {m for m in modulos if m.startswith("features.")}


def sala_de(modulo: str) -> str:
    return modulo.split(".")[1]


def es_compuerta(modulo: str) -> bool:
    sala = sala_de(modulo)
    return modulo == f"features.{sala}.{sala}_service"


def grafo_real() -> set[tuple[str, str]]:
    aristas = set()
    for ruta in FEATURES.rglob("*.py"):
        partes = ruta.relative_to(FEATURES).parts
        if len(partes) < 2:
            continue
        sala = partes[0]
        for modulo in modulos_de_salas(ruta.read_text(encoding="utf-8")):
            if sala_de(modulo) != sala:
                aristas.add((sala, sala_de(modulo)))
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


def test_ninguna_sala_importa_a_otra_fuera_de_la_deuda():
    nuevas = grafo_real() - DEUDA_LATERAL
    assert not nuevas, f"Dependencias laterales prohibidas por ADPA §3, usen app_core: {sorted(nuevas)}"


def test_la_deuda_lateral_solo_encoge():
    saldadas = DEUDA_LATERAL - grafo_real()
    assert not saldadas, f"Ya saldadas, retírelas de DEUDA_LATERAL y baje el tope: {sorted(saldadas)}"
    assert len(DEUDA_LATERAL) <= TOPE_DEUDA_LATERAL


def test_las_salas_no_forman_ciclos():
    assert sala_en_ciclo(grafo_real()) is None


def test_app_core_solo_importa_compuertas():
    """ADPA §3: el pasillo central invoca compuertas; nunca modelos ni archivos privados."""
    violaciones = [
        f"{ruta.relative_to(RAIZ).as_posix()} importa '{modulo}'"
        for ruta in (RAIZ / "app_core").rglob("*.py")
        for modulo in modulos_de_salas(ruta.read_text(encoding="utf-8"))
        if not es_compuerta(modulo)
    ]
    assert not violaciones, "\n".join(violaciones)


def test_el_detector_ve_todas_las_formas_de_importar():
    fuente = (
        "import features.rat.rat_service\n"
        "from features.roadmap.domain.models import x\n"
        "from features import evidencias\n"
        "def f():\n"
        "    from features.organizacion import organizacion_service\n"
    )
    assert modulos_de_salas(fuente) == {
        "features.rat.rat_service",
        "features.roadmap.domain.models",
        "features.evidencias",
        "features.organizacion.organizacion_service",
    }


def test_solo_la_compuerta_de_la_sala_cuenta_como_compuerta():
    assert es_compuerta("features.rat.rat_service")
    assert not es_compuerta("features.rat.domain.models")
    assert not es_compuerta("features.niif18.doctrine.doctrine_service")


def test_el_detector_de_ciclos_distingue_cadena_de_ciclo():
    assert sala_en_ciclo({("a", "b"), ("b", "c")}) is None
    assert sala_en_ciclo({("a", "b"), ("b", "a"), ("c", "a")}) == "a"
