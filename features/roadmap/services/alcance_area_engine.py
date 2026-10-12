"""Alcance por área sobre tareas de la hoja de ruta (sala ADPA: Hoja de Ruta).

El alcance del usuario lo decide la sala Organización (compuerta); la pertenencia
de la tarea a un área es dato de la hoja de ruta y se consulta aquí.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from features.organizacion.organizacion_service import RbacError, allowed_area_ids


async def ensure_task_in_area_scope(session: AsyncSession, tenant_id: str, user_id: str, task_id: str) -> None:
    """Exige que la tarea pertenezca a un área del responsable_area. Transversal = sin restricción."""
    scope = await allowed_area_ids(session, tenant_id, user_id)
    if scope is None:
        return
    row = (await session.execute(
        text("SELECT area_id FROM roadmap_tasks WHERE id=:id AND tenant_id=:t"),
        {"id": task_id, "t": tenant_id},
    )).first()
    if not row:
        raise RbacError(404, "Tarea no encontrada")
    if row[0] is None or row[0] not in scope:
        raise RbacError(403, "La tarea no pertenece a un área a su cargo")
