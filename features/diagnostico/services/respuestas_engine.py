"""Persistencia aislada por tenant de las respuestas del diagnóstico."""
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.db.session import fijar_contexto_rls

CONTROLES_VALIDOS = {f"P{i}" for i in range(1, 74)}
DIMENSIONES_VALIDAS = {f"D{i:02d}" for i in range(1, 11)}


async def listar_respuestas(session: AsyncSession, tenant_id: str, user_id: str) -> list[dict[str, Any]]:
    await fijar_contexto_rls(session, tenant_id, user_id)
    result = await session.execute(text("SELECT pregunta_id, control_ref, dimension, estado, nivel_evidencia, criticidad, respondido_por, actualizado_en FROM diagnostico_respuestas WHERE tenant_id = :tenant_id ORDER BY pregunta_id"), {"tenant_id": tenant_id})
    return [dict(row) for row in result.mappings().all()]


async def guardar_respuestas(session: AsyncSession, tenant_id: str, user_id: str, respuestas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    await fijar_contexto_rls(session, tenant_id, user_id)
    for respuesta in respuestas:
        if respuesta["control_ref"] not in CONTROLES_VALIDOS or respuesta["dimension"] not in DIMENSIONES_VALIDAS:
            raise ValueError("Control o dimensión fuera del catálogo")
        await session.execute(text("""
            INSERT INTO diagnostico_respuestas (tenant_id, pregunta_id, control_ref, dimension, estado, nivel_evidencia, criticidad, respondido_por, actualizado_en)
            VALUES (:tenant_id, :pregunta_id, :control_ref, :dimension, :estado, :nivel_evidencia, :criticidad, :respondido_por, :actualizado_en)
            ON CONFLICT (tenant_id, pregunta_id) DO UPDATE SET control_ref = EXCLUDED.control_ref, dimension = EXCLUDED.dimension, estado = EXCLUDED.estado, nivel_evidencia = EXCLUDED.nivel_evidencia, criticidad = EXCLUDED.criticidad, respondido_por = EXCLUDED.respondido_por, actualizado_en = EXCLUDED.actualizado_en
        """), {**respuesta, "tenant_id": tenant_id, "respondido_por": user_id, "actualizado_en": datetime.now(timezone.utc)})
        await registrar_evento(session, tenant_id, "diagnostico_respuesta", str(respuesta["pregunta_id"]), "diagnostico_respuesta_guardada", user_id, {"pregunta_id": respuesta["pregunta_id"]})
    return await listar_respuestas(session, tenant_id, user_id)
