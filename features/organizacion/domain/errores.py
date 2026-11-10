# ¤adpa
"""Códigos de error de negocio de la sala organizacion.

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

# === ORG-15 ===
# === fin ORG-15 ===

# === ORG-17 ===
# ¤inventario
INVENTARIO_NO_ENCONTRADO = CodigoErrorNegocio(
    codigo="INVENTARIO_NO_ENCONTRADO", status_code=404,
    mensaje_defecto="El elemento del inventario no existe en esta organización.", action_required=None,
)
INVENTARIO_DUPLICADO = CodigoErrorNegocio(
    codigo="INVENTARIO_DUPLICADO", status_code=409,
    mensaje_defecto="Ya existe un elemento igual en el inventario.", action_required=None,
)
INVENTARIO_REFERENCIA_INVALIDA = CodigoErrorNegocio(
    codigo="INVENTARIO_REFERENCIA_INVALIDA", status_code=422,
    mensaje_defecto="El área, la persona o el tratamiento indicados no existen en esta organización.",
    action_required=None,
)
INVENTARIO_CEDULA_INVALIDA = CodigoErrorNegocio(
    codigo="INVENTARIO_CEDULA_INVALIDA", status_code=422,
    mensaje_defecto="La cédula no es válida.", action_required=None,
)
INVENTARIO_CIFRADO_NO_CONFIGURADO = CodigoErrorNegocio(
    codigo="INVENTARIO_CIFRADO_NO_CONFIGURADO", status_code=503,
    mensaje_defecto="El servidor no tiene configurada la clave para guardar cédulas cifradas.",
    action_required=None,
)
registrar(
    INVENTARIO_NO_ENCONTRADO, INVENTARIO_DUPLICADO, INVENTARIO_REFERENCIA_INVALIDA,
    INVENTARIO_CEDULA_INVALIDA, INVENTARIO_CIFRADO_NO_CONFIGURADO,
)
# === fin ORG-17 ===

# === ORG-18 ===
# === fin ORG-18 ===

# === ORG-20 ===
# === fin ORG-20 ===
