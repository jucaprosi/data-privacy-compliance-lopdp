# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"""Tests de integracion de roadmap_service (BD)."""
import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy import text

from features.organizacion.organizacion_service import SoDViolation
from features.roadmap import roadmap_service
from features.roadmap.roadmap_service import TaskStatus


async def _sembrar_evidencia_doble_validacion(session, tenant: str, tarea: str, sube: str) -> list[str]:
    """RM-28 (R4): evidencia aprobada por coordinador y DPO en E1, que el cierre exige. Devuelve los usuarios creados."""
    coord, dpo = f"rm28-c-{uuid.uuid4().hex[:8]}", f"rm28-d-{uuid.uuid4().hex[:8]}"
    for uid in (coord, dpo):
        await session.execute(text("INSERT INTO users (id, email, nombre) VALUES (:id, :e, :n)"),
                              {"id": uid, "e": f"{uid}@test.local", "n": uid})
    await session.execute(text(
        "INSERT INTO task_evidence (id, task_id, tenant_id, clave_objeto, mime_type, file_size, uploaded_by, "
        "validation_status, validated_by, validated_at, validado_rol, nivel_acreditado, "
        "primera_validacion_por, primera_validacion_en, primera_validacion_rol) "
        "VALUES (:id, :tk, :t, :k, 'application/pdf', 100, :u, 'approved', :dpo, now(), 'dpo', 1, "
        ":coord, now(), 'coordinador')"
    ), {"id": f"ev-{uuid.uuid4().hex[:8]}", "tk": tarea, "t": tenant, "k": f"{tenant}/{tarea}/rm28.pdf",
        "u": sube, "dpo": dpo, "coord": coord})
    return [coord, dpo]


async def _borrar_evidencia_sembrada(session, tarea: str, usuarios: list[str]) -> None:
    await session.execute(text("DELETE FROM task_evidence WHERE task_id = :tk"), {"tk": tarea})
    await session.execute(text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": usuarios})


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
        text("INSERT INTO roadmaps (id, tenant_id, status, variables_json, generado_por) "
             "VALUES (:id, :t, 'generated', '{}', :u)"),
        {"id": rm_id, "t": tenant, "u": user},
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
    sembrados = await _sembrar_evidencia_doble_validacion(db_session, tenant, tk_id, seed_tenants["user_b"])
    await db_session.commit()

    try:
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
    finally:
        await db_session.rollback()
        await _borrar_evidencia_sembrada(db_session, tk_id, sembrados)
        await db_session.commit()


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
        text("INSERT INTO roadmaps (id, tenant_id, status, variables_json, generado_por) "
             "VALUES (:id, :t, 'generated', '{}', :u)"),
        {"id": rm_id, "t": tenant, "u": user},
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
        clave_objeto=f"test/{tk_id}/evidence.pdf",
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
        text("INSERT INTO roadmaps (id, tenant_id, status, variables_json, generado_por) "
             "VALUES (:id, :t, 'generated', '{}', :u)"),
        {"id": rm_id, "t": tenant, "u": user},
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
        clave_objeto=f"test/{tk_id}/doc.pdf",
        mime_type="application/pdf",
        file_size=512,
    )
    await db_session.commit()

    # Cuatro ojos: quien sube no resuelve su evidencia.
    with pytest.raises(SoDViolation):
        await roadmap_service.validate_evidence(
            db_session, tenant, user, ev["id"], "rejected", "OK"
        )
    await db_session.rollback()

    # RM-25b: la validación final exige la primera (coordinador) y una tercera persona con rol dpo o auditor.
    primero = seed_tenants["user_b"]
    await roadmap_service.registrar_primera_validacion(
        db_session, tenant, primero, "coordinador", tk_id, ev["id"]
    )
    validator = f"test-uc-{uuid.uuid4().hex[:8]}"
    await db_session.execute(
        text("INSERT INTO users (id, email, nombre) VALUES (:id, :e, :n)"),
        {"id": validator, "e": f"{validator}@test.local", "n": "Validador final"},
    )
    await db_session.commit()
    result = await roadmap_service.validate_evidence(
        db_session, tenant, validator, ev["id"], "approved", "OK", rol="dpo", nivel_acreditado=2
    )
    await db_session.commit()
    assert result is not None
    assert result["validation_status"] == "approved"

    await db_session.execute(text("DELETE FROM task_audit_log WHERE task_id = :t"), {"t": tk_id})
    await db_session.execute(text("DELETE FROM task_evidence WHERE task_id = :t"), {"t": tk_id})
    await db_session.execute(text("DELETE FROM users WHERE id = :id"), {"id": validator})
    await db_session.commit()
