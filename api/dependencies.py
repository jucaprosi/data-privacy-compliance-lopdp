"""Dependencias comunes para la API REST de Plataforma LOPDP 360.

Identidad (ver app_core/security.py): en modo `oidc` (por defecto) el usuario sale del token de Google
verificado y el tenant declarado se autoriza contra la membresía; no existe ningún valor por defecto
que conceda acceso. El modo `headers` (AUTH_MODE=headers, explícito) conserva la identidad por
cabeceras para desarrollo, pruebas y el periodo previo a que el frontend inicie sesión.
"""
from typing import Optional

from fastapi import Header, HTTPException, Request, status

from app_core.security import MODO_HEADERS, autenticar_en_tenant, modo_autenticacion

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
