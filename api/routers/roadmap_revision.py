# ¤roadmap ¤rbac-tenant
"""Rutas de revisión humana y activación de la Hoja de Ruta con cuatro ojos (RM-27)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import http_error, require_role
from app_core.db.session import get_session
from features.organizacion.organizacion_service import RbacError
from features.roadmap import roadmap_service

AUTO_REGISTRO = True
router = APIRouter(prefix="/roadmaps", tags=["Roadmap"])

_ROLES_CONSULTA = (
    "responsable_area",
    "coordinador",
    "dpo",
    "implementador",
    "admin_organizacion",
    "auditor",
)


@router.get("/{roadmap_id}/revision")
async def consultar_revision(
    roadmap_id: str,
    ctx: dict = Depends(require_role(*_ROLES_CONSULTA)),
    session: AsyncSession = Depends(get_session),
):
    """Devuelve el estado de revisión humana de la hoja de ruta."""
    try:
        return await roadmap_service.obtener_estado_revision(
            session, ctx["tenant_id"], roadmap_id, ctx["user_id"], rol=ctx["role"]
        )
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Hoja de ruta no encontrada") from exc
    except RbacError as exc:
        raise http_error(exc) from exc


@router.post("/{roadmap_id}/activar")
async def activar_hoja(
    roadmap_id: str,
    ctx: dict = Depends(require_role("coordinador", "dpo")),
    session: AsyncSession = Depends(get_session),
):
    """Activa una hoja de ruta generada. Solo coordinador o DPO que no la generó (409 si es la misma persona)."""
    try:
        return await roadmap_service.activar_hoja_ruta(
            session, ctx["tenant_id"], roadmap_id, ctx["user_id"], rol=ctx["role"]
        )
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Hoja de ruta no encontrada") from exc
    except RbacError as exc:
        raise http_error(exc) from exc
