# ¤cartera ¤rbac-tenant
"""Cartera de organizaciones por pertenencia (ORG-15, governance/especificaciones/ORG-15.md).

`GET /organizacion/cartera` solo requiere la identidad del token, como `/organizacion/mis-organizaciones`:
la persona ve únicamente las organizaciones donde tiene rol vigente y no se envía `X-Tenant-ID`.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import get_usuario_autenticado
from app_core.db.session import get_session
from features.organizacion import organizacion_service

AUTO_REGISTRO = True

router = APIRouter(prefix="/organizacion", tags=["Organización - Cartera"])


@router.get("/cartera")
async def cartera(
    user_id: str = Depends(get_usuario_autenticado),
    session: AsyncSession = Depends(get_session),
):
    """Una fila por organización de la persona: roles, dimensiones, brechas, hallazgos y tareas vencidas."""
    return {"organizaciones": await organizacion_service.armar_cartera(session, user_id)}
