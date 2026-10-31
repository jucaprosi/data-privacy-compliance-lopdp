# ¤adpa
"""Capacidades de la sala Organización para otras salas."""
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession


async def areas_permitidas(session: AsyncSession, tenant_id: str, user_id: str) -> Optional[set[str]]:
    """Áreas al alcance del usuario; None significa alcance transversal a toda la organización."""
    from features.organizacion import organizacion_service

    return await organizacion_service.allowed_area_ids(session, tenant_id, user_id)


async def listar_areas(session: AsyncSession, tenant_id: str) -> list[dict]:
    from features.organizacion import organizacion_service

    return await organizacion_service.list_areas(session, tenant_id)


async def listar_usuarios(session: AsyncSession, tenant_id: str) -> list[dict]:
    from features.organizacion import organizacion_service

    return await organizacion_service.list_tenant_users(session, tenant_id)


async def listar_roles_de_usuario(session: AsyncSession, tenant_id: str, user_id: str) -> list[dict]:
    """Fija al usuario consultado en el contexto RLS; quien llama debe restablecer el suyo."""
    from features.organizacion import organizacion_service

    return await organizacion_service.list_my_roles(session, tenant_id, user_id)


async def configuracion_de_organizacion(session: AsyncSession, tenant_id: str) -> dict:
    from features.organizacion import organizacion_service

    return await organizacion_service.get_tenant_config(session, tenant_id)


async def informe_de_designaciones(session: AsyncSession, tenant_id: str) -> dict[str, Any]:
    from features.organizacion import organizacion_service

    return await organizacion_service.obtener_informe_estado_designaciones(session, tenant_id)


async def crear_o_recuperar_usuario(session: AsyncSession, email: str, nombre: str) -> dict:
    from features.organizacion import organizacion_service

    return await organizacion_service.create_or_get_user(
        session=session,
        payload=organizacion_service.UserCreate(email=email, nombre=nombre),
    )


async def conceder_rol(session: AsyncSession, tenant_id: str, concedido_por: str, user_id: str, rol: str) -> dict:
    from features.organizacion import organizacion_service

    return await organizacion_service.grant_role(
        session=session,
        tenant_id=tenant_id,
        granted_by=concedido_por,
        payload=organizacion_service.RoleGrant(user_id=user_id, role=rol),
    )
