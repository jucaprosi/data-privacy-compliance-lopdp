# ¤roadmap ¤arbitro
"""RET-03 · Generación de la hoja de ruta sin cola externa (ni UPSTASH_REDIS_URL).

Asegura el retiro definitivo de `app_core/queue/redis_client.py`, `enqueue_generation`,
`get_job`, `pop_job`, `get_job_status`, la ruta `GET /api/v1/roadmaps/jobs/{job_id}`,
el cliente `getJob` / `RoadmapJobStatus` del frontend y el uso exclusivo del paquete
`redis` para la caché de lectura (GCP-06).
"""
from __future__ import annotations

import ast
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://sin-base:sin-base@localhost:1/sin-base")

from app_core.db.session import get_session  # noqa: E402
from features.organizacion import organizacion_service  # noqa: E402
from features.roadmap import roadmap_service  # noqa: E402
from main import app  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
PROHIBIDOS_SIMBOLOS = (
    "UPSTASH_",
    "enqueue_generation",
    "get_job_status",
    "pop_job",
    "RoadmapJobStatus",
)


def _archivos_fuente(carpeta: str, extensiones: tuple[str, ...]) -> list[Path]:
    base = RAIZ / carpeta
    if not base.exists():
        return []
    return [
        p
        for p in base.rglob("*")
        if p.is_file()
        and p.suffix in extensiones
        and "__pycache__" not in p.parts
        and "node_modules" not in p.parts
    ]


def test_sin_cola_externa():
    assert not (RAIZ / "app_core" / "queue" / "redis_client.py").exists()
    assert not (RAIZ / "app_core" / "queue").exists()
    assert not (RAIZ / "tests" / "test_redis_client.py").exists()

    archivos_py = [RAIZ / "main.py"]
    for carpeta in ("api", "app_core", "features", "scripts"):
        archivos_py.extend(_archivos_fuente(carpeta, (".py",)))

    for ruta in archivos_py:
        fuente = ruta.read_text(encoding="utf-8")
        arbol = ast.parse(fuente, filename=str(ruta))
        for nodo in ast.walk(arbol):
            modulos: list[str] = []
            if isinstance(nodo, ast.Import):
                modulos = [alias.name for alias in nodo.names]
            elif isinstance(nodo, ast.ImportFrom) and nodo.module:
                modulos = [nodo.module]
            assert not any("app_core.queue" in m or "redis_client" in m for m in modulos), (
                f"Import prohibido de cola externa en {ruta.relative_to(RAIZ)}"
            )
        for token in PROHIBIDOS_SIMBOLOS:
            assert token not in fuente, f"Símbolo retirado '{token}' presente en {ruta.relative_to(RAIZ)}"

    reqs = (RAIZ / "requirements.txt").read_text(encoding="utf-8")
    lineas_req = [l.strip().lower() for l in reqs.splitlines() if l.strip() and not l.strip().startswith("#")]
    assert not any(l.startswith(("python-dotenv", "boto3", "openai")) for l in lineas_req)
    assert any(l.startswith("redis") for l in lineas_req)
    assert "upstash" not in reqs.lower()


@pytest.mark.asyncio
async def test_ruta_de_trabajos_retirada(monkeypatch):
    for simbolo in ("enqueue_generation", "get_job", "pop_job", "get_job_status"):
        assert not hasattr(roadmap_service, simbolo), f"roadmap_service no debe exportar {simbolo}"

    rutas = {getattr(r, "path", "") for r in app.routes}
    assert "/api/v1/roadmaps/jobs/{job_id}" not in rutas

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as cliente:
        resp = await cliente.get(
            "/api/v1/roadmaps/jobs/job-inexistente",
            headers={"X-User-ID": "u-1", "X-Tenant-ID": "t-1", "X-Role": "implementador"},
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_generacion_en_linea_sin_cola(monkeypatch):
    monkeypatch.setattr(organizacion_service, "has_active_role", AsyncMock(return_value=True))
    esperado = {"job_id": "job-sync-1", "status": "completed", "roadmap_id": "rm-sync-1"}
    inline_mock = AsyncMock(return_value=esperado)
    monkeypatch.setattr(roadmap_service, "generate_roadmap_inline", inline_mock)

    async def _dummy_session():
        yield SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())

    app.dependency_overrides[get_session] = _dummy_session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as cliente:
            resp = await cliente.post(
                "/api/v1/roadmaps/generate",
                json={
                    "tenant_id": "t-1",
                    "user_id": "u-1",
                    "variables": {
                        "plazo_meses": 6,
                        "presupuesto": 1000.0,
                        "moneda": "USD",
                        "equipo": ["DPO"],
                        "dpo": "DPO Prueba",
                        "idioma": "ES",
                    },
                },
                headers={"X-User-ID": "u-1", "X-Tenant-ID": "t-1", "X-Role": "implementador"},
            )
    finally:
        app.dependency_overrides.pop(get_session, None)

    assert resp.status_code == 200, resp.text
    assert resp.json() == esperado
    inline_mock.assert_awaited_once()

    motor = (RAIZ / "features" / "roadmap" / "services" / "generacion_en_linea.py").read_text(encoding="utf-8")
    assert "set_job_status" not in motor
    assert "app_core.queue" not in motor


def test_cliente_frontend_sin_getjob():
    archivos = [
        RAIZ / "frontend" / "src" / "types" / "roadmap.ts",
        RAIZ / "frontend" / "src" / "lib" / "roadmap" / "cliente.ts",
        RAIZ / "frontend" / "src" / "lib" / "roadmap" / "mockServer.ts",
        RAIZ / "frontend" / "src" / "store" / "useRoadmapStore.ts",
    ]
    for archivo in archivos:
        texto = archivo.read_text(encoding="utf-8")
        assert "RoadmapJobStatus" not in texto, f"RoadmapJobStatus presente en {archivo.relative_to(RAIZ)}"
        assert "getJob" not in texto, f"getJob presente en {archivo.relative_to(RAIZ)}"
        assert "/roadmaps/jobs" not in texto, f"/roadmaps/jobs presente en {archivo.relative_to(RAIZ)}"
