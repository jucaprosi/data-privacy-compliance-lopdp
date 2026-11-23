# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤boveda-cloud ¤adpa
"""Errores de dominio de la sala Bóveda Cloud. Se lanzan como ErrorNegocio con código estable y estado HTTP."""
# === BOV-01 ===
from app_core.errors import ErrorNegocio

BOVEDA_CUOTA_ALMACENAMIENTO_EXCEDIDA = "BOVEDA_CUOTA_ALMACENAMIENTO_EXCEDIDA"
BOVEDA_CUOTA_EGRESS_EXCEDIDA = "BOVEDA_CUOTA_EGRESS_EXCEDIDA"
BOVEDA_SUSCRIPCION_NO_ENCONTRADA = "BOVEDA_SUSCRIPCION_NO_ENCONTRADA"
BOVEDA_SUSCRIPCION_SUSPENDIDA = "BOVEDA_SUSCRIPCION_SUSPENDIDA"
BOVEDA_SUSCRIPCION_YA_EXISTE = "BOVEDA_SUSCRIPCION_YA_EXISTE"
BOVEDA_PAQUETE_NO_ENCONTRADO = "BOVEDA_PAQUETE_NO_ENCONTRADO"
BOVEDA_CUOTA_PERSONALIZADA_REQUERIDA = "BOVEDA_CUOTA_PERSONALIZADA_REQUERIDA"
BOVEDA_ORGANIZACION_NO_ENCONTRADA = "BOVEDA_ORGANIZACION_NO_ENCONTRADA"

_ESTADOS = {
    BOVEDA_CUOTA_ALMACENAMIENTO_EXCEDIDA: (409, "No hay espacio suficiente en el plan para este archivo."),
    BOVEDA_CUOTA_EGRESS_EXCEDIDA: (409, "Se alcanzó el límite de descargas del plan."),
    BOVEDA_SUSCRIPCION_NO_ENCONTRADA: (404, "La organización no tiene un plan de almacenamiento activo."),
    BOVEDA_SUSCRIPCION_SUSPENDIDA: (409, "El servicio de almacenamiento está suspendido."),
    BOVEDA_SUSCRIPCION_YA_EXISTE: (409, "La organización ya tiene un plan de almacenamiento."),
    BOVEDA_PAQUETE_NO_ENCONTRADO: (422, "El paquete no existe en el catálogo."),
    BOVEDA_CUOTA_PERSONALIZADA_REQUERIDA: (422, "El paquete personalizado exige cuotas explícitas."),
    BOVEDA_ORGANIZACION_NO_ENCONTRADA: (404, "La organización no existe."),
}


def error(codigo: str) -> ErrorNegocio:
    """ErrorNegocio con el estado y el texto fijo del código; nunca lleva datos de la organización."""
    estado, texto = _ESTADOS[codigo]
    return ErrorNegocio(codigo, detail=texto, status_code=estado)
# === fin BOV-01 ===

# === BOV-02 ===
BOVEDA_OBJETO_NO_ENCONTRADO = "BOVEDA_OBJETO_NO_ENCONTRADO"
BOVEDA_ALMACEN_NO_DISPONIBLE = "BOVEDA_ALMACEN_NO_DISPONIBLE"
BOVEDA_CLAVE_INVALIDA = "BOVEDA_CLAVE_INVALIDA"

_ESTADOS.update({
    BOVEDA_OBJETO_NO_ENCONTRADO: (404, "El objeto no existe en la bóveda de la organización."),
    BOVEDA_ALMACEN_NO_DISPONIBLE: (503, "El almacenamiento no está disponible por ahora."),
    BOVEDA_CLAVE_INVALIDA: (422, "La categoría o el identificador del objeto no son válidos."),
})
# === fin BOV-02 ===

# --- INICIO BOV-03 ---
BOVEDA_ALTERACION_ORIGINAL_PROHIBIDA = "BOVEDA_ALTERACION_ORIGINAL_PROHIBIDA"
BOVEDA_OBJETO_NO_ENCONTRADO = "BOVEDA_OBJETO_NO_ENCONTRADO"
_ESTADOS[BOVEDA_ALTERACION_ORIGINAL_PROHIBIDA] = (409, "Prohibido alterar o sobrescribir el archivo original intacto con un derivado comprimido.")
_ESTADOS[BOVEDA_OBJETO_NO_ENCONTRADO] = (404, "El objeto bajo custodia no fue encontrado.")
# --- FIN BOV-03 ---

# --- INICIO BOV-04 ---
BOVEDA_METRICA_GLOBAL_PROHIBIDA = "BOVEDA_METRICA_GLOBAL_PROHIBIDA"
BOVEDA_ACTA_SHA256_INVALIDA = "BOVEDA_ACTA_SHA256_INVALIDA"

_ESTADOS[BOVEDA_METRICA_GLOBAL_PROHIBIDA] = (
    422,
    "Prohibido unificar las 10 dimensiones LOPDP en un porcentaje único global.",
)
_ESTADOS[BOVEDA_ACTA_SHA256_INVALIDA] = (
    422,
    "El acta de destrucción requiere un certificado SHA-256 hexadecimal de 64 caracteres.",
)
# --- FIN BOV-04 ---
