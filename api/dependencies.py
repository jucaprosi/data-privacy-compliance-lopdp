"""Dependencias comunes para la API REST de Plataforma LOPDP 360.

Identidad (ver app_core/security.py): en modo `oidc` (por defecto) el usuario sale del token de Google
verificado y el tenant declarado se autoriza contra la membresía; no existe ningún valor por defecto
que conceda acceso. El modo `headers` (AUTH_MODE=headers, explícito) conserva la identidad por
cabeceras para desarrollo, pruebas y el periodo previo a que el frontend inicie sesión.
"""
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, status

from app_core.security import (
    MODO_HEADERS,
    RolUsuario,
    UsuarioContexto,
    autenticar_en_tenant,
    modo_autenticacion,
)

_ESTADO_AUTENTICADO = "autenticacion_lopdp"


async def obtener_tenant_id_actual(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(default="tenant-default"),
) -> str:
    """Tenant (multi-tenant) de la solicitud, ya autorizado para quien la hace."""
    if modo_autenticacion() == MODO_HEADERS:
        # Modo explícito de desarrollo: sin cabecera se usa un tenant de demostración.
        tenant_id = x_tenant_id or ""
        if not tenant_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Encabezado X-Tenant-ID obligatorio para resolver contexto de aislamiento.",
            )
        return tenant_id.strip()

    # El valor por defecto de la firma es solo del modo headers (contrato congelado de la API):
    # en oidc, sin cabecera real no hay tenant.
    tenant_id = (request.headers.get("x-tenant-id") or "").strip()
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Encabezado X-Tenant-ID obligatorio para resolver contexto de aislamiento.",
        )
    usuario, roles = await autenticar_en_tenant(authorization, tenant_id)
    setattr(request.state, _ESTADO_AUTENTICADO, (usuario, roles))
    return tenant_id


def obtener_usuario_actual(
    request: Request,
    x_user_id: Optional[str] = Header(default="anonimo"),
    x_role: Optional[str] = Header(default="GESTOR_PROCESO"),
    tenant_id: str = Depends(obtener_tenant_id_actual),
) -> UsuarioContexto:
    """Contexto del usuario autenticado."""
    if modo_autenticacion() == MODO_HEADERS:
        try:
            rol_enum = RolUsuario(x_role)
        except ValueError:
            rol_enum = RolUsuario.GESTOR_PROCESO
        return UsuarioContexto(
            usuario_id=x_user_id,
            tenant_id=tenant_id,
            email=f"{x_user_id}@empresa.com",
            rol=rol_enum,
        )

    # oidc: usuario y correo salen del token; X-User-ID y X-Role no cuentan. El rol de independencia
    # se deriva de la membresía real: quien tiene el rol dpo queda sujeto a las restricciones del DPD.
    usuario, roles = getattr(request.state, _ESTADO_AUTENTICADO)
    rol_enum = RolUsuario.DPD_DPO_INTERNO if "dpo" in roles else RolUsuario.GESTOR_PROCESO
    return UsuarioContexto(
        usuario_id=usuario.usuario_id,
        tenant_id=tenant_id,
        email=usuario.email,
        rol=rol_enum,
    )
