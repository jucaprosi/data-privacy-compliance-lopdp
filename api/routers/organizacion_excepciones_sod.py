# ¤rbac-tenant
# ¤seguridad
"""Router REST para gestión de excepciones de separación de funciones (SoD) (ORG-02).

Endpoints bajo /api/v1/organizacion/excepciones-sod:
- POST   /                  solicitar excepción SoD (coordinador, admin_organizacion)
- GET    /                  listar excepciones (coordinador, implementador, dpo, admin_organizacion)
- GET    /{id}              ver detalle de excepción (coordinador, implementador, dpo, admin_organizacion)
- POST   /{id}/approve      aprobar excepción (admin_organizacion; beneficiario NO, DPO NO)
- POST   /{id}/revoke       revocar excepción (admin_organizacion)
- POST   /{id}/observaciones-dpo  registrar observaciones no vinculantes del DPO (dpo)
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import http_error, require_role
from app_core.db.session import get_session
from features.organizacion import organizacion_service as svc

AUTO_REGISTRO = True

router = APIRouter(prefix="/organizacion/excepciones-sod", tags=["Organización - Excepciones SoD"])

_solicitar = require_role("coordinador", "admin_organizacion")
_lectura = require_role("coordinador", "implementador", "dpo", "admin_organizacion")
_admin = require_role("admin_organizacion")
_dpo = require_role("dpo")


@router.post("", status_code=status.HTTP_201_CREATED)
async def solicitar_excepcion(
    payload: svc.ExcepcionSoDCreate,
    ctx: dict = Depends(_solicitar),
    session: AsyncSession = Depends(get_session),
):
    """Solicita una excepción SoD para la combinación coordinador + responsable_area."""
    try:
        return await svc.solicitar_excepcion_sod(session, ctx["tenant_id"], ctx["user_id"], payload)
    except svc.RbacError as exc:
        raise http_error(exc) from exc


@router.get("")
async def listar_excepciones(
    estado: Optional[str] = None,
    ctx: dict = Depends(_lectura),
    session: AsyncSession = Depends(get_session),
):
    """Lista las excepciones SoD del tenant con filtro opcional de estado."""
    try:
        return await svc.listar_excepciones_sod(session, ctx["tenant_id"], estado)
    except svc.RbacError as exc:
        raise http_error(exc) from exc


@router.get("/{id}")
async def ver_excepcion(
    id: str,
    ctx: dict = Depends(_lectura),
    session: AsyncSession = Depends(get_session),
):
    """Obtiene el detalle de una excepción SoD."""
    try:
        return await svc.obtener_excepcion_sod(session, ctx["tenant_id"], id)
    except svc.RbacError as exc:
        raise http_error(exc) from exc


@router.post("/{id}/approve")
async def aprobar_excepcion(
    id: str,
    payload: svc.ExcepcionSoDAprobar = Body(default_factory=svc.ExcepcionSoDAprobar),
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    """Aprueba la excepción SoD. El beneficiario NO puede aprobarla (salvo con resolución de RL si es único admin). El DPO TAMPOCO."""
    try:
        return await svc.aprobar_excepcion_sod(
            session, ctx["tenant_id"], ctx["user_id"], ctx["role"], id, payload
        )
    except svc.RbacError as exc:
        raise http_error(exc) from exc


@router.post("/{id}/revoke")
async def revocar_excepcion(
    id: str,
    payload: svc.ExcepcionSoDRevocar,
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    """Revoca una excepción SoD activa o pendiente."""
    try:
        return await svc.revocar_excepcion_sod(session, ctx["tenant_id"], ctx["user_id"], id, payload)
    except svc.RbacError as exc:
        raise http_error(exc) from exc


@router.post("/{id}/observaciones-dpo")
async def registrar_observacion_dpo(
    id: str,
    payload: svc.ExcepcionSoDObservacionDpo,
    ctx: dict = Depends(_dpo),
    session: AsyncSession = Depends(get_session),
):
    """Registra observaciones no vinculantes del DPO sobre la excepción SoD."""
    try:
        return await svc.agregar_observacion_dpo(session, ctx["tenant_id"], ctx["user_id"], id, payload)
    except svc.RbacError as exc:
        raise http_error(exc) from exc
