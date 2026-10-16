# ¤roadmap ¤adpa
"""Suite de pruebas deterministas para la generación en línea (RM-13, Decisión D-1).

Verifica:
1. Generación en línea exitosa (POST /roadmaps/generate responde 200 con {job_id, status: 'completed', roadmap_id}).
2. Persistencia en base de datos de roadmap, waves y tasks tras generación en línea.
3. Ejecución no bloqueante en hilo aparte (asyncio.to_thread).
4. Manejo de fallos con IA simulada: el roadmap queda con status 'failed' en BD y se retorna status 'failed' permitiendo reintento.
5. Consulta del estado del job vía GET /roadmaps/jobs/{job_id}.
6. Control de acceso RBAC: solo implementador puede generar en línea; otros roles reciben 403 Forbidden.
"""
from __future__ import annotations

import asyncio
from datetime import date, timedelta
import json
import os
from typing import Any
from unittest.mock import patch
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app_core.db.session import get_session
from features.roadmap import roadmap_service
from features.roadmap.roadmap_service import (
    RoadmapDocument,
    generate_roadmap_inline,
)
from main import app

pytestmark = pytest.mark.asyncio


def _async_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@pytest_asyncio.fixture
async def db_session_factory():
    """Generador de sesiones contra la base de datos de test."""
    engine = create_async_engine(_async_url(), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        yield factory
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def api_client(db_session_factory):
    """Cliente HTTP asíncrono para probar el gateway FastAPI."""
    async def _test_get_session():
        async with db_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = _test_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


def _datos_ejemplo_documento(roadmap_id: str, tenant_id: str) -> dict:
    """Documento de ejemplo que cumple estrictamente con RoadmapDocument."""
    today = date.today()
    return {
        "roadmap_id": roadmap_id,
        "tenant_id": tenant_id,
        "resumen_ejecutivo": "Plan de implementación LOPDP generado en línea.",
        "olas": [
            {
                "id": "ola-1",
                "nombre": "Ola 1: Medidas Inmediatas y Gobernanza",
                "plazo": "Meses 1 a 2",
                "objetivo": "Cerrar brechas prioritarias y designar DPO",
                "tareas": [
                    {
                        "id": str(uuid.uuid4()),
                        "control_ref": "P1",
                        "dimension": "D01",
                        "titulo": "Formalizar designación de DPO",
                        "descripcion": "Estructura organizativa de protección de datos.",
                        "responsable": "Dirección General",
                        "prioridad": "critica",
                        "esfuerzo_estimado_horas": 40,
                        "dependencias": [],
                        "entregable": "Resolución de designación de DPO inscrita",
                        "evidencia_requerida": ["Acta de designación"],
                        "kpi": "DPO nombrado y notificado",
                        "fecha_inicio": today.isoformat(),
                        "fecha_fin": (today + timedelta(days=30)).isoformat(),
                    }
                ],
            }
        ],
        "kpis_globales": {
            "criticos_totales": 1,
            "altos_totales": 0,
            "score_objetivo": 92.0,
            "evidencia_verificada_objetivo": 100.0,
        },
    }


def _payload(tenant_id: str, user_id: str) -> dict:
    return {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "variables": {
            "plazo_meses": 6,
            "presupuesto": 1500.0,
            "moneda": "USD",
            "equipo": ["DPO"],
            "dpo": "DPO Principal",
            "idioma": "ES",
        },
        "assessment": {"brechas": ["P1"]},
    }


def _headers(user_id: str, tenant_id: str, role: str) -> dict:
    return {
        "X-User-ID": user_id,
        "X-Tenant-ID": tenant_id,
        "X-Role": role,
    }


@pytest_asyncio.fixture
async def seed_data(db_session_factory):
    """Inserta tenant, usuarios y roles para las pruebas."""
    t_id = f"t1-{uuid.uuid4().hex[:8]}"
    user_imp = f"u-imp-{uuid.uuid4().hex[:8]}"
    user_dpo = f"u-dpo-{uuid.uuid4().hex[:8]}"

    async with db_session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion)
                VALUES (:t, 'Tenant Demo', 'Tenant Demo S.A.', :ruc)
            """),
            {"t": t_id, "ruc": f"RUC{t_id[:10]}"},
        )
        await session.execute(
            text("""
                INSERT INTO users (id, email, nombre) VALUES
                (:u1, :e1, 'Implementador'),
                (:u2, :e2, 'DPO')
            """),
            {
                "u1": user_imp, "e1": f"{user_imp}@test.local",
                "u2": user_dpo, "e2": f"{user_dpo}@test.local",
            },
        )
        await session.execute(
            text("""
                INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES
                (:r1, :u1, :t, 'implementador'),
                (:r2, :u2, :t, 'dpo')
            """),
            {
                "r1": str(uuid.uuid4()), "u1": user_imp, "t": t_id,
                "r2": str(uuid.uuid4()), "u2": user_dpo, "t": t_id,
            },
        )
        await session.commit()

    yield {
        "tenant_id": t_id,
        "user_implementador": user_imp,
        "user_dpo": user_dpo,
    }

    # Limpieza
    async with db_session_factory() as session:
        await session.execute(text("DELETE FROM roadmaps WHERE tenant_id = :t"), {"t": t_id})
        await session.execute(text("DELETE FROM user_tenant_roles WHERE tenant_id = :t"), {"t": t_id})
        await session.execute(text("DELETE FROM users WHERE id IN (:u1, :u2)"), {"u1": user_imp, "u2": user_dpo})
        await session.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t_id})
        await session.commit()


async def test_generacion_en_linea_exitosa_200(api_client, seed_data, db_session_factory):
    """POST /roadmaps/generate responde 200 con {job_id, status: 'completed', roadmap_id} y persiste en BD."""
    tenant_id = seed_data["tenant_id"]
    user_id = seed_data["user_implementador"]

    with patch("features.roadmap.services.generacion_en_linea.generate_roadmap_document") as mock_gen:
        def fake_gen(*args, **kwargs):
            rid = kwargs.get("roadmap_id", "rm-test-default")
            tid = kwargs.get("tenant_id", tenant_id)
            return RoadmapDocument.model_validate(_datos_ejemplo_documento(rid, tid))

        mock_gen.side_effect = fake_gen

        resp = await api_client.post(
            "/api/v1/roadmaps/generate",
            json=_payload(tenant_id, user_id),
            headers=_headers(user_id, tenant_id, "implementador"),
        )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "completed"
    assert "roadmap_id" in data
    roadmap_id = data["roadmap_id"]

    # Verificar persistencia en base de datos
    async with db_session_factory() as session:
        rm_row = (await session.execute(
            text("SELECT status, summary, score_objetivo FROM roadmaps WHERE id = :id AND tenant_id = :tid"),
            {"id": roadmap_id, "tid": tenant_id},
        )).mappings().first()

        assert rm_row is not None
        assert rm_row["status"] == "generated"
        assert rm_row["score_objetivo"] == 92.0

        waves = (await session.execute(
            text("SELECT * FROM roadmap_waves WHERE roadmap_id = :rid"),
            {"rid": roadmap_id},
        )).mappings().all()
        assert len(waves) == 1

        tasks = (await session.execute(
            text("SELECT * FROM roadmap_tasks WHERE wave_id = :wid"),
            {"wid": waves[0]["id"]},
        )).mappings().all()
        assert len(tasks) == 1
        assert tasks[0]["control_ref"] == "P1"
        assert tasks[0]["dimension"] == "D01"


async def test_generacion_en_linea_ejecuta_en_hilo_aparte(api_client, seed_data):
    """Verifica que generate_roadmap_inline ejecuta la llamada con asyncio.to_thread sin bloquear el loop."""
    tenant_id = seed_data["tenant_id"]
    user_id = seed_data["user_implementador"]

    to_thread_called = False
    original_to_thread = asyncio.to_thread

    async def spy_to_thread(func, *args, **kwargs):
        nonlocal to_thread_called
        to_thread_called = True
        return await original_to_thread(func, *args, **kwargs)

    with patch("asyncio.to_thread", side_effect=spy_to_thread), \
         patch("features.roadmap.services.generacion_en_linea.generate_roadmap_document") as mock_gen:
        mock_gen.side_effect = lambda *args, **kwargs: RoadmapDocument.model_validate(
            _datos_ejemplo_documento(kwargs.get("roadmap_id", "rm-th"), tenant_id)
        )

        resp = await api_client.post(
            "/api/v1/roadmaps/generate",
            json=_payload(tenant_id, user_id),
            headers=_headers(user_id, tenant_id, "implementador"),
        )

    assert resp.status_code == 200
    assert to_thread_called is True


async def test_generacion_en_linea_fallo_modelo_marca_failed(api_client, seed_data, db_session_factory):
    """Si la generación falla (ej. LLM error tras reintentos), el roadmap queda 'failed' y el cliente puede reintentar."""
    tenant_id = seed_data["tenant_id"]
    user_id = seed_data["user_implementador"]

    with patch("features.roadmap.services.generacion_en_linea.generate_roadmap_document") as mock_gen:
        mock_gen.side_effect = RuntimeError("Modelo sobrecargado o cuota excedida")

        resp = await api_client.post(
            "/api/v1/roadmaps/generate",
            json=_payload(tenant_id, user_id),
            headers=_headers(user_id, tenant_id, "implementador"),
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "failed"
    roadmap_id = data["roadmap_id"]

    # Verificar en BD que quedó marcado como failed
    async with db_session_factory() as session:
        row = (await session.execute(
            text("SELECT status, summary FROM roadmaps WHERE id = :id AND tenant_id = :tid"),
            {"id": roadmap_id, "tid": tenant_id},
        )).mappings().first()

        assert row is not None
        assert row["status"] == "failed"
        assert "Fallo de generación" in row["summary"]


async def test_get_job_status_retorna_estado_de_generacion(api_client, seed_data):
    """Los endpoints de estado siguen existiendo: GET /roadmaps/jobs/{job_id} responde con datos del job."""
    tenant_id = seed_data["tenant_id"]
    user_id = seed_data["user_implementador"]

    with patch("features.roadmap.services.generacion_en_linea.generate_roadmap_document") as mock_gen:
        mock_gen.side_effect = lambda *args, **kwargs: RoadmapDocument.model_validate(
            _datos_ejemplo_documento(kwargs.get("roadmap_id", "rm-job"), tenant_id)
        )

        resp = await api_client.post(
            "/api/v1/roadmaps/generate",
            json=_payload(tenant_id, user_id),
            headers=_headers(user_id, tenant_id, "implementador"),
        )
        assert resp.status_code == 200
        job_id = resp.json()["job_id"]

        job_resp = await api_client.get(
            f"/api/v1/roadmaps/jobs/{job_id}",
            headers=_headers(user_id, tenant_id, "implementador"),
        )

    assert job_resp.status_code == 200
    job_data = job_resp.json()
    assert job_data.get("status") in ("completed", "running", "queued")


async def test_generacion_en_linea_rbac_dpo_rechazado_403(api_client, seed_data):
    """El rol dpo es rechazado con 403 Forbidden al intentar generar roadmap."""
    tenant_id = seed_data["tenant_id"]
    user_dpo = seed_data["user_dpo"]

    resp = await api_client.post(
        "/api/v1/roadmaps/generate",
        json=_payload(tenant_id, user_dpo),
        headers=_headers(user_dpo, tenant_id, "dpo"),
    )
    assert resp.status_code == 403
