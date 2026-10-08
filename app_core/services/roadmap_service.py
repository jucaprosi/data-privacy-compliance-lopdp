"""Servicio de roadmap con persistencia async y RLS.

Todas las operaciones reciben tenant_id y user_id explícitos.
Cada query se ejecuta con set_config('app.current_tenant_id', ...).
"""
import json
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.schemas.roadmap_schema import (
    GenerateRoadmapRequest,
    RoadmapDocument,
    TaskStatus,
)


async def _set_session_context(session: AsyncSession, tenant_id: str, user_id: str | None = None) -> None:
    """Inyecta tenant_id y user_id en la sesión para RLS."""
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :tid, true)"),
        {"tid": tenant_id},
    )
    if user_id:
        await session.execute(
            text("SELECT set_config('app.current_user_id', :uid, true)"),
            {"uid": user_id},
        )


async def _audit(session: AsyncSession, tenant_id: str, user_id: str | None, task_id: str, action: str, payload: dict | None = None) -> None:
    """Registra una acción en task_audit_log."""
    await session.execute(
        text("""
            INSERT INTO task_audit_log (id, task_id, tenant_id, action, user_id, payload)
            VALUES (:id, :task_id, :tenant_id, :action, :user_id, CAST(:payload AS JSON))
        """),
        {
            "id": str(uuid4()),
            "task_id": task_id,
            "tenant_id": tenant_id,
            "action": action,
            "user_id": user_id,
            "payload": json.dumps(payload or {}),
        },
    )


def _resolve_completed_at(new_status: TaskStatus) -> datetime | None:
    """Regla de negocio: una tarea completada registra su timestamp; otra estado lo limpia.

    Vive en Python (no en SQL) para:
    - Evitar ambigüedad de tipos en la sentencia.
    - Centralizar la regla de negocio fuera de la capa de datos.
    """
    if new_status == TaskStatus.completada:
        return datetime.now(timezone.utc)
    return None


async def enqueue_generation(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    request: GenerateRoadmapRequest,
) -> str:
    """Persiste roadmap draft y encola job en Redis. Devuelve job_id."""
    from app_core.queue.redis_client import enqueue_job

    await _set_session_context(session, tenant_id, user_id)

    roadmap_id = str(uuid4())
    job_id = str(uuid4())

    await session.execute(
        text("""
            INSERT INTO roadmaps (id, tenant_id, status, variables_json, summary)
            VALUES (:id, :tenant_id, 'draft', CAST(:vars AS JSON), :summary)
        """),
        {
            "id": roadmap_id,
            "tenant_id": tenant_id,
            "vars": request.variables.model_dump_json(),
            "summary": "Roadmap en generación",
        },
    )

    payload = {
        "job_id": job_id,
        "roadmap_id": roadmap_id,
        "tenant_id": tenant_id,
        "user_id": user_id,
        "variables": request.variables.model_dump(),
        "assessment": request.assessment,
    }
    enqueue_job(payload)
    return job_id


async def get_job(job_id: str) -> Optional[dict]:
    """Estado del job desde Redis."""
    from app_core.queue.redis_client import get_job_status
    return get_job_status(job_id)


async def get_roadmap(
    session: AsyncSession,
    tenant_id: str,
    roadmap_id: str,
) -> Optional[dict]:
    """Devuelve roadmap con waves, tasks y evidence."""
    await _set_session_context(session, tenant_id)

    rm = (await session.execute(
        text("SELECT * FROM roadmaps WHERE id = :id AND tenant_id = :tid"),
        {"id": roadmap_id, "tid": tenant_id},
    )).mappings().first()
    if not rm:
        return None

    waves = (await session.execute(
        text("SELECT * FROM roadmap_waves WHERE roadmap_id = :rid ORDER BY sort_order"),
        {"rid": roadmap_id},
    )).mappings().all()

    result = {"roadmap": dict(rm), "waves": []}
    for w in waves:
        tasks = (await session.execute(
            text("SELECT * FROM roadmap_tasks WHERE wave_id = :wid ORDER BY start_date"),
            {"wid": w["id"]},
        )).mappings().all()
        wave = dict(w)
        wave["tasks"] = [dict(t) for t in tasks]
        result["waves"].append(wave)
    return result


async def update_task_status(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    task_id: str,
    new_status: TaskStatus,
) -> Optional[dict]:
    """Cambia estado de una tarea y registra audit log.

    La regla de `completed_at` se resuelve en Python (ver _resolve_completed_at),
    no en SQL, para evitar ambigüedad de tipos y mantener la lógica de negocio
    fuera de la capa de datos.
    """
    await _set_session_context(session, tenant_id, user_id)

    completed_at = _resolve_completed_at(new_status)

    result = await session.execute(
        text("""
            UPDATE roadmap_tasks
            SET status = :status,
                completed_at = :completed_at
            WHERE id = :id AND tenant_id = :tid
            RETURNING *
        """),
        {
            "status": new_status.value,
            "completed_at": completed_at,
            "id": task_id,
            "tid": tenant_id,
        },
    )
    row = result.mappings().first()
    if not row:
        return None

    await _audit(session, tenant_id, user_id, task_id, "status_changed", {"new_status": new_status.value})
    return dict(row)


async def get_kpis(
    session: AsyncSession,
    tenant_id: str,
    roadmap_id: str,
) -> dict:
    """KPIs agregados por roadmap."""
    await _set_session_context(session, tenant_id)

    row = (await session.execute(
        text("""
            SELECT
                COUNT(*) FILTER (WHERE t.status = 'completada') AS completadas,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE t.priority = 'critica') AS criticas,
                COUNT(*) FILTER (WHERE t.priority = 'alta') AS altas
            FROM roadmap_tasks t
            JOIN roadmap_waves w ON t.wave_id = w.id
            WHERE w.roadmap_id = :rid AND t.tenant_id = :tid
        """),
        {"rid": roadmap_id, "tid": tenant_id},
    )).mappings().first()

    total = row["total"] or 0
    completadas = row["completadas"] or 0
    return {
        "total_tareas": total,
        "completadas": completadas,
        "criticas": row["criticas"] or 0,
        "altas": row["altas"] or 0,
        "progreso_porcentaje": round(completadas * 100 / total, 1) if total else 0.0,
    }


async def register_evidence_upload(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    task_id: str,
    r2_key: str,
    mime_type: str,
    file_size: int,
    file_hash: str | None = None,
) -> dict:
    """Registra evidencia tras subida a R2."""
    await _set_session_context(session, tenant_id, user_id)

    evidence_id = str(uuid4())
    await session.execute(
        text("""
            INSERT INTO task_evidence
                (id, task_id, tenant_id, r2_key, mime_type, file_size, file_hash, uploaded_by, validation_status)
            VALUES
                (:id, :task_id, :tid, :r2_key, :mime, :size, :hash, :user, 'pending')
        """),
        {
            "id": evidence_id,
            "task_id": task_id,
            "tid": tenant_id,
            "r2_key": r2_key,
            "mime": mime_type,
            "size": file_size,
            "hash": file_hash,
            "user": user_id,
        },
    )
    await _audit(session, tenant_id, user_id, task_id, "evidence_uploaded", {"r2_key": r2_key})
    return {"id": evidence_id, "task_id": task_id, "r2_key": r2_key}


async def list_evidence(
    session: AsyncSession,
    tenant_id: str,
    task_id: str,
) -> list[dict]:
    """Lista evidencia de una tarea."""
    await _set_session_context(session, tenant_id)
    rows = (await session.execute(
        text("SELECT * FROM task_evidence WHERE task_id = :tid AND tenant_id = :org ORDER BY uploaded_at DESC"),
        {"tid": task_id, "org": tenant_id},
    )).mappings().all()
    return [dict(r) for r in rows]


async def validate_evidence(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    evidence_id: str,
    validation_status: str,
    notes: str = "",
) -> Optional[dict]:
    """Cambia el estado de validación de una evidencia."""
    await _set_session_context(session, tenant_id, user_id)

    result = await session.execute(
        text("""
            UPDATE task_evidence
            SET validation_status = :vs,
                validated_by = :uid,
                validated_at = now(),
                notes = :notes
            WHERE id = :id AND tenant_id = :tid
            RETURNING *
        """),
        {"vs": validation_status, "uid": user_id, "notes": notes, "id": evidence_id, "tid": tenant_id},
    )
    row = result.mappings().first()
    if not row:
        return None

    task_id = row["task_id"]
    await _audit(session, tenant_id, user_id, task_id, "evidence_validated", {"evidence_id": evidence_id, "status": validation_status})
    return dict(row)
