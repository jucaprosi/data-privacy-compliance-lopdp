# -*- coding: utf-8 -*-
# ¤adpa
# ¤firma-electronica
"""Entidades de dominio de la sala Firma Electrónica (FIRMA-03, BBAP paso 2)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class FirmaSession:
    """Sesión de firma de un documento de una organización, persistida en `firma_sessions`."""
    firma_id: UUID
    tenant_id: UUID
    documento_id: str
    firmante_id: str
    estado: str
    formato: str
    proveedor: str
    sha256_original: str
    sha256_firmado: str | None
    timestamp_tsa: datetime | None
    certificado_json: dict[str, Any] | None
    metadatos: dict[str, Any]
    creado_en: datetime
    actualizado_en: datetime


__all__ = ["FirmaSession"]
