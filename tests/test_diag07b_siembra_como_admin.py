# ¤diagnostico ¤dpo-independencia ¤arbitro
"""DIAG-07b: las pruebas siembran las respuestas del diagnóstico como administrador.

Guardia estática (sin base de datos): recorre los archivos del bloque y falla si un `PUT` a la ruta de
respuestas usa el rol dpo (literal `"dpo"` en `_como`/`_h` o PUT sin cabeceras, que toma la identidad por
defecto, el DPO). El gate transitorio de DIAG-07a todavía deja pasar al DPO: sin esta guardia el cambio de
rol de siembra no fallaría nunca. Los tests cuyo asunto es quién puede responder usan el rol como
parámetro, no como literal, y los reescribe DIAG-07.

Mutación documentada: volver a poner "dpo" en un PUT de siembra de cualquiera de estos archivos hace fallar
`test_ningun_put_de_siembra_usa_el_dpo`.
"""
import ast
from pathlib import Path

import pytest

ARCHIVOS = (
    "tests/test_diag11_prueba_y_real.py",
    "tests/test_diag13_evidencia_declarada.py",
    "tests/test_diagnostico_comparativo.py",
    "tests/test_diagnostico_escala_smartcidi.py",
    "tests/test_diagnostico_no_aplica.py",
    "tests/test_diagnostico_respuestas.py",
    "tests/test_diagnostico_resultados.py",
    "tests/test_evidencias_persistencia.py",
    "tests/test_roadmap_hallazgos.py",
)
# Excepción cerrada: (archivo, función) cuyo PUT como DPO es el asunto de la prueba. Solo puede decrecer.
EXCEPCIONES: frozenset[tuple[str, str]] = frozenset()

_RAIZ = Path(__file__).resolve().parent.parent
_RUTAS = {"RESPUESTAS", "RUTA"}


def _es_ruta_de_respuestas(nodo: ast.expr) -> bool:
    return (isinstance(nodo, ast.Name) and nodo.id in _RUTAS) or (
        isinstance(nodo, ast.Constant) and nodo.value == "/api/v1/diagnostico/respuestas"
    )


def _usa_dpo(cabeceras: ast.expr) -> bool:
    return any(isinstance(n, ast.Constant) and n.value == "dpo" for n in ast.walk(cabeceras))


def puts_como_dpo(fuente: str) -> list[tuple[str, int]]:
    """(función, línea) de cada PUT a la ruta de respuestas hecho como DPO o con la identidad por defecto."""
    arbol = ast.parse(fuente)
    hallazgos: list[tuple[str, int]] = []

    def visitar(nodo: ast.AST, funcion: str) -> None:
        for hijo in ast.iter_child_nodes(nodo):
            nombre = hijo.name if isinstance(hijo, (ast.FunctionDef, ast.AsyncFunctionDef)) else funcion
            if (
                isinstance(hijo, ast.Call) and isinstance(hijo.func, ast.Attribute) and hijo.func.attr == "put"
                and hijo.args and _es_ruta_de_respuestas(hijo.args[0])
            ):
                cabeceras = [k.value for k in hijo.keywords if k.arg == "headers"]
                if not cabeceras or _usa_dpo(cabeceras[0]):
                    hallazgos.append((funcion, hijo.lineno))
            visitar(hijo, nombre)

    visitar(arbol, "<módulo>")
    return hallazgos


def test_ningun_put_de_siembra_usa_el_dpo():
    violaciones = []
    for archivo in ARCHIVOS:
        for funcion, linea in puts_como_dpo((_RAIZ / archivo).read_text(encoding="utf-8")):
            if (archivo, funcion) not in EXCEPCIONES:
                violaciones.append(f"{archivo}:{linea} ({funcion})")
    assert not violaciones, "PUT de respuestas como dpo; siembra como administrador: " + ", ".join(violaciones)


def test_las_excepciones_solo_decrecen():
    """Una excepción que ya no hace falta se retira: la lista cerrada no puede quedar con entradas muertas."""
    reales = {
        (archivo, funcion)
        for archivo in ARCHIVOS
        for funcion, _ in puts_como_dpo((_RAIZ / archivo).read_text(encoding="utf-8"))
    }
    assert EXCEPCIONES <= reales


@pytest.mark.parametrize("fuente", [
    'async def test_x(ctx):\n    await c.put(RESPUESTAS, headers=_como(ctx, "dpo"), json={})\n',
    'async def test_x(ctx):\n    await c.put(RUTA, json={})\n',
    'async def test_x(ctx):\n    await c.put("/api/v1/diagnostico/respuestas", headers=_h(u, t, "dpo"), json={})\n',
])
def test_la_guardia_detecta_el_put_como_dpo(fuente):
    assert [f for f, _ in puts_como_dpo(fuente)] == ["test_x"]


@pytest.mark.parametrize("fuente", [
    'async def test_x(ctx):\n    await c.put(RESPUESTAS, headers=_como(ctx, "admin"), json={})\n',
    'async def test_x(ctx, clave):\n    await c.put(RESPUESTAS, headers=_como(ctx, clave), json={})\n',
    'async def test_x(ctx):\n    await c.put("/otra/ruta", json={})\n',
])
def test_la_guardia_no_marca_lo_que_no_es_siembra_como_dpo(fuente):
    assert puts_como_dpo(fuente) == []
