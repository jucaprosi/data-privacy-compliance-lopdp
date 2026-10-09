"""Tests de integracion.

Skip automatico si `redis` no esta disponible en el interprete actual.
Permite que el arnes use su propio Python sin instalar dependencias.
"""
import importlib.util

import pytest

_REDIS_AVAILABLE = importlib.util.find_spec("redis") is not None
pytestmark = pytest.mark.skipif(
    not _REDIS_AVAILABLE,
    reason="redis no instalado en este entorno (arnes); usar .venv para tests completos",
)
import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy import text

from app_core.schemas.roadmap_schema import (
    GenerateRoadmapRequest,
    PlanningVariables,
    TaskStatus,
)
from app_core.services import roadmap_service
from app_core.services.rbac_service import SoDViolation


def _valid_vars() -> dict:
    return {
        "plazo_meses": 6,
        "presupuesto": 1000.0,
        "moneda": "USD",
        "equipo": ["DPO"],
        "dpo": "Maria",
        "idioma": "ES",
    }


@pytest.mark.asyncio
async def test_enqueue_generation_persiste_roadmap(db_session, seed_tenants):
    """enqueue_generation crea roadmap draft en DB."""
    tenant = seed_tenants["tenant_a"]
    user = seed_tenants["user_a"]

    req = GenerateRoadmapRequest(
        tenant_id=tenant,
        user_id=user,
        variables=PlanningVariables(**_valid_vars()),
    )
    job_id = await roadmap_service.enqueue_generation(
        db_session, tenant, user, req
    )
    await db_session.commit()

    assert job_id is not None
    assert len(job_id) > 0

    row = (await db_session.execute(
        text("SELECT status FROM roadmaps WHERE tenant_id = :t"),
        {"t": tenant},
    )).fetchone()
    assert row is not None
    assert row[0] == "draft"


@pytest.mark.asyncio
async def test_get_roadmap_devuelve_none_si_no_existe(db_session, seed_tenants):
    """get_roadmap devuelve None para ID inexistente."""
    result = await roadmap_service.get_roadmap(
        db_session, seed_tenants["tenant_a"], "no-existe"
    )
    assert result is None


@pytest.mark.asyncio
async def test_get_kpis_roadmap_vacio(db_session, seed_tenants):
    """get_kpis devuelve ceros para roadmap sin tareas."""
    tenant = seed_tenants["tenant_a"]
    rm_id = f"rm-{uuid.uuid4().hex[:8]}"
    await db_session.execute(
        text("INSERT INTO roadmaps (id, tenant_id, status, variables_json) "
             "VALUES (:id, :t, 'draft', '{}')"),
        {"id": rm_id, "t": tenant},
    )
    await db_session.commit()

    kpis = await roadmap_service.get_kpis(db_session, tenant, rm_id)
    assert kpis["total_tareas"] == 0
    assert kpis["completadas"] == 0
    assert kpis["progreso_porcentaje"] == 0.0


@pytest.mark.asyncio
async def test_update_task_status_y_audit_log(db_session, seed_tenants):
    """update_task_status cambia status y registra audit."""
    tenant = seed_tenants["tenant_a"]
    user = seed_tenants["user_a"]

    rm_id = f"rm-{uuid.uuid4().hex[:8]}"
    wv_id = f"wv-{uuid.uuid4().hex[:8]}"
    tk_id = f"tk-{uuid.uuid4().hex[:8]}"

    await db_session.execute(
        text("INSERT INTO roadmaps (id, tenant_id, status, variables_json) "
             "VALUES (:id, :t, 'generated', '{}')"),
        {"id": rm_id, "t": tenant},
    )
    await db_session.execute(
        text("INSERT INTO roadmap_waves (id, roadmap_id, tenant_id, name) "
             "VALUES (:id, :r, :t, 'Ola 1')"),
        {"id": wv_id, "r": rm_id, "t": tenant},
    )
    await db_session.execute(
        text("INSERT INTO roadmap_tasks (id, wave_id, tenant_id, control_ref, dimension, "
             "title, priority, status) "
             "VALUES (:id, :w, :t, 'P10', 'D02', 'Task', 'critica', 'pendiente')"),
        {"id": tk_id, "w": wv_id, "t": tenant},
    )
    await db_session.commit()

    result = await roadmap_service.update_task_status(
        db_session, tenant, user, tk_id, TaskStatus.completada
    )
    await db_session.commit()
    assert result is not None
    assert result["status"] == "completada"

    audit = (await db_session.execute(
        text("SELECT COUNT(*) FROM task_audit_log WHERE task_id = :id"),
        {"id": tk_id},
    )).fetchone()
    assert audit[0] >= 1


@pytest.mark.asyncio
async def test_rls_aislamiento_entre_tenants(db_session, seed_tenants):
    """RLS: tenant A no ve roadmaps de tenant B."""
    ta = seed_tenants["tenant_a"]
    tb = seed_tenants["tenant_b"]

    rm_a = f"rm-a-{uuid.uuid4().hex[:8]}"
    rm_b = f"rm-b-{uuid.uuid4().hex[:8]}"

    # Insertar usando sesión con cada tenant (SET LOCAL permite escribir)
    await db_session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": ta})
    await db_session.execute(
        text("INSERT INTO roadmaps (id, tenant_id, status, variables_json) "
             "VALUES (:id, :t, 'draft', '{}')"),
        {"id": rm_a, "t": ta},
    )
    await db_session.commit()

    await db_session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tb})
    await db_session.execute(
        text("INSERT INTO roadmaps (id, tenant_id, status, variables_json) "
             "VALUES (:id, :t, 'draft', '{}')"),
        {"id": rm_b, "t": tb},
    )
    await db_session.commit()

    # Ver como tenant A
    result_a = await roadmap_service.get_roadmap(db_session, ta, rm_b)
    assert result_a is None, "Tenant A no debe ver roadmap de tenant B"

    result_b = await roadmap_service.get_roadmap(db_session, tb, rm_b)
    assert result_b is not None, "Tenant B sí debe ver su propio roadmap"


@pytest.mark.asyncio
async def test_register_evidence_y_list(db_session, seed_tenants):
    """register_evidence_upload inserta y list_evidence lo recupera."""
    tenant = seed_tenants["tenant_a"]
    user = seed_tenants["user_a"]

    rm_id = f"rm-{uuid.uuid4().hex[:8]}"
    wv_id = f"wv-{uuid.uuid4().hex[:8]}"
    tk_id = f"tk-{uuid.uuid4().hex[:8]}"

    await db_session.execute(
        text("INSERT INTO roadmaps (id, tenant_id, status, variables_json) "
             "VALUES (:id, :t, 'generated', '{}')"),
        {"id": rm_id, "t": tenant},
    )
    await db_session.execute(
        text("INSERT INTO roadmap_waves (id, roadmap_id, tenant_id, name) "
             "VALUES (:id, :r, :t, 'Ola 1')"),
        {"id": wv_id, "r": rm_id, "t": tenant},
    )
    await db_session.execute(
        text("INSERT INTO roadmap_tasks (id, wave_id, tenant_id, control_ref, dimension, "
             "title, priority, status) "
             "VALUES (:id, :w, :t, 'P10', 'D02', 'Task', 'critica', 'pendiente')"),
        {"id": tk_id, "w": wv_id, "t": tenant},
    )
    await db_session.commit()

    ev = await roadmap_service.register_evidence_upload(
        db_session, tenant, user, tk_id,
        r2_key=f"test/{tk_id}/evidence.pdf",
        mime_type="application/pdf",
        file_size=2048,
        file_hash="a" * 64,
    )
    await db_session.commit()
    assert ev["id"] is not None

    lista = await roadmap_service.list_evidence(db_session, tenant, tk_id)
    assert len(lista) >= 1
    assert any(e["id"] == ev["id"] for e in lista)


@pytest.mark.asyncio
async def test_validate_evidence(db_session, seed_tenants):
    """validate_evidence cambia validation_status."""
    tenant = seed_tenants["tenant_a"]
    user = seed_tenants["user_a"]

    rm_id = f"rm-{uuid.uuid4().hex[:8]}"
    wv_id = f"wv-{uuid.uuid4().hex[:8]}"
    tk_id = f"tk-{uuid.uuid4().hex[:8]}"

    await db_session.execute(
        text("INSERT INTO roadmaps (id, tenant_id, status, variables_json) "
             "VALUES (:id, :t, 'generated', '{}')"),
        {"id": rm_id, "t": tenant},
    )
    await db_session.execute(
        text("INSERT INTO roadmap_waves (id, roadmap_id, tenant_id, name) "
             "VALUES (:id, :r, :t, 'Ola 1')"),
        {"id": wv_id, "r": rm_id, "t": tenant},
    )
    await db_session.execute(
        text("INSERT INTO roadmap_tasks (id, wave_id, tenant_id, control_ref, dimension, "
             "title, priority, status) "
             "VALUES (:id, :w, :t, 'P10', 'D02', 'Task', 'critica', 'pendiente')"),
        {"id": tk_id, "w": wv_id, "t": tenant},
    )
    await db_session.commit()

    ev = await roadmap_service.register_evidence_upload(
        db_session, tenant, user, tk_id,
        r2_key=f"test/{tk_id}/doc.pdf",
        mime_type="application/pdf",
        file_size=512,
    )
    await db_session.commit()

    # Cuatro ojos: quien sube no valida.
    with pytest.raises(SoDViolation):
        await roadmap_service.validate_evidence(
            db_session, tenant, user, ev["id"], "approved", "OK"
        )
    await db_session.rollback()

    validator = seed_tenants["user_b"]
    result = await roadmap_service.validate_evidence(
        db_session, tenant, validator, ev["id"], "approved", "OK"
    )
    await db_session.commit()
    assert result is not None
    assert result["validation_status"] == "approved"
