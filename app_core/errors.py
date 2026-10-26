# ¤adpa
"""Catálogo de errores de negocio para la Plataforma LOPDP 360.

Define los identificadores semánticos y acciones sugeridas para excepciones
de dominio que el cliente REST o frontend debe interpretar sin acoplarse
a mensajes en lenguaje natural sueltos.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CodigoErrorNegocio:
    codigo: str
    status_code: int
    mensaje_defecto: str
    action_required: Optional[str] = None


# Catálogo estándar de errores de negocio
TENANT_SIZE_NOT_CONFIGURED = CodigoErrorNegocio(
    codigo="TENANT_SIZE_NOT_CONFIGURED",
    status_code=409,
    mensaje_defecto="El tamaño de la organización no está configurado.",
    action_required="configure_tenant_size",
)

SOD_VIOLATION = CodigoErrorNegocio(
    codigo="SOD_VIOLATION",
    status_code=409,
    mensaje_defecto="Violación de segregación de funciones (SoD).",
    action_required=None,
)

DPO_INDEPENDENCE_VIOLATED = CodigoErrorNegocio(
    codigo="DPO_INDEPENDENCE_VIOLATED",
    status_code=409,
    mensaje_defecto="Violación de independencia del Delegado de Protección de Datos (DPO).",
    action_required=None,
)

SELF_VALIDATION_FORBIDDEN = CodigoErrorNegocio(
    codigo="SELF_VALIDATION_FORBIDDEN",
    status_code=403,
    mensaje_defecto="Principio de cuatro ojos: quien sube una evidencia no puede validarla.",
    action_required=None,
)

MEMBER_ALREADY_EXISTS = CodigoErrorNegocio(
    codigo="MEMBER_ALREADY_EXISTS",
    status_code=409,
    mensaje_defecto="El usuario ya posee esta asignación en la organización.",
    action_required=None,
)

LAST_ADMIN_CANNOT_BE_REVOKED = CodigoErrorNegocio(
    codigo="LAST_ADMIN_CANNOT_BE_REVOKED",
    status_code=409,
    mensaje_defecto="No se puede revocar al último administrador de la organización.",
    action_required=None,
)

EVIDENCE_TYPE_NOT_ALLOWED = CodigoErrorNegocio(
    codigo="EVIDENCE_TYPE_NOT_ALLOWED",
    status_code=415,
    mensaje_defecto="El tipo de archivo no está permitido como evidencia.",
    action_required=None,
)

EVIDENCE_TOO_LARGE = CodigoErrorNegocio(
    codigo="EVIDENCE_TOO_LARGE",
    status_code=413,
    mensaje_defecto="El archivo supera el tamaño máximo permitido para evidencia.",
    action_required=None,
)

CATALOGO_ERRORES = {
    "TENANT_SIZE_NOT_CONFIGURED": TENANT_SIZE_NOT_CONFIGURED,
    "SOD_VIOLATION": SOD_VIOLATION,
    "DPO_INDEPENDENCE_VIOLATED": DPO_INDEPENDENCE_VIOLATED,
    "SELF_VALIDATION_FORBIDDEN": SELF_VALIDATION_FORBIDDEN,
    "MEMBER_ALREADY_EXISTS": MEMBER_ALREADY_EXISTS,
    "LAST_ADMIN_CANNOT_BE_REVOKED": LAST_ADMIN_CANNOT_BE_REVOKED,
    "EVIDENCE_TYPE_NOT_ALLOWED": EVIDENCE_TYPE_NOT_ALLOWED,
    "EVIDENCE_TOO_LARGE": EVIDENCE_TOO_LARGE,
}


# === BIB-105 ===
# ¤adpa
# ¤¤developer-architect
BIB_SIN_CAPACIDAD = CodigoErrorNegocio('BIB_SIN_CAPACIDAD', 403, 'No tienes capacidad editorial asignada.')
BIB_AUTOR_NO_INDEPENDIENTE = CodigoErrorNegocio('BIB_AUTOR_NO_INDEPENDIENTE', 403, 'No puedes revisar ni publicar una versión en cuya elaboración participaste.')
BIB_VERSION_INMUTABLE = CodigoErrorNegocio('BIB_VERSION_INMUTABLE', 409, 'Esta versión está cerrada y es inmutable; crea una versión nueva.')
BIB_PUBLICACION_INCOMPLETA = CodigoErrorNegocio('BIB_PUBLICACION_INCOMPLETA', 409, 'Completa archivo, ficha y responsable editorial antes de publicar.')
BIB_REVISION_PENDIENTE = CodigoErrorNegocio('BIB_REVISION_PENDIENTE', 409, 'Falta una revisión técnica o jurídica independiente de la edición actual.')
BIB_NO_ENCONTRADA = CodigoErrorNegocio('BIB_NO_ENCONTRADA', 404, 'No se encontró la versión editorial.')
BIB_CONFLICTO_VERSION = CodigoErrorNegocio('BIB_CONFLICTO_VERSION', 409, 'La versión cambió o el código y versión ya existen; actualiza el listado.')
BIB_ARCHIVO_INVALIDO = CodigoErrorNegocio('BIB_ARCHIVO_INVALIDO', 415, 'El maestro debe ser un DOCX o XLSX válido, sin macros y de hasta 10 MB.')
BIB_SUSTITUCION_REQUERIDA = CodigoErrorNegocio('BIB_SUSTITUCION_REQUERIDA', 409, 'Ya hay una versión publicada de este código; la nueva debe sustituirla expresamente.')
CATALOGO_ERRORES.update({
    'BIB_SIN_CAPACIDAD': BIB_SIN_CAPACIDAD,
    'BIB_AUTOR_NO_INDEPENDIENTE': BIB_AUTOR_NO_INDEPENDIENTE,
    'BIB_VERSION_INMUTABLE': BIB_VERSION_INMUTABLE,
    'BIB_PUBLICACION_INCOMPLETA': BIB_PUBLICACION_INCOMPLETA,
    'BIB_REVISION_PENDIENTE': BIB_REVISION_PENDIENTE,
    'BIB_NO_ENCONTRADA': BIB_NO_ENCONTRADA,
    'BIB_CONFLICTO_VERSION': BIB_CONFLICTO_VERSION,
    'BIB_ARCHIVO_INVALIDO': BIB_ARCHIVO_INVALIDO,
    'BIB_SUSTITUCION_REQUERIDA': BIB_SUSTITUCION_REQUERIDA,
})
# === fin BIB-105 ===
