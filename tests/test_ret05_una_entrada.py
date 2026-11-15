# ¤arquitectura ¤arbitro
"""RET-05 · Entrada única de la API (`main:app`) y despliegue exclusivo en Cloud Run.

Verifica la eliminación de configuraciones heredadas (`vercel.json`, `api/index.py`,
`vercel.svg`, `tests/test_vercel_despliegue.py`), la ausencia de imports de `api.index`,
la exposición de `/health` desde `main.app` y la limpieza de comentarios heredados.
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
    retirados = [
        RAIZ / "vercel.json",
        RAIZ / "frontend" / "vercel.json",
        RAIZ / "api" / "index.py",
        RAIZ / "frontend" / "public" / "vercel.svg",
        RAIZ / "tests" / "test_vercel_despliegue.py",
    ]
    for archivo in retirados:
        assert not archivo.exists(), f"Archivo heredado todavía presente: {archivo.relative_to(RAIZ)}"

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

    for ignorados in (
        RAIZ / ".gitignore",
        RAIZ / "frontend" / ".gitignore",
        RAIZ / "frontend" / ".dockerignore",
    ):
        assert ".vercel" not in ignorados.read_text(encoding="utf-8"), ignorados.relative_to(RAIZ)

    sin_mencion_plataforma_heredada = (
        RAIZ / "pytest.ini",
        RAIZ / "app_core" / "bucle_eventos.py",
        RAIZ / "api" / "routers" / "firma_anf.py",
        RAIZ / "features" / "roadmap" / "services" / "generacion_en_linea.py",
        RAIZ / "frontend" / "src" / "lib" / "auth" / "modo.ts",
        RAIZ / "frontend" / "next.config.cloudrun.ts",
    )
    for archivo in sin_mencion_plataforma_heredada:
        assert "vercel" not in archivo.read_text(encoding="utf-8").lower(), archivo.relative_to(RAIZ)

    readme_frontend = (RAIZ / "frontend" / "README.md").read_text(encoding="utf-8")
    assert "Deploy on Vercel" not in readme_frontend
    assert "vercel.com" not in readme_frontend


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
        assert "api.index" not in prueba_sec.read_text(encoding="utf-8")
