# ¤diagnostico ¤diagnostico-comparativo ¤rbac-tenant
"""API del comparativo del diagnóstico de prueba con el real (DIAG-06). Solo lectura.

La organización y la identidad salen del token; nada del cuerpo ni de la ruta las fija.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from features.diagnostico import diagnostico_service

AUTO_REGISTRO = True
router = APIRouter(prefix="/diagnostico", tags=["Diagnóstico"])

ROLES_CONSULTA = ("dpo", "implementador", "coordinador", "admin_organizacion")
_consulta = require_role(*ROLES_CONSULTA)


@router.get("/comparativo")
async def comparativo(ctx: dict = Depends(_consulta), session: AsyncSession = Depends(get_session)):
    return await diagnostico_service.comparativo_de_organizacion(session, ctx["tenant_id"], ctx["user_id"])
