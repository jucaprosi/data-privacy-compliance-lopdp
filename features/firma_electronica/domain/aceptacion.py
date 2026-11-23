# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤firma-electronica
"""Entidades de dominio y códigos de error de FIRMA-02: aceptación simple con acuse."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app_core.errors import CodigoErrorNegocio


# --------------------------------------------------------------------------- #
# Códigos de error de negocio (FIRMA-02)                                       #
# --------------------------------------------------------------------------- #

ACEPTACION_CADUCADA = CodigoErrorNegocio(
    codigo="ACEPTACION_CADUCADA",
    status_code=410,
    mensaje_defecto="El enlace de aceptación ha caducado o ya fue utilizado.",
)

ACEPTACION_NO_ENCONTRADA = CodigoErrorNegocio(
    codigo="ACEPTACION_NO_ENCONTRADA",
    status_code=404,
    mensaje_defecto="El enlace de aceptación no existe.",
)

PERSONA_NO_ENCONTRADA = CodigoErrorNegocio(
    codigo="PERSONA_NO_ENCONTRADA",
    status_code=404,
    mensaje_defecto="La persona destinataria no está en el inventario de la organización.",
)

DOCUMENTO_NO_APROBADO = CodigoErrorNegocio(
    codigo="DOCUMENTO_NO_APROBADO",
    status_code=409,
    mensaje_defecto="Solo se pueden enviar a aceptación documentos con estado 'aprobado'.",
)


# --------------------------------------------------------------------------- #
# Entidades de dominio                                                          #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class DocumentoParaAceptacion:
    """Información del documento que BIB-107 proveerá a través de biblioteca_service."""
    id: UUID
    tenant_id: UUID
    nombre: str
    sha256: str
    estado: str


@dataclass(frozen=True)
class PersonaParaAceptacion:
    """Persona del inventario de la organización (ORG-17) a la que se envía el documento."""
    id: UUID
    nombre: str
    email: str


@dataclass
class Aceptacion:
    """Fila de la tabla aceptaciones."""
    id: UUID
    tenant_id: UUID
    documento_id: UUID
    documento_sha256: str
    persona_id: UUID
    token_hash: str
    caduca_en: datetime
    nombre: str
    email: str
    creado_por: UUID
    creado_en: datetime
    aceptado_en: Optional[datetime] = None
    ip: Optional[str] = None
    acuse_sha256: Optional[str] = None

    @property
    def vigente(self) -> bool:
        return self.aceptado_en is None and self.caduca_en > datetime.now(timezone.utc)


@dataclass(frozen=True)
class EnlaceGenerado:
    """Resultado de crear un enlace de aceptación para una persona."""
    persona_id: str
    url: str


@dataclass(frozen=True)
class InfoPublicaAceptacion:
    """Datos que se muestran en la página pública /aceptar/<token>."""
    nombre_documento: str
    organizacion: str
    sha256: str


@dataclass(frozen=True)
class ResultadoAceptacion:
    """Resultado de aceptar: hash de la custodia y bytes del PDF de acuse."""
    acuse_sha256: str
    acuse_pdf: bytes
