# ¤roadmap ¤rbac-tenant
"""Primera validación de la evidencia de una tarea por el Coordinador (RM-25a).

La validación final sigue siendo el PATCH de `roadmaps.py`; esta ruta solo registra la primera, sin exigirla todavía.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import http_error, require_role
from app_core.db.session import get_session
from features.organizacion.organizacion_service import RbacError
from features.roadmap import roadmap_service

AUTO_REGISTRO = True
router = APIRouter(prefix="/roadmaps", tags=["Hoja de Ruta - Validación de evidencia"])


@router.post("/tasks/{task_id}/evidence/{evidence_id}/primera-validacion")
async def primera_validacion(
    task_id: str,
    evidence_id: str,
    ctx: dict = Depends(require_role("coordinador")),
    session: AsyncSession = Depends(get_session),
):
    """Registra la primera validación. Solo el coordinador; quien subió la evidencia no puede (409)."""
    try:
        valor = await roadmap_service.registrar_primera_validacion(
            session, ctx["tenant_id"], ctx["user_id"], ctx["role"], task_id, evidence_id
        )
    except RbacError as exc:
        raise http_error(exc) from exc
    if not valor:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evidencia no encontrada")
    return valor
