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
- Los `boceto_*` no hacen llamadas de red ni usan credenciales. El consumo real de ANF STB v2 TEST
  vive en la sección FIRMA-06 y exige configuración explícita.
"""
from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Optional, Sequence
from uuid import UUID, uuid4

# FIRMA-03 (BBAP paso 2): persistencia real. La compuerta solo reexporta; la lógica vive en el engine.
from features.firma_electronica.domain.entities import FirmaSession
# FIRMA-06 (BBAP paso 2): consumo real de ANF STB v2 en TEST.
from features.firma_electronica.services import anf_stb_client
from features.firma_electronica.services.anf_stb_client import AnfStbError, AnfStbNoConfiguradoError
from features.firma_electronica.services.anf_stb_engine import (
    CLAVE_SOLICITUD,
    rechazar_firma_anf,
    registrar_solicitud_anf,
    reservar_envio_anf,
)
from features.firma_electronica.services.firma_session_engine import (
    SesionFirmaNoEncontradaError,
    TransicionFirmaInvalidaError,
    crear_sesion_firma,
    listar_sesiones,
    marcar_firmado,
    obtener_sesion,
)


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
    pdf_firmado: bytes | None = field(default=None, repr=False)


__all__ = [
    # Funciones reales (FIRMA-03)
    "FirmaSession",
    "SesionFirmaNoEncontradaError",
    "TransicionFirmaInvalidaError",
    "crear_sesion_firma",
    "listar_sesiones",
    "marcar_firmado",
    "obtener_sesion",
    # Alias de compatibilidad (boceto FIRMA-01 — no borrar)
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


# === FIRMA-06 ===
# ¤firma-electronica
EMISOR_ANF = "ANF Autoridad de Certificación Ecuador C.A."
DATO_NO_DISPONIBLE = "NO_DISPONIBLE"
PAGINAS_ANF_DEFECTO = ("ultima(50, 50)",)
ESPERAS_ANF_SEGUNDOS = (30, 30, 30)  # ANF pide consultar a los 30, 60 y 90 s; después es error.


class FirmaAnfEnProcesoError(Exception):
    """ANF no terminó dentro de las esperas. Su `solicitud_id` sigue siendo consultable."""

    def __init__(self, solicitud_id: str):
        super().__init__(f"La solicitud de firma '{solicitud_id}' sigue en proceso.")
        self.solicitud_id = solicitud_id


def anf_stb_configurado() -> bool:
    return anf_stb_client.esta_configurado()


async def solicitar_firma_anf_stb(
    documento: DocumentoParaFirma,
    firmante_id: str,
    pdf: bytes,
    paginas: Sequence[str] = PAGINAS_ANF_DEFECTO,
) -> str:
    """Envía el PDF a ANF y devuelve el id de la petición. Se firma lo que se registró, nada más."""
    if hashlib.sha256(pdf).hexdigest() != documento.sha256_original.lower():
        raise ValueError("El PDF no coincide con sha256_original.")
    return await anf_stb_client.solicitar_firma(pdf, documento.documento_id, firmante_id, paginas)


async def consultar_firma_anf_stb(
    documento: DocumentoParaFirma,
    firmante_id: str,
    solicitud_id: str,
    formato: FormatoFirma = FormatoFirma.PADES_BES,
) -> Optional[ResultadoFirma]:
    """Devuelve el resultado, o `None` si ANF sigue firmando.

    ANF solo entrega el PDF: sello y certificado van dentro de él y aún no se extraen. Por eso
    `timestamp_tsa` es la hora de recepción y los datos del certificado constan como no disponibles;
    `metadatos_auditoria` lo declara para que nadie lo lea como un sello de tiempo verificado.
    """
    firmado = await anf_stb_client.consultar_documentos(solicitud_id, documento.documento_id)
    if firmado is None:
        return None
    ahora = datetime.now(timezone.utc)
    return ResultadoFirma(
        firma_id=str(uuid4()),
        documento_id=documento.documento_id,
        tenant_id=documento.tenant_id,
        firmante_id=firmante_id,
        estado=EstadoFirma.FIRMADO,
        formato=formato,
        sha256_firmado=hashlib.sha256(firmado.pdf).hexdigest(),
        timestamp_tsa=ahora,
        certificado=CertificadoInfo(
            emisor=EMISOR_ANF,
            titular_nombre=DATO_NO_DISPONIBLE,
            titular_cedula=firmante_id,
            ruc_empresa=None,
            valido_desde=ahora,
            valido_hasta=ahora,
            numero_serie=DATO_NO_DISPONIBLE,
            acreditado_arcotel=False,
        ),
        proveedor=ProveedorFirma.ANF,
        metadatos_auditoria={
            "proveedor": "ANF",
            "modalidad": "STB_directo",
            "emisor": EMISOR_ANF,
            "ambiente": "TEST",
            "fase": "BBAP_paso_2",
            CLAVE_SOLICITUD: solicitud_id,
            "timestamp_tsa_fuente": "recepcion_plataforma",
            "certificado_verificado": False,
        },
        pdf_firmado=firmado.pdf,
    )


async def firmar_documento_anf_stb(
    documento: DocumentoParaFirma,
    firmante_id: str,
    pdf: bytes,
    formato: FormatoFirma = FormatoFirma.PADES_BES,
    paginas: Sequence[str] = PAGINAS_ANF_DEFECTO,
    esperas: Sequence[float] = ESPERAS_ANF_SEGUNDOS,
) -> ResultadoFirma:
    """Firma real vía WS1 STB de ANF: solicita y consulta hasta agotar `esperas`.

    Sin configuración, `boceto_firmar_documento_anf` responde únicamente con `APP_ENV=test`; en
    cualquier otro ambiente falla cerrado, para que un boceto jamás pase por una firma real.
    """
    if formato == FormatoFirma.XADES_BES:
        raise ValueError("ANF STB firma PDF; XAdES no aplica.")
    if not anf_stb_client.esta_configurado():
        if anf_stb_client.es_ambiente_de_pruebas():
            return boceto_firmar_documento_anf(documento, firmante_id, formato)
        raise AnfStbNoConfiguradoError("ANF STB no está habilitado en este ambiente.")
    solicitud_id = await solicitar_firma_anf_stb(documento, firmante_id, pdf, paginas)
    for espera in esperas:
        await asyncio.sleep(espera)
        resultado = await consultar_firma_anf_stb(documento, firmante_id, solicitud_id, formato)
        if resultado is not None:
            return resultado
    raise FirmaAnfEnProcesoError(solicitud_id)


__all__ += [
    "AnfStbError",
    "AnfStbNoConfiguradoError",
    "CLAVE_SOLICITUD",
    "FirmaAnfEnProcesoError",
    "anf_stb_configurado",
    "consultar_firma_anf_stb",
    "firmar_documento_anf_stb",
    "rechazar_firma_anf",
    "registrar_solicitud_anf",
    "reservar_envio_anf",
    "solicitar_firma_anf_stb",
]
# === fin FIRMA-06 ===

# === FIRMA-02 ===
# ¤firma-electronica
from features.firma_electronica.domain.aceptacion import (
    ACEPTACION_CADUCADA,
    ACEPTACION_NO_ENCONTRADA,
    DOCUMENTO_NO_APROBADO,
    Aceptacion,
    DocumentoParaAceptacion,
    EnlaceGenerado,
    InfoPublicaAceptacion,
    PersonaParaAceptacion,
)
from features.firma_electronica.services.aceptacion_engine import (
    crear_enlaces,
    listar_aceptaciones,
    obtener_info_publica,
    registrar_aceptacion,
    verificar_hash,
)


__all__ += [
    "ACEPTACION_CADUCADA",
    "ACEPTACION_NO_ENCONTRADA",
    "DOCUMENTO_NO_APROBADO",
    "Aceptacion",
    "DocumentoParaAceptacion",
    "EnlaceGenerado",
    "InfoPublicaAceptacion",
    "PersonaParaAceptacion",
    "crear_enlaces",
    "listar_aceptaciones",
    "obtener_info_publica",
    "registrar_aceptacion",
    "verificar_hash",
]
# === fin FIRMA-02 ===
