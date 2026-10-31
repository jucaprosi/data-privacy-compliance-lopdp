"""Motor de configuración de la organización (sala ADPA: Organización).

Gestiona la consulta y actualización de tamaño y sector del tenant,
asegurando el vocabulario cerrado, parámetros enlazados (cero SQL interpolado)
y registro inmutable en audit_events.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from app_core.audit import registrar_evento
from app_core.errors import CodigoErrorNegocio
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

    # 2. Cambios solicitados: un valor None significa «no cambiar esta columna».
    params: dict[str, Any] = {"tenant_id": tenant_id, "tamano": tamano, "sector": sector}

    payload_auditoria: dict[str, Any] = {}
    if tamano is not None:
        payload_auditoria["tamano"] = tamano
    if sector is not None:
        payload_auditoria["sector"] = sector

    if not payload_auditoria:
        # Nada que actualizar, devolver estado actual
        return await get_tenant_config(session, tenant_id)

    # Sentencia estática: las columnas del SET son literales y los valores llegan como
    # parámetros enlazados; COALESCE conserva el valor actual de la columna no solicitada.
    stmt = text(
        """
        UPDATE tenants
        SET tamano = COALESCE(:tamano, tamano),
            sector = COALESCE(:sector, sector),
            updated_at = now()
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


# === ORG-16 ===
RUC_YA_REGISTRADO = CodigoErrorNegocio(
    codigo="RUC_YA_REGISTRADO",
    status_code=409,
    mensaje_defecto="El RUC ya pertenece a otra organización.",
    action_required=None,
)

_SQL_PERFIL = """
UPDATE tenants
SET razon_social = :razon_social,
    nombre_comercial = :nombre_comercial,
    ruc_identificacion = :ruc,
    sector = :sector,
    tamano = :tamano,
    naturaleza = :naturaleza,
    rol_datos = :rol_datos,
    actividades_riesgo = CAST(:actividades_riesgo AS json),
    updated_at = now()
WHERE id = :tenant_id
RETURNING id, nombre_comercial, razon_social, ruc_identificacion, sector, tamano,
          naturaleza, rol_datos, actividades_riesgo, activo
"""


async def actualizar_perfil_tenant(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    perfil: dict[str, Any],
) -> dict[str, Any]:
    """Paso 1 del alta (ORG-16): razón social, nombre comercial, RUC, sector, tamaño, naturaleza,
    rol de datos y actividades de riesgo. Valores ya validados por el esquema del router; audita
    qué campos se enviaron, no sus valores."""
    import json

    await get_tenant_config(session, tenant_id)
    try:
        async with session.begin_nested():
            fila = (await session.execute(
                text(_SQL_PERFIL),
                {
                    "tenant_id": tenant_id,
                    "razon_social": perfil["razon_social"],
                    "nombre_comercial": perfil["nombre_comercial"],
                    "ruc": perfil["ruc"],
                    "sector": perfil["sector"],
                    "tamano": perfil["tamano"],
                    "naturaleza": perfil["naturaleza"],
                    "rol_datos": perfil["rol_datos"],
                    "actividades_riesgo": json.dumps(perfil["actividades_riesgo"]),
                },
            )).mappings().one()
    except IntegrityError as exc:
        raise ErrorNegocio(RUC_YA_REGISTRADO) from exc
    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="tenant",
        entity_id=tenant_id,
        action="perfil_alta_updated",
        user_id=user_id,
        payload={"campos": sorted(perfil)},
    )
    return dict(fila)
# === fin ORG-16 ===
