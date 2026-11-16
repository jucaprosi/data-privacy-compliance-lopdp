# ¤adpa
"""Códigos de error de negocio de la sala incidentes.

Viven en la sala que los lanza y se registran en CATALOGO_ERRORES al importarse; ninguna tarea
escribe en app_core/errors.py. Cada tarea añade sus códigos solo dentro de su sección reservada.
"""
from app_core.errors import CATALOGO_ERRORES, CodigoErrorNegocio


# === ADPA-05 ===
# ¤adpa
def registrar(*codigos: CodigoErrorNegocio) -> None:
    """Añade los códigos al catálogo común; un código ya registrado distinto es un error de diseño."""
    for codigo in codigos:
        previo = CATALOGO_ERRORES.get(codigo.codigo)
        if previo is not None and previo != codigo:
            raise ValueError(f"Código de error duplicado: {codigo.codigo}")
        CATALOGO_ERRORES[codigo.codigo] = codigo
# === fin ADPA-05 ===

# === INC-02 ===
registrar(
    CodigoErrorNegocio("SECCION_INCOMPLETA", 422, "Completa este paso antes de continuar."),
    CodigoErrorNegocio("DECISION_SIN_JUSTIFICACION", 422, "Explica tu decisión con al menos 20 caracteres."),
    CodigoErrorNegocio("SECCION_ANTERIOR_INCOMPLETA", 409, "Antes de seguir, completa el paso anterior."),
    CodigoErrorNegocio(
        "DECISION_NOTIFICAR_PENDIENTE", 409, "Registra la decisión de notificar antes de cerrar la vulneración."
    ),
    CodigoErrorNegocio("INFORME_NO_PEDIDO", 409, "La decisión registrada no pide este informe."),
    CodigoErrorNegocio("ASISTENTE_CAMBIO_CONCURRENTE", 409, "Otro guardado de este paso se registró al mismo tiempo."),
    CodigoErrorNegocio("EVIDENCIA_NO_CUSTODIADA", 422, "Elige una evidencia ya custodiada por la organización."),
    CodigoErrorNegocio("LECCIONES_NO_DISPONIBLES", 503, "Las lecciones aún no pueden guardarse como hallazgos."),
)
# === fin INC-02 ===

# === INC-03 ===
registrar(
    CodigoErrorNegocio("INCIDENTE_NO_ENCONTRADO", 404, "No se encontró el incidente."),
    CodigoErrorNegocio("INCIDENTE_YA_CERRADO", 409, "El incidente ya está cerrado."),
    CodigoErrorNegocio("INCIDENTE_YA_ABIERTO", 409, "El incidente ya está abierto."),
    CodigoErrorNegocio(
        "INCIDENTE_CAMBIO_CONCURRENTE", 409, "Otro cambio de estado del incidente se registró al mismo tiempo."
    ),
)
# === fin INC-03 ===
