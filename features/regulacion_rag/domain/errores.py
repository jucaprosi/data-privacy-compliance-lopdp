# ¤adpa
"""Códigos de error de negocio de la sala regulacion_rag.

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

# === REG-01 ===
# ¤paquete-normativo
NO_ES_OPERADOR = CodigoErrorNegocio(
    "NO_ES_OPERADOR", 403, "Solo el operador de la plataforma edita el paquete normativo."
)
PARAMETRO_NO_VERIFICADO = CodigoErrorNegocio(
    "PARAMETRO_NO_VERIFICADO", 409, "Hay parámetros sin verificar: el paquete no se publica."
)
PAQUETE_NO_BORRADOR = CodigoErrorNegocio(
    "PAQUETE_NO_BORRADOR", 409, "Solo se edita o publica una versión en borrador."
)
UNIDAD_REQUERIDA = CodigoErrorNegocio("UNIDAD_REQUERIDA", 422, "Todo plazo lleva unidad.")
PAQUETE_NO_ENCONTRADO = CodigoErrorNegocio("PAQUETE_NO_ENCONTRADO", 404, "No existe el paquete normativo.")
VERSION_DUPLICADA = CodigoErrorNegocio("VERSION_DUPLICADA", 409, "Esa versión del paquete ya existe.")
VERSION_REQUERIDA = CodigoErrorNegocio("VERSION_REQUERIDA", 422, "Falta la versión.")

CODIGOS_REG01 = {
    c.codigo: c
    for c in (
        NO_ES_OPERADOR,
        PARAMETRO_NO_VERIFICADO,
        PAQUETE_NO_BORRADOR,
        UNIDAD_REQUERIDA,
        PAQUETE_NO_ENCONTRADO,
        VERSION_DUPLICADA,
        VERSION_REQUERIDA,
    )
}
registrar(*CODIGOS_REG01.values())
# === fin REG-01 ===

# === VTX-01 ===
VTX_CACHE_NO_DISPONIBLE = CodigoErrorNegocio(
    codigo="VTX_CACHE_NO_DISPONIBLE",
    status_code=503,
    mensaje_defecto="La caché del corpus normativo no está disponible.",
)
registrar(VTX_CACHE_NO_DISPONIBLE)
# === fin VTX-01 ===
