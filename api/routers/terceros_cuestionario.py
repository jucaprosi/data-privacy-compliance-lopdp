# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤developer-architect ¤seguridad ¤terceros
"""Router privado de cuestionarios de garantías para encargados (TER-02).

Endpoints:
- POST /api/v1/terceros/{id}/cuestionarios
- GET  /api/v1/terceros/{id}/cuestionarios
- POST /api/v1/terceros/cuestionarios/{id}/revision
"""
from __future__ import annotations

from datetime import date
from typing import Any, List, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from app_core.errors import ErrorNegocio
from features.terceros import terceros_service

AUTO_REGISTRO = True

router = APIRouter(prefix="/terceros", tags=["Terceros - Cuestionarios (TER-02)"])

_roles_gestion = require_role("implementador", "coordinador")
_roles_consulta = require_role("implementador", "coordinador", "dpo", "admin_organizacion", "auditor")


class CrearCuestionarioIn(BaseModel):
    dias_vigencia: int = Field(7, description="Vigencia del enlace en días (1 a 30)")


class RevisionCuestionarioIn(BaseModel):
    decision: Literal["conforme", "correccion", "rechazado"]
    comentario: Optional[str] = None
    proxima_revision: Optional[date] = None


@router.post("/{id}/cuestionarios", status_code=status.HTTP_201_CREATED)
async def crear_enlace_cuestionario(
    id: str,
    payload: CrearCuestionarioIn = CrearCuestionarioIn(),
    ctx: dict = Depends(_roles_gestion),
    session: AsyncSession = Depends(get_session),
):
    try:
        datos, _ = await terceros_service.crear_enlace_cuestionario(
            session,
            tenant_id=ctx["tenant_id"],
            user_id=ctx["user_id"],
            tercero_id=id,
            dias_vigencia=payload.dias_vigencia,
        )
        return datos
    except ErrorNegocio as e:
        raise HTTPException(status_code=e.status_code, detail=e.code)


@router.get("/{id}/cuestionarios")
async def listar_cuestionarios(
    id: str,
    ctx: dict = Depends(_roles_consulta),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await terceros_service.listar_cuestionarios_tercero(
            session,
            tenant_id=ctx["tenant_id"],
            tercero_id=id,
        )
    except ErrorNegocio as e:
        raise HTTPException(status_code=e.status_code, detail=e.code)


@router.post("/cuestionarios/{id}/revision")
async def revisar_cuestionario(
    id: str,
    payload: RevisionCuestionarioIn,
    ctx: dict = Depends(_roles_gestion),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await terceros_service.revisar_cuestionario(
            session,
            tenant_id=ctx["tenant_id"],
            user_id=ctx["user_id"],
            cuestionario_id=id,
            decision=payload.decision,
            comentario=payload.comentario,
            proxima_revision=payload.proxima_revision,
        )
    except ErrorNegocio as e:
        raise HTTPException(status_code=e.status_code, detail=e.code)
