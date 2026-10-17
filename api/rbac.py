"""Dependencias RBAC por tenant para los routers de la API.

Identidad (ver app_core/security.py): en modo `oidc` (por defecto) el usuario sale del token de
Google verificado y X-User-ID se ignora; en modo `headers` (AUTH_MODE=headers, explícito) sale de
X-User-ID. En ambos, X-Tenant-ID y X-Role son declaraciones: el rol debe estar activo en
user_tenant_roles para ese usuario y ese tenant.
"""
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import get_session
from app_core.security import MODO_HEADERS, modo_autenticacion, usuario_verificado
from features.organizacion import organizacion_service
from features.organizacion.organizacion_service import Role

# Compatibilidad con rol legacy
ROLE_ALIASES = {"GESTOR_PROCESO": "encargado"}


async def get_context(
    authorization: Optional[str] = Header(None),
    x_user_id: str = Header("", alias="X-User-ID"),  # opcional: en oidc se ignora (contrato congelado: type string)
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_role: str = Header(..., alias="X-Role"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Resuelve el contexto del usuario y verifica membresía activa."""
    if modo_autenticacion() == MODO_HEADERS:
        if not x_user_id:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Falta la cabecera X-User-ID")
        user_id = x_user_id
    else:
        # El usuario sale solo del token verificado; X-User-ID, si llega, no cuenta.
        user_id = (await usuario_verificado(session, authorization)).usuario_id
    role = ROLE_ALIASES.get(x_role, x_role)
    if role not in Role.__members__:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"Rol '{x_role}' no autorizado",
        )
    if not await organizacion_service.has_active_role(session, x_tenant_id, user_id, role):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sin membresía activa")
    return {"user_id": user_id, "tenant_id": x_tenant_id, "role": role}


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


def http_error(exc: organizacion_service.RbacError) -> HTTPException:
    return HTTPException(exc.code, exc.detail)
