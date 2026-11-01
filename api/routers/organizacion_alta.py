# ¤rbac-tenant ¤alta-organizacion
"""Router del alta de la organización en siete pasos (ORG-16).

Endpoints (prefijo /api/v1/organizacion):
- GET  /alta               estado derivado de los pasos; cualquier rol de gestión lo lee.
- GET  /alta/sugerencias   catálogo de estructura según el sector; admin_organizacion e implementador.
- POST /alta/paso/{id}     guarda un paso; admin_organizacion e implementador (el dpo recibe 403).

La organización y la identidad salen del contexto de la sesión; el cuerpo no las admite.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import get_context, http_error, require_role
from app_core.db.session import get_session
from features.organizacion import organizacion_service

AUTO_REGISTRO = True

router = APIRouter(prefix="/organizacion", tags=["Organización - Alta en siete pasos"])

_LECTORES = ("admin_organizacion", "implementador", "coordinador", "dpo")
_ESCRITORES = ("admin_organizacion", "implementador")


@router.get("/alta")
async def get_alta(
    ctx: dict = Depends(require_role(*_LECTORES)),
    session: AsyncSession = Depends(get_session),
):
    """Pasos del asistente y cuáles están completos, derivado de los datos guardados."""
    return await organizacion_service.obtener_estado_alta(session, ctx["tenant_id"])


@router.get("/alta/sugerencias")
async def get_sugerencias(
    ctx: dict = Depends(require_role(*_ESCRITORES)),
    session: AsyncSession = Depends(get_session),
):
    """Tratamientos y terceros típicos del sector, solo como estructura."""
    return await organizacion_service.obtener_sugerencias_alta(session, ctx["tenant_id"])


@router.post("/alta/paso/{paso_id}")
async def post_paso(
    paso_id: str,
    cuerpo: dict[str, Any],
    ctx: dict = Depends(require_role(*_ESCRITORES)),
    session: AsyncSession = Depends(get_session),
):
    """Guarda el paso por la compuerta de su sala."""
    try:
        return await organizacion_service.guardar_paso_alta(
            session, ctx["tenant_id"], ctx["user_id"], paso_id, cuerpo,
        )
    except organizacion_service.RbacError as exc:
        raise http_error(exc) from exc
