# -*- coding: utf-8 -*-
# ¤adpa
# ¤firma-electronica
"""Boceto de la compuerta pública de la sala ADPA: Firma Electrónica (Fase BBAP, paso 1).

Decisión de diseño D-4: Integración con ANF (Autoridad de Certificación
acreditada por ARCOTEL en Ecuador) para firma electrónica avanzada/cualificada
de evidencias de cumplimiento, actas de comité y dictámenes del DPO.

Invariantes ADPA:
- Aislamiento modular estricto (cero imports cruzados internos).
- Interfaz tipada y determinista.
- Sin proveedor real ni credenciales en este boceto.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Sequence
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


@dataclass(frozen=True)
class CertificadoInfo:
    """Información del certificado digital emitido por entidad de certificación acreditada (ej. ANF)."""
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
    """Descriptor del documento o evidencia preparado para firma."""
    documento_id: str
    tenant_id: str
    nombre_archivo: str
    mime_type: str
    sha256_original: str
    tamano_bytes: int


@dataclass(frozen=True)
class ResultadoFirma:
    """Resultado auditable de la operación de firmado digital."""
    firma_id: str
    documento_id: str
    tenant_id: str
    firmante_id: str
    estado: EstadoFirma
    formato: FormatoFirma
    sha256_firmado: str
    timestamp_tsa: datetime
    certificado: CertificadoInfo
    metadatos_anf: dict[str, Any] = field(default_factory=dict)


__all__ = [
    "CertificadoInfo",
    "DocumentoParaFirma",
    "EstadoFirma",
    "FormatoFirma",
    "ResultadoFirma",
    "boceto_firmar_documento_anf",
    "boceto_verificar_firma_anf",
]


def boceto_firmar_documento_anf(
    documento: DocumentoParaFirma,
    firmante_id: str,
    formato: FormatoFirma = FormatoFirma.PADES_B_LTV,
) -> ResultadoFirma:
    """Boceto (BBAP paso 1) para firma electrónica de evidencia/acta vía ANF.

    No realiza llamadas remotas ni requiere credenciales en esta fase.
    """
    ahora = datetime.now(timezone.utc)
    cert_boceto = CertificadoInfo(
        emisor="ANF Autoridad de Certificacion Ecuador (ARCOTEL)",
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
        metadatos_anf={"proveedor": "ANF", "fase": "BBAP_boceto"},
    )


def boceto_verificar_firma_anf(
    sha256_firmado: str,
) -> dict[str, Any]:
    """Boceto (BBAP paso 1) de validación criptográfica y estado de revocación (OCSP/CRL)."""
    return {
        "valido": True,
        "entidad_certificadora": "ANF Autoridad de Certificacion Ecuador",
        "acreditacion_arcotel": "VIGENTE",
        "algoritmo": "SHA256withRSA",
        "revocado": False,
        "timestamp_valido": True,
    }
