"""Router de administración de la organización: usuarios, áreas y roles por tenant.

Las operaciones de escritura exigen 'admin_organizacion'.
GET /organizacion/me/roles solo requiere X-User-ID y X-Tenant-ID, para que el
cliente descubra con qué roles puede actuar antes de enviar X-Role.
"""
from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import http_error, require_role
from app_core.db.session import get_session
from app_core.schemas.rbac_schema import AreaCreate, AreaUpdate, RoleGrant, UserCreate
from app_core.services import rbac_service

router = APIRouter(prefix="/organizacion", tags=["Organización y roles"])

_admin = require_role("admin_organizacion")


@router.get("/me/roles")
async def my_roles(
    x_user_id: str = Header(..., alias="X-User-ID"),
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_session),
):
    """Roles activos del usuario en el tenant."""
    roles = await rbac_service.list_my_roles(session, x_tenant_id, x_user_id)
    return {"user_id": x_user_id, "tenant_id": x_tenant_id, "roles": roles}


# ============================================================================
# Usuarios
# ============================================================================

@router.get("/usuarios")
async def list_users(
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    """Usuarios con asignaciones activas en el tenant."""
    return await rbac_service.list_tenant_users(session, ctx["tenant_id"])


@router.post("/usuarios", status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    """Crea un usuario, o devuelve el existente con ese email, para asignarle roles."""
    return await rbac_service.create_or_get_user(session, payload)


# ============================================================================
# Áreas
# ============================================================================

@router.get("/areas")
async def list_areas(
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    return await rbac_service.list_areas(session, ctx["tenant_id"])


@router.post("/areas", status_code=status.HTTP_201_CREATED)
async def create_area(
    payload: AreaCreate,
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await rbac_service.create_area(session, ctx["tenant_id"], payload)
    except rbac_service.RbacError as exc:
        raise http_error(exc) from exc


@router.patch("/areas/{area_id}")
async def update_area(
    area_id: str,
    payload: AreaUpdate,
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await rbac_service.update_area(session, ctx["tenant_id"], area_id, payload)
    except rbac_service.RbacError as exc:
        raise http_error(exc) from exc


# ============================================================================
# Asignación de roles
# ============================================================================

@router.get("/roles")
async def list_roles(
    incluir_revocados: bool = False,
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    return await rbac_service.list_role_assignments(
        session, ctx["tenant_id"], include_revoked=incluir_revocados
    )


@router.post("/roles", status_code=status.HTTP_201_CREATED)
async def grant_role(
    payload: RoleGrant,
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    """Asigna un rol. 409 si viola la SoD del DPO o ya existe activo."""
    try:
        return await rbac_service.grant_role(session, ctx["tenant_id"], ctx["user_id"], payload)
    except rbac_service.RbacError as exc:
        raise http_error(exc) from exc


@router.delete("/roles/{assignment_id}")
async def revoke_role(
    assignment_id: str,
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    """Revoca (valid_to = now) una asignación. Conserva el registro para auditoría."""
    try:
        return await rbac_service.revoke_role(session, ctx["tenant_id"], ctx["user_id"], assignment_id)
    except rbac_service.RbacError as exc:
        raise http_error(exc) from exc
