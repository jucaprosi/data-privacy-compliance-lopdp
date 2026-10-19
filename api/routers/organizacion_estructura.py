# ¤rbac-tenant
# ¤sala-organizacion
"""Router para la estructura orgánica de la organización: unidades, cargos y jefaturas (ORG-07).

Endpoints bajo /organizacion/estructura:
- GET /arbol: Árbol completo (unidades, cargos, titulares y vacantes).
- GET /cobertura: Informe de cobertura (unidades sin jefatura, jefaturas vacantes, responsables por designar).
- POST /areas: Crear o registrar nivel de área en la estructura orgánica.
- PATCH /areas/{area_id}: Editar datos/nivel/padre de un área.
- POST /cargos: Crear cargo orgánico en un área.
- PATCH /cargos/{cargo_id}: Editar cargo orgánico (nombre, tipo, es_jefatura, reporta_a, vigencia).
- POST /cargos/{cargo_id}/titular: Asignar o remover titular de un cargo orgánico.

Permisos:
- Escribe el 'admin_organizacion'.
- Leen 'coordinador', 'implementador', 'dpo', 'admin_organizacion' (el DPO solo lectura: audita).
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import http_error, require_role
from app_core.db.session import get_session
from features.organizacion import organizacion_service
from features.organizacion.organizacion_service import (
    AreaEstructuraCreate,
    AreaEstructuraUpdate,
    CargoCreate,
    CargoTitularSet,
    CargoUpdate,
)

AUTO_REGISTRO = True

router = APIRouter(prefix="/organizacion/estructura", tags=["Organización - Estructura Orgánica"])

_admin = require_role("admin_organizacion")
_lectura = require_role("coordinador", "implementador", "dpo", "admin_organizacion")


@router.get("/arbol")
async def get_arbol_estructura(
    ctx: dict = Depends(_lectura),
    session: AsyncSession = Depends(get_session),
):
    """Obtiene el árbol completo de unidades, cargos, titulares y vacantes."""
    try:
        return await organizacion_service.obtener_arbol_estructura(session, ctx["tenant_id"])
    except organizacion_service.RbacError as exc:
        raise http_error(exc) from exc


@router.get("/cobertura")
async def get_informe_cobertura(
    ctx: dict = Depends(_lectura),
    session: AsyncSession = Depends(get_session),
):
    """Obtiene el informe de cobertura orgánica y lista de responsables por designar."""
    try:
        return await organizacion_service.obtener_informe_cobertura(session, ctx["tenant_id"])
    except organizacion_service.RbacError as exc:
        raise http_error(exc) from exc


@router.post("/areas", status_code=status.HTTP_201_CREATED)
async def create_area_estructura(
    payload: AreaEstructuraCreate,
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    """Crea una unidad orgánica dentro de la estructura."""
    try:
        return await organizacion_service.crear_area_estructura(
            session, ctx["tenant_id"], payload, ctx["user_id"]
        )
    except organizacion_service.RbacError as exc:
        raise http_error(exc) from exc


@router.patch("/areas/{area_id}")
async def update_area_estructura(
    area_id: str,
    payload: AreaEstructuraUpdate,
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    """Modifica una unidad orgánica en la estructura."""
    try:
        return await organizacion_service.editar_area_estructura(
            session, ctx["tenant_id"], area_id, payload, ctx["user_id"]
        )
    except organizacion_service.RbacError as exc:
        raise http_error(exc) from exc


@router.post("/cargos", status_code=status.HTTP_201_CREATED)
async def create_cargo_organico(
    payload: CargoCreate,
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    """Crea un nuevo cargo orgánico."""
    try:
        return await organizacion_service.crear_cargo(
            session, ctx["tenant_id"], payload, ctx["user_id"]
        )
    except organizacion_service.RbacError as exc:
        raise http_error(exc) from exc


@router.patch("/cargos/{cargo_id}")
async def update_cargo_organico(
    cargo_id: str,
    payload: CargoUpdate,
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    """Actualiza la definición de un cargo orgánico."""
    try:
        return await organizacion_service.editar_cargo(
            session, ctx["tenant_id"], cargo_id, payload, ctx["user_id"]
        )
    except organizacion_service.RbacError as exc:
        raise http_error(exc) from exc


@router.post("/cargos/{cargo_id}/titular")
async def set_cargo_titular(
    cargo_id: str,
    payload: CargoTitularSet,
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    """Asigna o revoca el titular de un cargo orgánico."""
    try:
        return await organizacion_service.asignar_titular_cargo(
            session, ctx["tenant_id"], cargo_id, payload.titular_user_id, ctx["user_id"]
        )
    except organizacion_service.RbacError as exc:
        raise http_error(exc) from exc
