# ¤rbac-tenant ¤arbitro ¤adpa
"""BOV-02b: la compuerta de Bóveda Cloud reúne sus tres routers y main.py la monta una sola vez (R1).

Contrato: governance/especificaciones/BOV-02b.md §5. Sin base de datos ni `import yaml`.
"""
from __future__ import annotations

import ast
import os
from pathlib import Path

os.environ.setdefault("APP_ENV", "test")
if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL") or "postgresql+psycopg://u:c@localhost/pruebas"

RAIZ = Path(__file__).resolve().parent.parent
SALA = RAIZ / "features" / "boveda_cloud"
PROHIBIDO = "features.boveda_cloud.routes"

RUTAS_SALA = {
    ("GET", "/api/v1/boveda-cloud/suscripcion"),
    ("POST", "/api/v1/boveda-cloud/objetos/url-subida-firmada"),
    ("POST", "/api/v1/boveda-cloud/objetos/{objeto_id}/url-descarga-firmada"),
    ("GET", "/api/v1/boveda-cloud/orquestador-10d"),
}


def _rutas_openapi() -> set[tuple[str, str]]:
    from main import app

    esquema = app.openapi()
    return {(metodo.upper(), ruta) for ruta, ops in esquema["paths"].items() for metodo in ops}


def test_rutas_de_la_sala_montadas():
    """R1 y m1: el OpenAPI de main.app trae suscripción, los dos POST de objetos y el orquestador."""
    faltan = RUTAS_SALA - _rutas_openapi()
    assert not faltan, f"rutas de la bóveda sin montar: {sorted(faltan)}"


def test_la_compuerta_reune_los_tres_routers():
    """El router de la compuerta, montado solo en una app vacía, trae las cuatro rutas de la sala."""
    from fastapi import FastAPI

    from features.boveda_cloud import boveda_cloud_service as svc

    app = FastAPI()
    app.include_router(svc.router, prefix="/api/v1")
    rutas = {(m.upper(), ruta) for ruta, ops in app.openapi()["paths"].items() for m in ops}
    faltan = RUTAS_SALA - rutas
    assert not faltan, f"rutas fuera de la compuerta: {sorted(faltan)}"


def test_main_registra_la_sala_una_sola_vez():
    """R1: una puerta por sala; main.py solo nombra la compuerta, nunca el paquete de rutas."""
    texto = (RAIZ / "main.py").read_text(encoding="utf-8")
    assert texto.count('"features.boveda_cloud.boveda_cloud_service"') == 1
    assert PROHIBIDO not in texto


def _importa_rutas(arbol: ast.AST) -> bool:
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            if any(a.name == PROHIBIDO or a.name.startswith(PROHIBIDO + ".") for a in nodo.names):
                return True
        elif isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.level == 0:
            if nodo.module == PROHIBIDO or nodo.module.startswith(PROHIBIDO + "."):
                return True
            if nodo.module == "features.boveda_cloud" and any(a.name == "routes" for a in nodo.names):
                return True
    return False


def test_rutas_solo_por_la_compuerta():
    """R1: ningún módulo de la aplicación fuera de features/boveda_cloud/ importa sus rutas.

    Las pruebas (tests/) quedan fuera: verifican la sala por dentro y no forman parte de la aplicación.
    """
    excluidas = {".git", ".venv", "venv", "node_modules", "tests", "__pycache__"}
    infractores = []
    for archivo in RAIZ.rglob("*.py"):
        relativo = archivo.relative_to(RAIZ)
        if excluidas & set(relativo.parts) or archivo.is_relative_to(SALA):
            continue
        try:
            arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        if _importa_rutas(arbol):
            infractores.append(relativo.as_posix())
    assert not infractores, f"importan {PROHIBIDO} fuera de la sala: {infractores}"


def test_el_detector_ve_una_importacion_directa():
    """El detector de R1 no es vacuo: reconoce las dos formas de importar las rutas."""
    assert _importa_rutas(ast.parse("from features.boveda_cloud.routes import orquestador_routes"))
    assert _importa_rutas(ast.parse("from features.boveda_cloud import routes"))
    assert not _importa_rutas(ast.parse("from features.boveda_cloud import boveda_cloud_service"))
