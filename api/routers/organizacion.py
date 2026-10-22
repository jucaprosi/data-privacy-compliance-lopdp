"""Router de administración de la organización: usuarios, áreas y roles por tenant.

Las operaciones de escritura exigen 'admin_organizacion'.
GET /organizacion/me/roles solo requiere la identidad del usuario (token verificado en
`oidc`, X-User-ID en `headers`) y X-Tenant-ID, para que el cliente descubra con qué roles
puede actuar antes de enviar X-Role. Lista siempre los roles del usuario autenticado.
"""
from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import get_usuario_autenticado, http_error, require_role
from app_core.db.session import get_session
from features.organizacion import organizacion_service
from features.organizacion.organizacion_service import AreaCreate, AreaUpdate, RoleGrant, UserCreate

router = APIRouter(prefix="/organizacion", tags=["Organización y roles"])

_admin = require_role("admin_organizacion")


@router.get("/me/roles")
async def my_roles(
    user_id: str = Depends(get_usuario_autenticado),
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_session),
):
    """Roles activos del usuario autenticado en el tenant."""
    roles = await organizacion_service.list_my_roles(session, x_tenant_id, user_id)
    return {"user_id": user_id, "tenant_id": x_tenant_id, "roles": roles}


# ============================================================================
# Usuarios
# ============================================================================

@router.get("/usuarios")
async def list_users(
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    """Usuarios con asignaciones activas en el tenant."""
    return await organizacion_service.list_tenant_users(session, ctx["tenant_id"])


@router.post("/usuarios", status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    """Crea un usuario, o devuelve el existente con ese email, para asignarle roles."""
    return await organizacion_service.create_or_get_user(session, payload)


# ============================================================================
# Áreas
# ============================================================================

@router.get("/areas")
async def list_areas(
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    return await organizacion_service.list_areas(session, ctx["tenant_id"])


@router.post("/areas", status_code=status.HTTP_201_CREATED)
async def create_area(
    payload: AreaCreate,
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await organizacion_service.create_area(session, ctx["tenant_id"], payload)
    except organizacion_service.RbacError as exc:
        raise http_error(exc) from exc


@router.patch("/areas/{area_id}")
async def update_area(
    area_id: str,
    payload: AreaUpdate,
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await organizacion_service.update_area(session, ctx["tenant_id"], area_id, payload)
    except organizacion_service.RbacError as exc:
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
    return await organizacion_service.list_role_assignments(
        session, ctx["tenant_id"], include_revoked=incluir_revocados
    )


@router.post("/roles", status_code=status.HTTP_201_CREATED)
async def grant_role(
    payload: RoleGrant,
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    """Asigna un rol directamente (administrador).

    409 si viola la SoD del DPO, si ya existe activo, si es una autoconcesión de un rol
    operativo o si es `responsable_area` habiendo ya `implementador` (el camino es RM-10).
    """
    try:
        return await organizacion_service.conceder_rol_directo(session, ctx["tenant_id"], ctx["user_id"], payload)
    except organizacion_service.RbacError as exc:
        raise http_error(exc) from exc


@router.delete("/roles/{assignment_id}")
async def revoke_role(
    assignment_id: str,
    ctx: dict = Depends(_admin),
    session: AsyncSession = Depends(get_session),
):
    """Revoca (valid_to = now) una asignación. Conserva el registro y deja el evento role_revoked."""
    try:
        return await organizacion_service.revocar_rol_directo(session, ctx["tenant_id"], ctx["user_id"], assignment_id)
    except organizacion_service.RbacError as exc:
        raise http_error(exc) from exc
