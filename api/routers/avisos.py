# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤notificaciones ¤seguridad
"""Router de los avisos de la plataforma (NOTIF-02), bajo /api/v1/avisos.

Cada persona lee y marca solo los suyos (RLS); la sincronización es del operador, como el disparo de NORM-05.
"""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import get_usuario_autenticado
from api.routers.plataforma import require_operador
from app_core.db.session import get_session
from features.notificaciones import notificaciones_service as svc

AUTO_REGISTRO = True
PREFIJO = "/api/v1"

router = APIRouter(prefix="/avisos", tags=["Avisos de la plataforma"])


class AvisoOut(BaseModel):
    id: str
    titulo: str
    texto: str
    enlace: Optional[str]
    leido: bool
    pendiente: bool
    creado_en: str


class BandejaOut(BaseModel):
    avisos: list[AvisoOut]
    sin_leer: int


@router.get("", response_model=BandejaOut)
async def listar(filtro: Literal["sin_leer", "todos"] = "todos", antes: Optional[str] = Query(None, max_length=40),
                 usuario: str = Depends(get_usuario_autenticado), session: AsyncSession = Depends(get_session)):
    r = await svc.avisos_servicio.listar(session, usuario, filtro, antes)
    return {"avisos": [{**a, "creado_en": a["creado_en"].isoformat()} for a in r["avisos"]], "sin_leer": r["sin_leer"]}


@router.post("/sincronizar", status_code=status.HTTP_200_OK)
async def sincronizar(operador: dict = Depends(require_operador), session: AsyncSession = Depends(get_session)) -> dict:
    resultado = await svc.avisos_servicio.sincronizar(session)
    await session.commit()
    return resultado


@router.post("/{aviso_id}/leido", status_code=status.HTTP_204_NO_CONTENT)
async def marcar_leido(aviso_id: str, usuario: str = Depends(get_usuario_autenticado),
                       session: AsyncSession = Depends(get_session)) -> None:
    if not await svc.avisos_servicio.marcar_leido(session, usuario, aviso_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, {"codigo": "AVISO_NO_ENCONTRADO"})
    await session.commit()
