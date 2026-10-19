# ¤roadmap ¤seguridad
"""Router para la consulta del registro de auditoría de Hoja de Ruta.

Endpoint: GET /api/v1/roadmaps/{roadmap_id}/audit-log
Roles autorizados: coordinador, dpo, implementador, admin_organizacion.
Invariantes: Auto-registro ADPA, RLS multi-tenant, cero SQL interpolado.
"""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from features.roadmap import roadmap_service

AUTO_REGISTRO = True

router = APIRouter(prefix="/roadmaps", tags=["Hoja de Ruta - Auditoría"])


@router.get("/{roadmap_id}/audit-log")
async def get_audit_log(
    roadmap_id: str,
    limit: int = Query(50, ge=1, le=200, description="Cantidad máxima de eventos a recuperar"),
    offset: int = Query(0, ge=0, description="Número de eventos a omitir"),
    ctx: dict = Depends(require_role("coordinador", "dpo", "implementador", "admin_organizacion")),
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """Consulta paginada y de solo lectura del audit log de un roadmap."""
    resultado = await roadmap_service.get_roadmap_audit_log(
        session=session,
        tenant_id=ctx["tenant_id"],
        roadmap_id=roadmap_id,
        limit=limit,
        offset=offset,
    )
    if resultado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap no encontrado")

    return resultado
