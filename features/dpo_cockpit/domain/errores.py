# ¤adpa
"""Códigos de error de negocio de la sala dpo_cockpit.

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

# === DPO-03 ===
# ¤dpo-cockpit
CONSULTA_CERRADA = CodigoErrorNegocio(
    "CONSULTA_CERRADA", 409, "Esta consulta ya está cerrada. Para otra pregunta, crea una nueva consulta."
)
CONSULTA_NO_ENCONTRADA = CodigoErrorNegocio("CONSULTA_NO_ENCONTRADA", 404, "No se encontró la consulta.")
CONSULTA_INVALIDA = CodigoErrorNegocio("CONSULTA_INVALIDA", 422, "La consulta no es válida.")
CONSULTA_SOLO_DPO_RESPONDE = CodigoErrorNegocio(
    "CONSULTA_SOLO_DPO_RESPONDE", 403, "Solo el DPO puede responder y cerrar consultas."
)
registrar(CONSULTA_CERRADA, CONSULTA_NO_ENCONTRADA, CONSULTA_INVALIDA, CONSULTA_SOLO_DPO_RESPONDE)
# === fin DPO-03 ===
