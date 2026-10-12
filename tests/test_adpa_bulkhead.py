"""Mamparos ADPA de las salas Organización y Hoja de Ruta (análisis AST, sin BD).

Invariante: fuera de una sala, lo único que se importa de ella es su compuerta
``features.<sala>.<sala>_service``. Esto cubre routers, ``api/``, ``app_core/``,
otras salas y las pruebas.
"""
import ast
import os
import re

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALAS = ("organizacion", "roadmap")
MARCADORES_RESERVADOS = {
    "roadmap": ("RM-07", "RM-08", "RM-09", "RM-12", "RM-13"),
    "organizacion": ("RM-10", "RM-15", "RM-16"),
}
CARPETAS_EXCLUIDAS = {".venv", "venv", "node_modules", ".git", "__pycache__", "frontend", ".next"}


def _archivos_py():
    for base, dirs, files in os.walk(RAIZ):
        dirs[:] = [d for d in dirs if d not in CARPETAS_EXCLUIDAS]
        for nombre in files:
            if nombre.endswith(".py"):
                yield os.path.join(base, nombre)


def _modulos_importados(ruta: str):
    with open(ruta, "r", encoding="utf-8") as f:
        arbol = ast.parse(f.read(), filename=ruta)
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.level == 0:
            yield nodo.module
            # `from features.roadmap import services` importa un submódulo, no la compuerta.
            if nodo.module == "features":
                for alias in nodo.names:
                    yield f"features.{alias.name}"
            elif re.fullmatch(r"features\.[a-z_0-9]+", nodo.module):
                for alias in nodo.names:
                    yield f"{nodo.module}.{alias.name}"
        elif isinstance(nodo, ast.Import):
            for alias in nodo.names:
                yield alias.name


def _sala_de(ruta: str):
    rel = os.path.relpath(ruta, RAIZ).split(os.sep)
    if len(rel) >= 3 and rel[0] == "features":
        return rel[1]
    return None


def test_cada_sala_tiene_su_compuerta():
    for sala in SALAS:
        compuerta = os.path.join(RAIZ, "features", sala, f"{sala}_service.py")
        assert os.path.isfile(compuerta), f"La sala {sala} carece de la compuerta {sala}_service.py"


@pytest.mark.parametrize("sala", SALAS)
def test_solo_se_importa_la_compuerta_de_la_sala(sala):
    """Todo import de features.<sala>.* desde fuera de la sala termina en <sala>_service."""
    permitido = f"features.{sala}.{sala}_service"
    violaciones = []
    for ruta in _archivos_py():
        if _sala_de(ruta) == sala:
            continue
        for modulo in _modulos_importados(ruta):
            if modulo == f"features.{sala}" or modulo == permitido:
                continue
            if modulo.startswith(f"features.{sala}."):
                violaciones.append(f"{os.path.relpath(ruta, RAIZ)} importa '{modulo}'")
    assert not violaciones, "Imports que saltan la compuerta:\n" + "\n".join(violaciones)


def test_ninguna_sala_importa_el_codigo_viejo_de_app_core():
    """El código de las salas ya no vive en app_core/{services,schemas,workers}."""
    viejos = ("app_core.services", "app_core.schemas", "app_core.workers", "app_core.ai.roadmap_prompts")
    violaciones = [
        f"{os.path.relpath(r, RAIZ)} importa '{m}'"
        for r in _archivos_py()
        for m in _modulos_importados(r)
        if m.startswith(viejos)
    ]
    assert not violaciones, "\n".join(violaciones)


@pytest.mark.parametrize("sala", SALAS)
def test_compuerta_conserva_secciones_reservadas(sala):
    """Cada tarea futura edita solo su sección; sin marcadores no hay frontera entre tareas."""
    with open(os.path.join(RAIZ, "features", sala, f"{sala}_service.py"), encoding="utf-8") as f:
        texto = f.read()
    for tarea in MARCADORES_RESERVADOS[sala]:
        assert f"# === {tarea} ===" in texto, f"Falta la apertura de la sección {tarea}"
        assert f"# === fin {tarea} ===" in texto, f"Falta el cierre de la sección {tarea}"
        assert texto.index(f"# === {tarea} ===") < texto.index(f"# === fin {tarea} ==="), tarea
