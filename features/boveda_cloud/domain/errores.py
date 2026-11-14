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
