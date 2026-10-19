"""Router de asignación de tareas a responsables de área (sala ADPA: Hoja de Ruta).
`¤roadmap` `¤rbac-tenant`

Endpoint: POST /roadmaps/tasks/{id}/assign
Rol autorizado: coordinador
Verifica membresía y alcances por área a través de la compuerta de Organización.
"""
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from features.roadmap import roadmap_service

AUTO_REGISTRO = True

router = APIRouter(prefix="/roadmaps", tags=["Hoja de Ruta Inteligente - Asignación"])


class AssignTaskRequest(BaseModel):
    responsable_id: str = Field(..., min_length=1, description="ID del usuario responsable de área")


@router.post("/tasks/{task_id}/assign", status_code=status.HTTP_200_OK)
async def assign_task(
    task_id: str,
    payload: AssignTaskRequest,
    ctx: dict = Depends(require_role("coordinador")),
    session: AsyncSession = Depends(get_session),
):
    """Asigna una tarea a un responsable de área. Rol autorizado: coordinador."""
    return await roadmap_service.assign_task_to_responsable(
        session=session,
        tenant_id=ctx["tenant_id"],
        user_id=ctx["user_id"],
        task_id=task_id,
        responsable_id=payload.responsable_id,
    )
