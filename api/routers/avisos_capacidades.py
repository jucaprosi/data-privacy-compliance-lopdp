# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤notificaciones ¤seguridad
"""Sincronización de los avisos de capacidades editoriales (NOTIF-04), bajo /api/v1/avisos. Solo el operador."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.plataforma import require_operador
from app_core.db.session import get_session
from features.notificaciones.services import avisos_capacidades

AUTO_REGISTRO = True
PREFIJO = "/api/v1"

router = APIRouter(prefix="/avisos", tags=["Avisos de la plataforma"])


@router.post("/sincronizar-capacidades", status_code=status.HTTP_200_OK)
async def sincronizar_capacidades(operador: dict = Depends(require_operador),
                                  session: AsyncSession = Depends(get_session)) -> dict:
    resultado = await avisos_capacidades.sincronizar(session)
    await session.commit()
    return resultado
