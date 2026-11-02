# -*- coding: utf-8 -*-
# ¤adpa
# ¤firma-electronica
"""Motor de sesiones de firma persistidas en PostgreSQL (FIRMA-03, BBAP paso 2).

La sesión de BD llega con el tenant ya fijado por `fijar_contexto_rls`; además cada consulta filtra
por `tenant_id`, de modo que un tenant equivocado devuelve «no existe» y no una fila ajena. Crear y
firmar dejan su evento en `audit_events` dentro de la misma transacción que el cambio. Sin red real.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from features.firma_electronica.domain.entities import FirmaSession

ENTIDAD_AUDITORIA = "firma_session"
ACCION_CREAR = "crear_sesion_firma"
ACCION_FIRMAR = "marcar_firmado"

ESTADO_INICIAL = "borrador"
ESTADOS_VALIDOS = ("borrador", "pendiente_firma", "firmado", "rechazado", "error_validacion")
ESTADOS_FIRMABLES = ("borrador", "pendiente_firma")


class SesionFirmaNoEncontradaError(Exception):
    """La sesión no existe en la organización indicada."""


class TransicionFirmaInvalidaError(Exception):
    """La sesión no está en un estado desde el que pueda marcarse como firmada."""


def _valor(dato: Any) -> str:
    """Acepta un `str` o un Enum de `str` (los de la compuerta) y devuelve el texto."""
    return str(getattr(dato, "value", dato))


def _a_sesion(fila) -> FirmaSession:
    return FirmaSession(**dict(fila))


async def crear_sesion_firma(
    db: AsyncSession,
    tenant_id: UUID | str,
    documento_id: str,
    firmante_id: str,
    formato: str,
    proveedor: str,
    sha256_original: str,
    usuario_id: Optional[str] = None,
) -> FirmaSession:
    """Crea la sesión en estado `borrador` y registra el evento `crear_sesion_firma`."""
    fila = (
        await db.execute(
            text(
                """
                INSERT INTO firma_sessions
                    (tenant_id, documento_id, firmante_id, estado, formato, proveedor, sha256_original)
                VALUES
                    (CAST(:tenant_id AS uuid), :documento_id, :firmante_id, :estado,
                     :formato, :proveedor, :sha256_original)
                RETURNING *
                """
            ),
            {
                "tenant_id": str(tenant_id),
                "documento_id": documento_id,
                "firmante_id": firmante_id,
                "estado": ESTADO_INICIAL,
                "formato": _valor(formato),
                "proveedor": _valor(proveedor),
                "sha256_original": sha256_original,
            },
        )
    ).mappings().one()
    sesion = _a_sesion(fila)
    await registrar_evento(
        db,
        tenant_id=str(tenant_id),
        entity_type=ENTIDAD_AUDITORIA,
        entity_id=str(sesion.firma_id),
        action=ACCION_CREAR,
        user_id=usuario_id,
        payload={
            "documento_id": documento_id,
            "sha256_original": sha256_original,
            "formato": sesion.formato,
            "proveedor": sesion.proveedor,
        },
    )
    return sesion


async def obtener_sesion(
    db: AsyncSession, firma_id: UUID | str, tenant_id: UUID | str
) -> Optional[FirmaSession]:
    """Devuelve la sesión de la organización o None si no existe en ella."""
    fila = (
        await db.execute(
            text(
                "SELECT * FROM firma_sessions "
                "WHERE firma_id = CAST(:firma_id AS uuid) AND tenant_id = CAST(:tenant_id AS uuid)"
            ),
            {"firma_id": str(firma_id), "tenant_id": str(tenant_id)},
        )
    ).mappings().first()
    return None if fila is None else _a_sesion(fila)


async def marcar_firmado(
    db: AsyncSession,
    firma_id: UUID | str,
    tenant_id: UUID | str,
    sha256_firmado: str,
    certificado_json: dict[str, Any],
    timestamp_tsa: datetime,
    usuario_id: Optional[str] = None,
) -> FirmaSession:
    """Cierra una sesión no firmada como `firmado`, una sola vez, y registra `marcar_firmado`."""
    fila = (
        await db.execute(
            text(
                """
                UPDATE firma_sessions
                   SET estado = 'firmado',
                       sha256_firmado = :sha256_firmado,
                       certificado_json = CAST(:certificado_json AS jsonb),
                       timestamp_tsa = :timestamp_tsa,
                       actualizado_en = now()
                 WHERE firma_id = CAST(:firma_id AS uuid)
                   AND tenant_id = CAST(:tenant_id AS uuid)
                   AND estado IN ('borrador', 'pendiente_firma')
                RETURNING *
                """
            ),
            {
                "firma_id": str(firma_id),
                "tenant_id": str(tenant_id),
                "sha256_firmado": sha256_firmado,
                "certificado_json": json.dumps(certificado_json, default=str),
                "timestamp_tsa": timestamp_tsa,
            },
        )
    ).mappings().first()
    if fila is None:
        existente = await obtener_sesion(db, firma_id, tenant_id)
        if existente is None:
            raise SesionFirmaNoEncontradaError(f"La sesión de firma '{firma_id}' no existe en la organización.")
        raise TransicionFirmaInvalidaError(
            f"La sesión de firma '{firma_id}' está en estado '{existente.estado}' y no admite firma."
        )
    sesion = _a_sesion(fila)
    await registrar_evento(
        db,
        tenant_id=str(tenant_id),
        entity_type=ENTIDAD_AUDITORIA,
        entity_id=str(sesion.firma_id),
        action=ACCION_FIRMAR,
        user_id=usuario_id,
        payload={
            "documento_id": sesion.documento_id,
            "sha256_firmado": sha256_firmado,
            "timestamp_tsa": timestamp_tsa.isoformat(),
        },
    )
    return sesion


async def listar_sesiones(
    db: AsyncSession,
    tenant_id: UUID | str,
    estado: Optional[str] = None,
    limit: int = 50,
) -> List[FirmaSession]:
    """Lista las sesiones de la organización, de la más reciente a la más antigua."""
    if estado is not None:
        estado = _valor(estado)
        if estado not in ESTADOS_VALIDOS:
            raise ValueError(f"Estado de firma desconocido: '{estado}'.")
    filas = (
        await db.execute(
            text(
                """
                SELECT * FROM firma_sessions
                 WHERE tenant_id = CAST(:tenant_id AS uuid)
                   AND (CAST(:estado AS text) IS NULL OR estado = CAST(:estado AS text))
                 ORDER BY creado_en DESC, firma_id DESC
                 LIMIT :limite
                """
            ),
            {"tenant_id": str(tenant_id), "estado": estado, "limite": max(1, min(int(limit), 500))},
        )
    ).mappings().all()
    return [_a_sesion(f) for f in filas]


__all__ = [
    "ACCION_CREAR",
    "ACCION_FIRMAR",
    "ENTIDAD_AUDITORIA",
    "ESTADOS_VALIDOS",
    "SesionFirmaNoEncontradaError",
    "TransicionFirmaInvalidaError",
    "crear_sesion_firma",
    "listar_sesiones",
    "marcar_firmado",
    "obtener_sesion",
]
