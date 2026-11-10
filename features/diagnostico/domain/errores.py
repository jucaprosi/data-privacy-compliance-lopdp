# ¤adpa
"""Códigos de error de negocio de la sala diagnostico.

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

# === DIAG-04 ===
# === fin DIAG-04 ===

# === DIAG-05 ===
# ¤diagnostico-no-aplica
NO_APLICA_SIN_JUSTIFICACION = CodigoErrorNegocio(
    codigo="DIAG_NO_APLICA_SIN_JUSTIFICACION",
    status_code=422,
    mensaje_defecto="Una respuesta «no aplica» necesita una justificación.",
    action_required="justificar_no_aplica",
)
registrar(NO_APLICA_SIN_JUSTIFICACION)
# === fin DIAG-05 ===

# === DIAG-06 ===
# ¤diagnostico-comparativo Un sellado anterior a la escala SMARTCIDI no trae niveles asignados.
COMPARATIVO_ESCALA_ANTERIOR = CodigoErrorNegocio(
    codigo="DIAG_COMPARATIVO_ESCALA_ANTERIOR",
    status_code=409,
    mensaje_defecto="Uno de los diagnósticos se selló con la escala anterior y no se puede comparar.",
    action_required="volver_a_sellar",
)
registrar(COMPARATIVO_ESCALA_ANTERIOR)
# === fin DIAG-06 ===

# === DIAG-07 ===
# === fin DIAG-07 ===

# === DIAG-11 ===
# ¤diagnostico Dos sellos como máximo: el de prueba y el real (línea base).
SELLOS_AGOTADOS = CodigoErrorNegocio(
    codigo="DIAG_SELLOS_AGOTADOS",
    status_code=409,
    mensaje_defecto="El diagnóstico ya tiene sellados el de prueba y el real; no se puede volver a sellar.",
    action_required="consultar_estados",
)
RESPUESTAS_CERRADAS = CodigoErrorNegocio(
    codigo="DIAG_RESPUESTAS_CERRADAS",
    status_code=409,
    mensaje_defecto="El diagnóstico real ya está sellado: las respuestas no se pueden cambiar.",
    action_required="consultar_estados",
)
registrar(SELLOS_AGOTADOS, RESPUESTAS_CERRADAS)
# === fin DIAG-11 ===

# === DIAG-12 ===
# === fin DIAG-12 ===
