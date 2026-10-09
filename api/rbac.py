"""Dependencias RBAC por tenant para los routers de la API.

Auth por headers: X-User-ID, X-Tenant-ID, X-Role.
El rol declarado en X-Role debe estar activo en user_tenant_roles.
"""
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import get_session
from app_core.schemas.roadmap_schema import Role
from app_core.services import rbac_service

# Compatibilidad con rol legacy
ROLE_ALIASES = {"GESTOR_PROCESO": "encargado"}


async def get_context(
    x_user_id: str = Header(..., alias="X-User-ID"),
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_role: str = Header(..., alias="X-Role"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Resuelve el contexto del usuario y verifica membresía activa."""
    role = ROLE_ALIASES.get(x_role, x_role)
    if role not in Role.__members__:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"Rol '{x_role}' no autorizado",
        )
    if not await rbac_service.has_active_role(session, x_tenant_id, x_user_id, role):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sin membresía activa")
    return {"user_id": x_user_id, "tenant_id": x_tenant_id, "role": role}


def require_role(*roles: str):
    """Dependency que exige que el usuario tenga uno de los roles indicados."""
    async def checker(ctx: dict = Depends(get_context)) -> dict:
        if ctx["role"] not in roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Rol {ctx['role']} no autorizado para esta operación",
            )
        return ctx
    return checker


def http_error(exc: rbac_service.RbacError) -> HTTPException:
    return HTTPException(exc.code, exc.detail)
