# ¤rbac-tenant
# ¤sala-organizacion
"""Router para las designaciones formales del DPD y del Coordinador (ORG-06).

Endpoints bajo /api/v1/organizacion/designaciones:
- POST /: Crear designación formal (solo admin_organizacion).
- GET /: Listar designaciones formales (admin_organizacion, coordinador, dpo, implementador).
- GET /estado: Informe de estado de solo lectura (admin_organizacion, coordinador, dpo, implementador).
- GET /{id}: Ver detalle de una designación formal.
- POST /{id}/declarar: Registrar declaración previa de conflictos (SOLO la propia persona designada).
- POST /{id}/inscribir: Registrar constancia de inscripción ante SPDP (solo admin_organizacion).
- POST /{id}/revocar: Revocar formalmente la designación (solo admin_organizacion).
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import http_error, require_role
from app_core.db.session import get_session
from features.organizacion import organizacion_service
from features.organizacion.organizacion_service import (
    DeclaracionConflictosCreate,
    DesignacionCreate,
    InscripcionSpdpCreate,
    RevocacionCreate,
    TipoDesignacion,
)

AUTO_REGISTRO = True

router = APIRouter(prefix="/organizacion/designaciones", tags=["Organización - Designaciones Formales"])

_admin = require_role("admin_organizacion")
_lectura = require_role("admin_organizacion", "coordinador", "dpo", "implementador")
_autenticado = require_role("admin_organizacion", "coordinador", "dpo", "implementador", "responsable_area")


@router.post("", status_code=status.HTTP_201_CREATED)
async def post_designacion(
    payload: DesignacionCreate,
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    """Crea una designación formal (DPD o Coordinador). Requiere admin_organizacion."""
    try:
        return await organizacion_service.crear_designacion_formal(
            session=session,
            tenant_id=ctx["tenant_id"],
            admin_user_id=ctx["user_id"],
            payload=payload,
        )
    except organizacion_service.RbacError as exc:
        raise http_error(exc) from exc


@router.get("")
async def get_designaciones(
    tipo: Optional[TipoDesignacion] = Query(default=None),
    ctx: dict = Depends(_lectura),
    session: AsyncSession = Depends(get_session),
):
    """Lista las designaciones formales del tenant."""
    try:
        return await organizacion_service.listar_designaciones_formales(
            session=session,
            tenant_id=ctx["tenant_id"],
            tipo=tipo,
        )
    except organizacion_service.RbacError as exc:
        raise http_error(exc) from exc


@router.get("/estado")
async def get_estado_designaciones(
    ctx: dict = Depends(_lectura),
    session: AsyncSession = Depends(get_session),
):
    """Informe de estado de designaciones: DPD (designado, declaración, inscripción, conflicto) y Coordinador (mandato)."""
    try:
        return await organizacion_service.obtener_informe_estado_designaciones(
            session=session,
            tenant_id=ctx["tenant_id"],
        )
    except organizacion_service.RbacError as exc:
        raise http_error(exc) from exc


@router.get("/{designacion_id}")
async def get_designacion(
    designacion_id: str,
    ctx: dict = Depends(_lectura),
    session: AsyncSession = Depends(get_session),
):
    """Obtiene el detalle de una designación formal."""
    try:
        return await organizacion_service.obtener_designacion_formal(
            session=session,
            tenant_id=ctx["tenant_id"],
            designacion_id=designacion_id,
        )
    except organizacion_service.RbacError as exc:
        raise http_error(exc) from exc


@router.post("/{designacion_id}/declarar")
async def post_declaracion_conflictos(
    designacion_id: str,
    payload: DeclaracionConflictosCreate,
    ctx: dict = Depends(_autenticado),
    session: AsyncSession = Depends(get_session),
):
    """Registra la declaración previa de conflictos. SOLO la propia persona designada puede declarar."""
    try:
        return await organizacion_service.registrar_declaracion_conflictos(
            session=session,
            tenant_id=ctx["tenant_id"],
            designacion_id=designacion_id,
            user_id_declarador=ctx["user_id"],
            payload=payload,
        )
    except organizacion_service.RbacError as exc:
        raise http_error(exc) from exc


@router.post("/{designacion_id}/inscribir")
async def post_inscripcion_spdp(
    designacion_id: str,
    payload: InscripcionSpdpCreate,
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    """Registra la constancia de inscripción ante la SPDP. Requiere admin_organizacion."""
    try:
        return await organizacion_service.registrar_inscripcion_spdp(
            session=session,
            tenant_id=ctx["tenant_id"],
            designacion_id=designacion_id,
            admin_user_id=ctx["user_id"],
            payload=payload,
        )
    except organizacion_service.RbacError as exc:
        raise http_error(exc) from exc


@router.post("/{designacion_id}/revocar")
async def post_revocar_designacion(
    designacion_id: str,
    payload: RevocacionCreate,
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    """Revoca formalmente la designación. Requiere admin_organizacion."""
    try:
        return await organizacion_service.revocar_designacion_formal(
            session=session,
            tenant_id=ctx["tenant_id"],
            designacion_id=designacion_id,
            admin_user_id=ctx["user_id"],
            payload=payload,
        )
    except organizacion_service.RbacError as exc:
        raise http_error(exc) from exc
