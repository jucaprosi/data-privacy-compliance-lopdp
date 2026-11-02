# -*- coding: utf-8 -*-
# ¤adpa
# ¤firma-electronica
"""Estados de una sesión de firma mientras ANF la procesa (FIRMA-06, BBAP paso 2).

`reservar_envio_anf` bloquea la fila antes de llamar a ANF: cada `POST /signs` puede costar dinero y
una petición doble no se deshace. Si ANF falla, la transacción revierte y la sesión vuelve a
`borrador`. Firmar sigue siendo `marcar_firmado` (FIRMA-03). Sin red: la red vive en `anf_stb_client`.
"""
from __future__ import annotations

import json
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from features.firma_electronica.domain.entities import FirmaSession
from features.firma_electronica.services.firma_session_engine import (
    ENTIDAD_AUDITORIA,
    TransicionFirmaInvalidaError,
)

ACCION_ENVIAR = "enviar_firma_anf"
ACCION_RECHAZAR = "rechazar_firma_anf"
CLAVE_SOLICITUD = "anf_solicitud_id"


async def _actualizar(
    db: AsyncSession,
    firma_id: UUID | str,
    tenant_id: UUID | str,
    estado_origen: str,
    estado_nuevo: str,
    metadatos: dict[str, Any],
) -> FirmaSession:
    fila = (
        await db.execute(
            text(
                """
                UPDATE firma_sessions
                   SET estado = :estado_nuevo,
                       metadatos = metadatos || CAST(:metadatos AS jsonb),
                       actualizado_en = now()
                 WHERE firma_id = CAST(:firma_id AS uuid)
                   AND tenant_id = CAST(:tenant_id AS uuid)
                   AND estado = :estado_origen
                RETURNING *
                """
            ),
            {
                "firma_id": str(firma_id),
                "tenant_id": str(tenant_id),
                "estado_origen": estado_origen,
                "estado_nuevo": estado_nuevo,
                "metadatos": json.dumps(metadatos),
            },
        )
    ).mappings().first()
    if fila is None:
        raise TransicionFirmaInvalidaError(
            f"La sesión de firma '{firma_id}' no está en estado '{estado_origen}'."
        )
    return FirmaSession(**dict(fila))


async def reservar_envio_anf(db: AsyncSession, firma_id: UUID | str, tenant_id: UUID | str) -> FirmaSession:
    """Pasa `borrador` a `pendiente_firma`; una segunda petición simultánea no encuentra la fila."""
    return await _actualizar(db, firma_id, tenant_id, "borrador", "pendiente_firma", {})


async def registrar_solicitud_anf(
    db: AsyncSession,
    firma_id: UUID | str,
    tenant_id: UUID | str,
    solicitud_id: str,
    usuario_id: Optional[str] = None,
) -> FirmaSession:
    """Guarda el id que devolvió ANF, sin el cual el documento firmado no se puede recuperar."""
    sesion = await _actualizar(
        db, firma_id, tenant_id, "pendiente_firma", "pendiente_firma",
        {CLAVE_SOLICITUD: solicitud_id, "anf_ambiente": "TEST"},
    )
    await registrar_evento(
        db,
        tenant_id=str(tenant_id),
        entity_type=ENTIDAD_AUDITORIA,
        entity_id=str(sesion.firma_id),
        action=ACCION_ENVIAR,
        user_id=usuario_id,
        payload={"documento_id": sesion.documento_id, CLAVE_SOLICITUD: solicitud_id, "anf_ambiente": "TEST"},
    )
    return sesion


async def rechazar_firma_anf(
    db: AsyncSession,
    firma_id: UUID | str,
    tenant_id: UUID | str,
    tipo_error: str,
    usuario_id: Optional[str] = None,
) -> FirmaSession:
    """Cierra como `rechazado` una firma que ANF dio por fallida. Solo se guarda el `typeCode`."""
    sesion = await _actualizar(
        db, firma_id, tenant_id, "pendiente_firma", "rechazado", {"anf_error": tipo_error}
    )
    await registrar_evento(
        db,
        tenant_id=str(tenant_id),
        entity_type=ENTIDAD_AUDITORIA,
        entity_id=str(sesion.firma_id),
        action=ACCION_RECHAZAR,
        user_id=usuario_id,
        payload={"documento_id": sesion.documento_id, "anf_error": tipo_error},
    )
    return sesion


__all__ = [
    "ACCION_ENVIAR",
    "ACCION_RECHAZAR",
    "CLAVE_SOLICITUD",
    "rechazar_firma_anf",
    "registrar_solicitud_anf",
    "reservar_envio_anf",
]
