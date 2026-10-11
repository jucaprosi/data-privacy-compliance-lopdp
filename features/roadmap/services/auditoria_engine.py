"""Registro de acciones sobre tareas en task_audit_log (sala ADPA: Hoja de Ruta)."""
import json
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def registrar_auditoria(
    session: AsyncSession,
    tenant_id: str,
    user_id: str | None,
    task_id: str,
    action: str,
    payload: dict | None = None,
) -> None:
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
