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

CATALOGO_ERRORES = {
    "TENANT_SIZE_NOT_CONFIGURED": TENANT_SIZE_NOT_CONFIGURED,
    "SOD_VIOLATION": SOD_VIOLATION,
    "DPO_INDEPENDENCE_VIOLATED": DPO_INDEPENDENCE_VIOLATED,
    "SELF_VALIDATION_FORBIDDEN": SELF_VALIDATION_FORBIDDEN,
    "MEMBER_ALREADY_EXISTS": MEMBER_ALREADY_EXISTS,
    "LAST_ADMIN_CANNOT_BE_REVOKED": LAST_ADMIN_CANNOT_BE_REVOKED,
}
