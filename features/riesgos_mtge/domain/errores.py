# ¤adpa
"""Códigos de error de negocio de la sala riesgos_mtge.

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

# === MTGE-03 ===
# ¤riesgos-eipd
EIPD_OBLIGATORIA = CodigoErrorNegocio(
    "EIPD_OBLIGATORIA", 409, "Este tratamiento exige la evaluación de impacto; no puede marcarse como no obligatoria.")
EIPD_SIN_DECISION = CodigoErrorNegocio(
    "EIPD_SIN_DECISION", 409, "Con riesgo residual alto, elige una decisión antes de cerrar.")
EIPD_PASO_INCOMPLETO = CodigoErrorNegocio(
    "EIPD_PASO_INCOMPLETO", 409, "Completa los pasos 1 a 7 antes de cerrar la evaluación.")
EIPD_CERRADA = CodigoErrorNegocio(
    "EIPD_CERRADA", 409, "La evaluación está cerrada y ya no se puede modificar.")
EIPD_NO_ENCONTRADA = CodigoErrorNegocio(
    "EIPD_NO_ENCONTRADA", 404, "No se encontró la evaluación de impacto.")
EIPD_TRATAMIENTO_NO_ENCONTRADO = CodigoErrorNegocio(
    "EIPD_TRATAMIENTO_NO_ENCONTRADO", 404, "No se encontró el tratamiento en el registro de actividades.")
EIPD_PASO_INVALIDO = CodigoErrorNegocio(
    "EIPD_PASO_INVALIDO", 422, "El paso indicado no existe o su contenido no es válido.")

EIPD_CUSTODIA_NO_DISPONIBLE = CodigoErrorNegocio(
    "EIPD_CUSTODIA_NO_DISPONIBLE", 503, "Aún no se puede custodiar el informe; la evaluación sigue abierta.")

registrar(EIPD_CUSTODIA_NO_DISPONIBLE, EIPD_OBLIGATORIA, EIPD_SIN_DECISION, EIPD_PASO_INCOMPLETO, EIPD_CERRADA, EIPD_NO_ENCONTRADA,
          EIPD_TRATAMIENTO_NO_ENCONTRADO, EIPD_PASO_INVALIDO)
# === fin MTGE-03 ===
