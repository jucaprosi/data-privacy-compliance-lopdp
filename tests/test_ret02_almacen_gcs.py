# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤evidencias ¤roadmap ¤seguridad-tenant ¤arbitro
"""RET-02 · Almacén de evidencias de hoja de ruta en Google Cloud Storage y clave por organización."""
from __future__ import annotations

import ast
import os
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://sin-base:sin-base@localhost:1/sin-base")

from api.routers import roadmaps as router_roadmaps  # noqa: E402
from app_core.db.session import get_session  # noqa: E402
from app_core.errors import CATALOGO_ERRORES  # noqa: E402
from app_core.storage import FirmaSubida  # noqa: E402
from app_core.storage.limites import (  # noqa: E402
    TAMANO_MAXIMO_BYTES,
    clave_pertenece_a_tenant,
    construir_clave_objeto,
)
from features.organizacion import organizacion_service  # noqa: E402
from features.roadmap import roadmap_service  # noqa: E402
from main import app  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
URL_SUBIDA = "/api/v1/roadmaps/tasks/task-1/evidence/upload-url"
URL_REGISTRO = "/api/v1/roadmaps/tasks/task-1/evidence"
HEADERS_ORG_A = {"X-User-ID": "u-a", "X-Tenant-ID": "org-a", "X-Role": "responsable_area"}


class _AlmacenDoble:
    def __init__(self) -> None:
        self.claves_firmadas: list[str] = []

    def firmar_subida(self, clave: str, tipo_mime: str) -> FirmaSubida:
        self.claves_firmadas.append(clave)
        return FirmaSubida(
            clave=clave,
            url=f"https://storage.googleapis.com/evydentia-evidencias/{clave}?X-Goog-Signature=sim",
            metodo="PUT",
            cabeceras={
                "Content-Type": tipo_mime,
                "x-goog-if-generation-match": "0",
            },
        )


@pytest.fixture
def entorno_evidencia(monkeypatch):
    monkeypatch.setenv("EVIDENCIA_FISICA", "true")
    monkeypatch.setattr(organizacion_service, "has_active_role", AsyncMock(return_value=True))
    monkeypatch.setattr(roadmap_service, "ensure_task_in_area_scope", AsyncMock(return_value=None))
    registrar = AsyncMock(return_value={"id": "evd-ret02", "clave_objeto": "ok"})
    monkeypatch.setattr(roadmap_service, "register_evidence_upload", registrar)

    anteriores = dict(app.dependency_overrides)
    app.dependency_overrides[get_session] = lambda: None
    try:
        yield registrar
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(anteriores)


@pytest.mark.asyncio
async def test_clave_lleva_tenant(entorno_evidencia, monkeypatch):
    almacen = _AlmacenDoble()
    monkeypatch.setattr(router_roadmaps, "_almacen_evidencias", lambda: almacen)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as cliente:
        resp = await cliente.post(
            URL_SUBIDA,
            json={"filename": "politica.pdf", "mime_type": "application/pdf", "file_size": 1024},
            headers=HEADERS_ORG_A,
        )

    assert resp.status_code == 200, resp.text
    datos = resp.json()
    assert datos["clave_objeto"].startswith("org-a/task-1/")
    assert datos["key"] == datos["clave_objeto"]
    assert datos["url"].startswith("https://storage.googleapis.com/")
    assert ".." not in datos["clave_objeto"]
    assert almacen.claves_firmadas == [datos["clave_objeto"]]

    clave_unitaria = construir_clave_objeto("org-a", "task-1", "../secreto.pdf")
    assert clave_unitaria.startswith("org-a/task-1/")
    assert clave_pertenece_a_tenant(clave_unitaria, "org-a")
    assert not clave_pertenece_a_tenant("task-1/secreto.pdf", "org-a")
    assert not clave_pertenece_a_tenant("org-b/task-1/secreto.pdf", "org-a")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "clave_ajena",
    [
        "org-b/task-1/archivo.pdf",
        "org-a/../org-b/task-1/archivo.pdf",
        "/org-a/task-1/archivo.pdf",
        "sin-organizacion.pdf",
    ],
)
async def test_no_confirma_clave_de_otro_tenant(entorno_evidencia, monkeypatch, clave_ajena):
    registrar = entorno_evidencia
    monkeypatch.setattr(router_roadmaps, "_almacen_evidencias", lambda: _AlmacenDoble())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as cliente:
        resp = await cliente.post(
            URL_REGISTRO,
            params={"clave_objeto": clave_ajena, "mime_type": "application/pdf", "file_size": 1024},
            headers=HEADERS_ORG_A,
        )

    assert resp.status_code == 403
    assert resp.json()["code"] == "RM_CLAVE_OBJETO_INVALIDA"
    registrar.assert_not_awaited()


@pytest.mark.asyncio
async def test_evidencia_validacion_servidor(entorno_evidencia, monkeypatch):
    assert TAMANO_MAXIMO_BYTES == 25 * 1024 * 1024
    monkeypatch.setattr(router_roadmaps, "_almacen_evidencias", lambda: _AlmacenDoble())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as cliente:
        bad_mime_sign = await cliente.post(
            URL_SUBIDA,
            json={"filename": "payload.exe", "mime_type": "application/x-msdownload", "file_size": 1024},
            headers=HEADERS_ORG_A,
        )
        bad_size_sign = await cliente.post(
            URL_SUBIDA,
            json={"filename": "enorme.pdf", "mime_type": "application/pdf", "file_size": TAMANO_MAXIMO_BYTES + 1},
            headers=HEADERS_ORG_A,
        )
        bad_mime_reg = await cliente.post(
            URL_REGISTRO,
            params={"clave_objeto": "org-a/task-1/payload.exe", "mime_type": "application/x-msdownload", "file_size": 1024},
            headers=HEADERS_ORG_A,
        )
        bad_size_reg = await cliente.post(
            URL_REGISTRO,
            params={"clave_objeto": "org-a/task-1/enorme.pdf", "mime_type": "application/pdf", "file_size": TAMANO_MAXIMO_BYTES + 1},
            headers=HEADERS_ORG_A,
        )

    assert bad_mime_sign.status_code == 415 and bad_mime_sign.json()["code"] == "EVIDENCE_TYPE_NOT_ALLOWED"
    assert bad_size_sign.status_code == 413 and bad_size_sign.json()["code"] == "EVIDENCE_TOO_LARGE"
    assert bad_mime_reg.status_code == 415 and bad_mime_reg.json()["code"] == "EVIDENCE_TYPE_NOT_ALLOWED"
    assert bad_size_reg.status_code == 413 and bad_size_reg.json()["code"] == "EVIDENCE_TOO_LARGE"

    for ruta_rel in (
        "features/evidencias/services/evidencias_engine.py",
        "features/evidencias/services/custodia_generados_engine.py",
        "features/evidencias/services/paquete_inspeccion_engine.py",
        "api/routers/evidencias_inspeccion.py",
    ):
        contenido = (RAIZ / ruta_rel).read_text(encoding="utf-8")
        assert "app_core.storage.limites" in contenido, ruta_rel


@pytest.mark.asyncio
async def test_almacen_no_configurado_falla_cerrado(entorno_evidencia, monkeypatch):
    registrar = entorno_evidencia
    monkeypatch.delenv("GCP_STORAGE_BUCKET", raising=False)
    monkeypatch.delenv("K_SERVICE", raising=False)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as cliente:
        r_firma = await cliente.post(
            URL_SUBIDA,
            json={"filename": "politica.pdf", "mime_type": "application/pdf", "file_size": 1024},
            headers=HEADERS_ORG_A,
        )
        r_confirma = await cliente.post(
            URL_REGISTRO,
            params={"clave_objeto": "org-a/task-1/politica.pdf", "mime_type": "application/pdf", "file_size": 1024},
            headers=HEADERS_ORG_A,
        )

    for resp in (r_firma, r_confirma):
        assert resp.status_code == 503
        cuerpo = resp.json()
        assert cuerpo["code"] == "RM_ALMACEN_NO_DISPONIBLE"
        texto_error = str(cuerpo).lower()
        for detalle in ("gcp", "bucket", "storage", "google", "googleapis"):
            assert detalle not in texto_error
    registrar.assert_not_awaited()


def test_sin_r2():
    """Verifica el contrato positivo del almacén único en Google Cloud Storage y límites."""
    assert (RAIZ / "app_core" / "storage" / "gcs.py").is_file()
    assert (RAIZ / "app_core" / "storage" / "limites.py").is_file()

    archivos_py = [RAIZ / "main.py"]
    for carpeta in ("api", "app_core", "features", "scripts"):
        base = RAIZ / carpeta
        if base.exists():
            archivos_py.extend(p for p in base.rglob("*.py") if "__pycache__" not in p.parts)

    for ruta in archivos_py:
        ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))

    requisitos = (RAIZ / "requirements.txt").read_text(encoding="utf-8").lower()
    assert "google-cloud-storage" in requisitos

    csp = (RAIZ / "frontend" / "next.config.ts").read_text(encoding="utf-8")
    assert "https://storage.googleapis.com" in csp

    migracion = RAIZ / "alembic" / "versions" / "ret02_clave_objeto.py"
    assert migracion.exists()
    assert "clave_objeto" in migracion.read_text(encoding="utf-8")

    for codigo in ("RM_ALMACEN_NO_DISPONIBLE", "RM_CLAVE_OBJETO_INVALIDA"):
        mensaje = CATALOGO_ERRORES[codigo].mensaje_defecto.lower()
        assert "bucket" not in mensaje and "google" not in mensaje and "gcs" not in mensaje
