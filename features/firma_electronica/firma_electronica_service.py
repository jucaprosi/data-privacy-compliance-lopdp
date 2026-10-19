# -*- coding: utf-8 -*-
# ¤adpa
# ¤firma-electronica
"""Boceto de la compuerta pública de la sala ADPA: Firma Electrónica (Fase BBAP, paso 1).

Decisión de diseño D-4 y Aporte 111:
- Integración con ANF (Autoridad de Certificación acreditada por ARCOTEL en Ecuador)
  para firma electrónica avanzada/cualificada vía STB directo.
- Compatibilidad con pasarela One-Shot Biometric (Radical / UniverselD) para verificación
  biométrica facial y emisión de certificados de un solo uso.
- Firma de Assessments, consentimientos informados y documentos DPA.

Invariantes ADPA:
- Aislamiento modular estricto (cero imports cruzados internos).
- Interfaz tipada, inmutable y determinista.
- Sin llamadas de red reales ni credenciales activas en este boceto.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import UUID, uuid4


class FormatoFirma(str, Enum):
    """Estándares de firma digital admitidos según normativa ecuatoriana (Ley de Comercio Electrónico)."""
    PADES_BES = "PAdES-BES"
    PADES_B_EPES = "PAdES-B-EPES"
    PADES_B_LTV = "PAdES-B-LTV"  # Con validación a largo plazo y sellado de tiempo TSA
    XADES_BES = "XAdES-BES"


class EstadoFirma(str, Enum):
    """Estados del ciclo de vida de un proceso de firma electrónica."""
    BORRADOR = "borrador"
    PENDIENTE_FIRMA = "pendiente_firma"
    FIRMADO = "firmado"
    RECHAZADO = "rechazado"
    ERROR_VALIDACION = "error_validacion"


class ProveedorFirma(str, Enum):
    """Proveedores admitidos en el ecosistema EVYDENTIA / SMARTCIDI (Aporte 111)."""
    ANF = "ANF"                  # ANF AC — Proveedor B (WS1 STB directo)
    UNIVERSEID = "UNIVERSEID"    # Radical / UniverselD / DARKCAM — Proveedor A (Pasarela One-Shot)


@dataclass(frozen=True)
class CertificadoInfo:
    """Información del certificado digital emitido por entidad de certificación acreditada."""
    emisor: str
    titular_nombre: str
    titular_cedula: str
    ruc_empresa: str | None
    valido_desde: datetime
    valido_hasta: datetime
    numero_serie: str
    acreditado_arcotel: bool = True


@dataclass(frozen=True)
class DocumentoParaFirma:
    """Descriptor del documento o evidencia preparado para firma (Assessment, Consentimiento, DPA)."""
    documento_id: str
    tenant_id: str
    nombre_archivo: str
    mime_type: str
    sha256_original: str
    tamano_bytes: int


@dataclass(frozen=True)
class SesionFirmaPasarela:
    """Descriptor de sesión para la modalidad pasarela (UniverselD / One-Shot Biometric)."""
    session_id: str
    tenant_id: str
    verification_url: str
    expires_at: datetime
    proveedor: ProveedorFirma = ProveedorFirma.UNIVERSEID


@dataclass(frozen=True)
class ResultadoFirma:
    """Resultado auditable de la operación de firmado digital resguardado como evidencia."""
    firma_id: str
    documento_id: str
    tenant_id: str
    firmante_id: str
    estado: EstadoFirma
    formato: FormatoFirma
    sha256_firmado: str
    timestamp_tsa: datetime
    certificado: CertificadoInfo
    proveedor: ProveedorFirma = ProveedorFirma.ANF
    metadatos_auditoria: dict[str, Any] = field(default_factory=dict)


__all__ = [
    "CertificadoInfo",
    "DocumentoParaFirma",
    "EstadoFirma",
    "FormatoFirma",
    "ProveedorFirma",
    "ResultadoFirma",
    "SesionFirmaPasarela",
    "boceto_firmar_documento_anf",
    "boceto_iniciar_sesion_pasarela",
    "boceto_verificar_firma",
    "boceto_verificar_firma_anf",
    "boceto_verificar_webhook_pasarela",
]


def boceto_firmar_documento_anf(
    documento: DocumentoParaFirma,
    firmante_id: str,
    formato: FormatoFirma = FormatoFirma.PADES_B_LTV,
) -> ResultadoFirma:
    """Boceto (BBAP paso 1) para firma electrónica directa vía WS1 STB de ANF AC.

    No realiza llamadas remotas ni requiere credenciales en esta fase.
    """
    ahora = datetime.now(timezone.utc)
    cert_boceto = CertificadoInfo(
        emisor="ANF Autoridad de Certificación Ecuador C.A. (ARCOTEL)",
        titular_nombre="BOCETO REPRESENTANTE",
        titular_cedula="1710034065",
        ruc_empresa=None,
        valido_desde=ahora,
        valido_hasta=ahora,
        numero_serie="BOCETO-SERIE-ANF-001",
        acreditado_arcotel=True,
    )
    return ResultadoFirma(
        firma_id=str(uuid4()),
        documento_id=documento.documento_id,
        tenant_id=documento.tenant_id,
        firmante_id=firmante_id,
        estado=EstadoFirma.FIRMADO,
        formato=formato,
        sha256_firmado=f"boceto-signed-{documento.sha256_original}",
        timestamp_tsa=ahora,
        certificado=cert_boceto,
        proveedor=ProveedorFirma.ANF,
        metadatos_auditoria={"proveedor": "ANF", "modalidad": "STB_directo", "fase": "BBAP_boceto"},
    )


def boceto_iniciar_sesion_pasarela(
    documento: DocumentoParaFirma,
    titular_cedula: str,
    titular_nombres: str,
    return_url: str,
) -> SesionFirmaPasarela:
    """Boceto (BBAP paso 1) para inicio de sesión en pasarela One-Shot Biometric."""
    ahora = datetime.now(timezone.utc)
    return SesionFirmaPasarela(
        session_id=str(uuid4()),
        tenant_id=documento.tenant_id,
        verification_url=f"https://app.universe-id.com/verify/boceto-{uuid4()}",
        expires_at=ahora,
        proveedor=ProveedorFirma.UNIVERSEID,
    )


def boceto_verificar_webhook_pasarela(
    payload_json: Mapping[str, Any],
    firma_recibida: str,
    webhook_secret: str,
) -> bool:
    """Contrato de validación criptográfica HMAC-SHA256 para eventos de webhook entrantes."""
    # En fase boceto no requiere cómputo real si no hay secreto, pero valida el contrato
    if not webhook_secret or not firma_recibida:
        return False
    return True


def boceto_verificar_firma_anf(
    sha256_firmado: str,
) -> dict[str, Any]:
    """Boceto (BBAP paso 1) de validación criptográfica y estado de revocación con ANF."""
    return boceto_verificar_firma(sha256_firmado=sha256_firmado, proveedor=ProveedorFirma.ANF)


def boceto_verificar_firma(
    sha256_firmado: str,
    proveedor: ProveedorFirma = ProveedorFirma.ANF,
) -> dict[str, Any]:
    """Boceto (BBAP paso 1) de validación criptográfica, vigencia y acreditación ARCOTEL."""
    return {
        "valido": True,
        "entidad_certificadora": "ANF Autoridad de Certificación Ecuador C.A." if proveedor == ProveedorFirma.ANF else "Radical / UniverselD",
        "acreditacion_arcotel": "VIGENTE",
        "algoritmo": "SHA256withRSA",
        "revocado": False,
        "timestamp_valido": True,
    }
