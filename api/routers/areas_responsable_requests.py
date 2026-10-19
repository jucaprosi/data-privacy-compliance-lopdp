# ¤rbac-tenant
"""Flujo de alta de responsables de área (PRD §5.3.1): el coordinador solicita, el implementador ejecuta.

Endpoints, todos bajo /api/v1/areas/responsable-requests:
- POST   /                  solicitar el alta (coordinador)
- GET    /                  listar (coordinador, implementador); filtro opcional ?estado=
- GET    /{id}              ver una solicitud (coordinador, implementador)
- PATCH  /{id}              cancelar, solo quien la solicitó y solo si está pendiente (coordinador)
- POST   /{id}/approve      aprobar (implementador)
- POST   /{id}/reject       rechazar (implementador)
- POST   /{id}/execute      ejecutar: asigna el rol responsable_area (implementador)

Los errores de negocio se traducen aquí: RbacError a su código HTTP y ErrorNegocio por el manejador
global (con `code` y `action_required`). El coordinador que intente aprobar o ejecutar recibe 403.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import http_error, require_role
from app_core.db.session import get_session
from features.organizacion import organizacion_service as svc

AUTO_REGISTRO = True

router = APIRouter(prefix="/areas/responsable-requests", tags=["Organización - Alta de responsables de área"])

_coordinador = require_role("coordinador")
_coordinador_o_implementador = require_role("coordinador", "implementador")
_implementador = require_role("implementador")


@router.post("", status_code=status.HTTP_201_CREATED)
async def solicitar_alta(
    payload: svc.ResponsableRequestCreate,
    ctx: dict = Depends(_coordinador),
    session: AsyncSession = Depends(get_session),
):
    """El coordinador solicita dar de alta a un responsable de área."""
    try:
        return await svc.create_responsable_request(session, ctx["tenant_id"], ctx["user_id"], payload)
    except svc.RbacError as exc:
        raise http_error(exc) from exc


@router.get("")
async def listar_altas(
    estado: Optional[str] = None,
    ctx: dict = Depends(_coordinador_o_implementador),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await svc.list_responsable_requests(session, ctx["tenant_id"], estado)
    except svc.RbacError as exc:
        raise http_error(exc) from exc


@router.get("/{id}")
async def ver_alta(
    id: str,
    ctx: dict = Depends(_coordinador_o_implementador),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await svc.get_responsable_request(session, ctx["tenant_id"], id)
    except svc.RbacError as exc:
        raise http_error(exc) from exc


@router.patch("/{id}")
async def cancelar_alta(
    id: str,
    payload: svc.ResponsableRequestPatch,
    ctx: dict = Depends(_coordinador),
    session: AsyncSession = Depends(get_session),
):
    """Cancela la solicitud. El cuerpo solo admite {"estado": "cancelada"}."""
    try:
        return await svc.cancel_responsable_request(session, ctx["tenant_id"], ctx["user_id"], id)
    except svc.RbacError as exc:
        raise http_error(exc) from exc


@router.post("/{id}/approve")
async def aprobar_alta(
    id: str,
    payload: svc.ResponsableRequestDecision = Body(default_factory=svc.ResponsableRequestDecision),
    ctx: dict = Depends(_implementador),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await svc.approve_responsable_request(session, ctx["tenant_id"], ctx["user_id"], id, payload)
    except svc.RbacError as exc:
        raise http_error(exc) from exc


@router.post("/{id}/reject")
async def rechazar_alta(
    id: str,
    payload: svc.ResponsableRequestDecision = Body(default_factory=svc.ResponsableRequestDecision),
    ctx: dict = Depends(_implementador),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await svc.reject_responsable_request(session, ctx["tenant_id"], ctx["user_id"], id, payload)
    except svc.RbacError as exc:
        raise http_error(exc) from exc


@router.post("/{id}/execute")
async def ejecutar_alta(
    id: str,
    ctx: dict = Depends(_implementador),
    session: AsyncSession = Depends(get_session),
):
    """Asigna el rol responsable_area. Atómico: el área, el rol, el estado y la auditoría, o nada."""
    try:
        return await svc.execute_responsable_request(session, ctx["tenant_id"], ctx["user_id"], id)
    except svc.RbacError as exc:
        raise http_error(exc) from exc
