# ¤arquitectura ¤arbitro
"""RET-05 · Entrada única de la API (`main:app`) y salud de routers en Google Cloud Run."""
from __future__ import annotations

import os

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://sin-base:sin-base@localhost:1/sin-base")

import main  # noqa: E402


def test_health_routers():
    cliente = TestClient(main.app)
    for ruta in ("/", "/health", "/api/v1/health"):
        resp = cliente.get(ruta)
        assert resp.status_code in (200, 503)
        datos = resp.json()
        assert datos["status"] in ("OPERATIONAL", "DEGRADED")
        assert "routers" in datos
        assert isinstance(datos["routers"]["total"], int) and datos["routers"]["total"] > 0
