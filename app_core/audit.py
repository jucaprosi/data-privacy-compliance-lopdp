"""Registro inmutable de eventos que no son de una tarea.

Maneja inserciones append-only sobre la tabla audit_events
usando la sesion del tenant en curso.
"""
from datetime import datetime, timezone
import json
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def registrar_evento(
    session: AsyncSession,
    tenant_id: str,
    entity_type: str,
    entity_id: str,
    action: str,
    user_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> str:
    """Registra un evento de auditoria en audit_events.

    Retorna el id (UUID string) del evento registrado.
    """
    event_id = str(uuid4())
    ahora = datetime.now(timezone.utc)
    payload_json = json.dumps(payload or {})

    await session.execute(
        text(
            """
            INSERT INTO audit_events (
                id,
                tenant_id,
                entity_type,
                entity_id,
                action,
                user_id,
                timestamp,
                payload
            ) VALUES (
                :id,
                :tenant_id,
                :entity_type,
                :entity_id,
                :action,
                :user_id,
                :timestamp,
                CAST(:payload AS JSON)
            )
            """
        ),
        {
            "id": event_id,
            "tenant_id": tenant_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "user_id": user_id,
            "timestamp": ahora,
            "payload": payload_json,
        },
    )
    return event_id
