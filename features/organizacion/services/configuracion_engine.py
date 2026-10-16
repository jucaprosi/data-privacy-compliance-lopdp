"""Motor de configuración de la organización (sala ADPA: Organización).

Gestiona la consulta y actualización de tamaño y sector del tenant,
asegurando el vocabulario cerrado, parámetros enlazados (cero SQL interpolado)
y registro inmutable en audit_events.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from features.organizacion.domain.tamanos import TAMANOS_ORGANIZACION


async def get_tenant_config(session: AsyncSession, tenant_id: str) -> dict[str, Any]:
    """Obtiene la configuración actual de la organización para el tenant dado."""
    stmt = text(
        """
        SELECT
            id,
            nombre_comercial,
            razon_social,
            ruc_identificacion,
            sector,
            tamano,
            activo
        FROM tenants
        WHERE id = :tenant_id
        """
    )
    result = await session.execute(stmt, {"tenant_id": tenant_id})
    row = result.mappings().one_or_none()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organización no encontrada",
        )
    return dict(row)


async def update_tenant_config(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    tamano: Optional[str] = None,
    sector: Optional[str] = None,
) -> dict[str, Any]:
    """Actualiza tamaño y/o sector de la organización y registra evento en audit_events."""
    if tamano is not None and tamano not in TAMANOS_ORGANIZACION:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Tamaño inválido '{tamano}'. Opciones permitidas: {TAMANOS_ORGANIZACION}",
        )

    # 1. Verificar existencia de la organización
    await get_tenant_config(session, tenant_id)

    # 2. Construir update parametrizado
    update_fields = []
    params: dict[str, Any] = {"tenant_id": tenant_id}

    payload_auditoria: dict[str, Any] = {}
    if tamano is not None:
        update_fields.append("tamano = :tamano")
        params["tamano"] = tamano
        payload_auditoria["tamano"] = tamano
    if sector is not None:
        update_fields.append("sector = :sector")
        params["sector"] = sector
        payload_auditoria["sector"] = sector

    if not update_fields:
        # Nada que actualizar, devolver estado actual
        return await get_tenant_config(session, tenant_id)

    update_fields.append("updated_at = now()")

    stmt = text(
        f"""
        UPDATE tenants
        SET {", ".join(update_fields)}
        WHERE id = :tenant_id
        RETURNING
            id,
            nombre_comercial,
            razon_social,
            ruc_identificacion,
            sector,
            tamano,
            activo
        """
    )
    result = await session.execute(stmt, params)
    updated_row = result.mappings().one()

    # 3. Registrar auditoría inmutable en audit_events
    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="tenant",
        entity_id=tenant_id,
        action="config_updated",
        user_id=user_id,
        payload=payload_auditoria,
    )

    return dict(updated_row)
