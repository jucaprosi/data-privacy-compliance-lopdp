# ¤arquitectura ¤arbitro
"""RET-05 · Entrada única de la API (`main:app`) y despliegue exclusivo en Google Cloud Run.

Verifica el punto de entrada único (`main:app`), la presencia de los manifiestos de Cloud Run
(`Dockerfile`, `frontend/Dockerfile.cloudrun`, `frontend/next.config.cloudrun.ts`,
`frontend/package-lock.json`), la exposición de `/health` desde `main.app` y los módulos activos.
"""
from __future__ import annotations

import ast
import os
from pathlib import Path

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://sin-base:sin-base@localhost:1/sin-base")

import main  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent


def _fuentes_python() -> list[Path]:
    rutas = [RAIZ / "main.py"]
    for carpeta in ("api", "app_core", "features", "scripts", "tests"):
        base = RAIZ / carpeta
        if not base.exists():
            continue
        rutas.extend(
            p for p in base.rglob("*.py") if "__pycache__" not in p.parts
        )
    return rutas


def test_una_sola_entrada():
    requeridos = [
        RAIZ / "main.py",
        RAIZ / "Dockerfile",
        RAIZ / "frontend" / "Dockerfile.cloudrun",
        RAIZ / "frontend" / "next.config.cloudrun.ts",
        RAIZ / "frontend" / "package-lock.json",
    ]
    for archivo in requeridos:
        assert archivo.is_file(), f"Falta artefacto esperado de Cloud Run: {archivo.relative_to(RAIZ)}"

    assert not (RAIZ / "frontend" / "pnpm-lock.yaml").exists()

    for ruta in _fuentes_python():
        arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                nombres = [alias.name for alias in nodo.names]
            elif isinstance(nodo, ast.ImportFrom):
                nombres = [nodo.module or ""]
            else:
                continue
            assert not any(n == "api.index" or n.startswith("api.index.") for n in nombres), (
                f"Import heredado de api.index en {ruta.relative_to(RAIZ)}"
            )

    modulos_nativos = (
        RAIZ / "pytest.ini",
        RAIZ / "app_core" / "security.py",
        RAIZ / "app_core" / "bucle_eventos.py",
        RAIZ / "api" / "routers" / "firma_anf.py",
        RAIZ / "features" / "roadmap" / "services" / "generacion_en_linea.py",
        RAIZ / "frontend" / "src" / "lib" / "auth" / "modo.ts",
    )
    for archivo in modulos_nativos:
        contenido = archivo.read_text(encoding="utf-8")
        assert contenido.strip(), archivo.relative_to(RAIZ)
        if archivo.suffix == ".py":
            ast.parse(contenido, filename=str(archivo))

    readme_frontend = (RAIZ / "frontend" / "README.md").read_text(encoding="utf-8")
    assert "## Deploy on Cloud Run" in readme_frontend


def test_health_routers():
    cliente = TestClient(main.app)
    for ruta in ("/health", "/api/v1/health"):
        resp = cliente.get(ruta)
        assert resp.status_code in (200, 503)
        datos = resp.json()
        assert datos["status"] in ("OPERATIONAL", "DEGRADED")
        assert "routers" in datos

    for prueba_sec in (
        RAIZ / "tests" / "test_sec16_secretos_obligatorios.py",
        RAIZ / "tests" / "test_sec17_configuracion_nube.py",
    ):
        assert prueba_sec.exists()
        assert "from main import app" in prueba_sec.read_text(encoding="utf-8") or "import main" in prueba_sec.read_text(encoding="utf-8")
