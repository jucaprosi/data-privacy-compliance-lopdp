# ¤roadmap
"""Router de edición de detalles de tareas de la Hoja de Ruta.

Endpoint: PATCH /api/v1/roadmaps/tasks/{id}/details
Rol requerido: implementador.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from features.roadmap import roadmap_service
from features.roadmap.roadmap_service import TaskDetailsUpdate

AUTO_REGISTRO = True

router = APIRouter(prefix="/roadmaps", tags=["Hoja de Ruta Inteligente"])


@router.patch("/tasks/{task_id}/details")
async def patch_task_details(
    task_id: str,
    payload: TaskDetailsUpdate,
    ctx: dict = Depends(require_role("implementador")),
    session: AsyncSession = Depends(get_session),
):
    """Edita detalles operativos de una tarea (título, fechas, responsable, KPI, entregable).
    
    Solo permitido para el rol 'implementador'.
    """
    updated_task = await roadmap_service.edit_task_details(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        task_id=task_id,
        payload=payload,
    )
    if not updated_task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarea no encontrada")
    return updated_task
