# ¤adpa
"""Códigos de error de negocio de la sala rat.

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

# === RAT-07 ===
# ¤adpa
TITULAR_IDENTIFICADO = CodigoErrorNegocio(
    codigo="TITULAR_IDENTIFICADO",
    status_code=422,
    mensaje_defecto="Esta plataforma no guarda datos de titulares: solo cantidades por colectivo.",
)
COLECTIVO_NO_ENCONTRADO = CodigoErrorNegocio(
    codigo="COLECTIVO_NO_ENCONTRADO",
    status_code=404,
    mensaje_defecto="El colectivo no existe en la organización.",
)
VALIDACION_CONSENTIMIENTO = CodigoErrorNegocio(
    codigo="VALIDACION_CONSENTIMIENTO",
    status_code=422,
    mensaje_defecto="Los datos del colectivo o del registro no son válidos.",
)
registrar(TITULAR_IDENTIFICADO, COLECTIVO_NO_ENCONTRADO, VALIDACION_CONSENTIMIENTO)
# === fin RAT-07 ===
