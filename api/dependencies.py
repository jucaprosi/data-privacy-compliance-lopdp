"""Dependencias comunes para la API REST de Plataforma LOPDP 360."""
from fastapi import Header, HTTPException, status, Depends
from typing import Optional

def obtener_tenant_id_actual(x_tenant_id: Optional[str] = Header(default="tenant-default")) -> str:
    """Extrae y valida el identificador de inquilino (Multi-tenant) desde los encabezados HTTP."""
    if not x_tenant_id or not x_tenant_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Encabezado X-Tenant-ID obligatorio para resolver contexto de aislamiento.",
        )
    return x_tenant_id.strip()

from app_core.security import UsuarioContexto, RolUsuario, validar_permiso_sod, AccionOperativa

def obtener_usuario_actual(
    x_user_id: Optional[str] = Header(default="anonimo"),
    x_role: Optional[str] = Header(default="GESTOR_PROCESO"),
    tenant_id: str = Depends(obtener_tenant_id_actual)
) -> UsuarioContexto:
    """Extrae el contexto del usuario autenticado."""
    try:
        rol_enum = RolUsuario(x_role)
    except ValueError:
        rol_enum = RolUsuario.GESTOR_PROCESO
    
    return UsuarioContexto(
        usuario_id=x_user_id,
        tenant_id=tenant_id,
        email=f"{x_user_id}@empresa.com",
        rol=rol_enum
    )
