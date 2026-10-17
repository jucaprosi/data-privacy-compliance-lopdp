"""Evidencia de tareas: registro, listado y validación con cuatro ojos (sala ADPA: Hoja de Ruta)."""
from typing import Optional
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from features.organizacion.organizacion_service import SoDViolation, check_four_eyes
from features.roadmap.services.auditoria_engine import registrar_auditoria
from features.roadmap.services.contexto_tenant import set_session_context


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
    await set_session_context(session, tenant_id, user_id)

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
    await registrar_auditoria(session, tenant_id, user_id, task_id, "evidence_uploaded", {"r2_key": r2_key})
    return {"id": evidence_id, "task_id": task_id, "r2_key": r2_key}


async def list_evidence(
    session: AsyncSession,
    tenant_id: str,
    task_id: str,
    rol: Optional[str] = None,
    user_id: Optional[str] = None,
) -> list[dict]:
    """Lista evidencia de una tarea.

    El `responsable_area` ve solo la evidencia que subió él (PRD §5.2, Módulo 5); los demás roles,
    toda la del tenant. Sin identidad de usuario falla cerrado: no devuelve nada.
    """
    await set_session_context(session, tenant_id)
    if rol == "responsable_area":
        if not user_id:
            return []
        rows = (await session.execute(
            text(
                "SELECT * FROM task_evidence WHERE task_id = :tid AND tenant_id = :org "
                "AND uploaded_by = :uid ORDER BY uploaded_at DESC"
            ),
            {"tid": task_id, "org": tenant_id, "uid": user_id},
        )).mappings().all()
        return [dict(r) for r in rows]
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
    """Cambia el estado de validación de una evidencia.

    Cuatro ojos: quien subió la evidencia no puede validarla (SoDViolation).
    """
    await set_session_context(session, tenant_id, user_id)

    current = (await session.execute(
        text("SELECT uploaded_by FROM task_evidence WHERE id = :id AND tenant_id = :tid"),
        {"id": evidence_id, "tid": tenant_id},
    )).first()
    if not current:
        return None
    motivo = check_four_eyes(current[0], user_id)
    if motivo:
        raise SoDViolation(motivo)

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
    await registrar_auditoria(
        session, tenant_id, user_id, task_id, "evidence_validated",
        {"evidence_id": evidence_id, "status": validation_status},
    )
    return dict(row)
