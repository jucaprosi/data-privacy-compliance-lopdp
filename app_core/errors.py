# ¤adpa
"""Catálogo de errores de negocio para la Plataforma LOPDP 360.

Define los identificadores semánticos y acciones sugeridas para excepciones
de dominio que el cliente REST o frontend debe interpretar sin acoplarse
a mensajes en lenguaje natural sueltos.
"""
from dataclasses import dataclass
from typing import Optional, Union


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


# === FIRMA-06 ===
# ¤firma-electronica
ANF_NO_CONFIGURADO = CodigoErrorNegocio('ANF_NO_CONFIGURADO', 503, 'La firma con ANF no está habilitada en este ambiente.')
ANF_NO_DISPONIBLE = CodigoErrorNegocio('ANF_NO_DISPONIBLE', 502, 'ANF no respondió de forma verificable; intenta de nuevo.')
ANF_RECHAZO = CodigoErrorNegocio('ANF_RECHAZO', 422, 'ANF rechazó la solicitud de firma.')
FIRMA_SESION_NO_ENCONTRADA = CodigoErrorNegocio('FIRMA_SESION_NO_ENCONTRADA', 404, 'La sesión de firma no existe.')
FIRMA_PROVEEDOR_INVALIDO = CodigoErrorNegocio('FIRMA_PROVEEDOR_INVALIDO', 409, 'La sesión no corresponde a una firma de PDF con ANF.')
FIRMA_ESTADO_INVALIDO = CodigoErrorNegocio('FIRMA_ESTADO_INVALIDO', 409, 'El estado de la sesión no admite esta operación.')
FIRMA_DOCUMENTO_INVALIDO = CodigoErrorNegocio('FIRMA_DOCUMENTO_INVALIDO', 422, 'El documento debe ser un PDF en Base64 que coincida con sha256_original.')
CATALOGO_ERRORES.update({
    'ANF_NO_CONFIGURADO': ANF_NO_CONFIGURADO,
    'ANF_NO_DISPONIBLE': ANF_NO_DISPONIBLE,
    'ANF_RECHAZO': ANF_RECHAZO,
    'FIRMA_SESION_NO_ENCONTRADA': FIRMA_SESION_NO_ENCONTRADA,
    'FIRMA_PROVEEDOR_INVALIDO': FIRMA_PROVEEDOR_INVALIDO,
    'FIRMA_ESTADO_INVALIDO': FIRMA_ESTADO_INVALIDO,
    'FIRMA_DOCUMENTO_INVALIDO': FIRMA_DOCUMENTO_INVALIDO,
})
# === fin FIRMA-06 ===


# === RAT-06 ===
RAT_VACIO = CodigoErrorNegocio('RAT_VACIO', 409, 'No hay fichas vigentes que exportar.')
CATALOGO_ERRORES['RAT_VACIO'] = RAT_VACIO
# === fin RAT-06 ===

# --- INICIO SEC-13 ---
LIMITE_PETICIONES = CodigoErrorNegocio(
    'LIMITE_PETICIONES', 429, 'Has superado el número de solicitudes; vuelve a intentarlo más tarde.'
)
LIMITE_NO_DISPONIBLE = CodigoErrorNegocio(
    'LIMITE_NO_DISPONIBLE', 503, 'El servicio de límites no está disponible; vuelve a intentarlo más tarde.'
)
CATALOGO_ERRORES.update({
    'LIMITE_PETICIONES': LIMITE_PETICIONES,
    'LIMITE_NO_DISPONIBLE': LIMITE_NO_DISPONIBLE,
})
# --- FIN SEC-13 ---

# --- INICIO ADPA-02 ---
class ErrorNegocio(Exception):
    """Excepción de negocio tipada con código semántico."""

    def __init__(
        self,
        codigo_o_obj: Union[str, CodigoErrorNegocio],
        detail: Optional[str] = None,
        status_code: Optional[int] = None,
        action_required: Optional[str] = None,
    ):
        if isinstance(codigo_o_obj, CodigoErrorNegocio):
            self.code: str = codigo_o_obj.codigo
            self.status_code: int = status_code or codigo_o_obj.status_code
            self.detail: str = detail or codigo_o_obj.mensaje_defecto
            self.action_required: Optional[str] = (
                action_required if action_required is not None else codigo_o_obj.action_required
            )
        elif isinstance(codigo_o_obj, str):
            self.code = codigo_o_obj
            cat = CATALOGO_ERRORES.get(codigo_o_obj)
            if cat:
                self.status_code = status_code or cat.status_code
                self.detail = detail or cat.mensaje_defecto
                self.action_required = (
                    action_required if action_required is not None else cat.action_required
                )
            else:
                self.status_code = status_code or 400
                self.detail = detail or codigo_o_obj
                self.action_required = action_required
        else:
            raise TypeError("codigo_o_obj debe ser str o CodigoErrorNegocio")

        super().__init__(self.detail)
# --- FIN ADPA-02 ---
