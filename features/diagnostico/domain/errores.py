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
# ¤diagnostico-asignacion Quién puede ser encargado de un dominio del assessment.
ENCARGADO_SIN_ROL = CodigoErrorNegocio(
    codigo="ENCARGADO_SIN_ROL",
    status_code=422,
    mensaje_defecto="La persona elegida no tiene un rol vigente en la organización.",
    action_required="elegir_persona_con_rol",
)
ENCARGADO_ES_DPO = CodigoErrorNegocio(
    codigo="ENCARGADO_ES_DPO",
    status_code=422,
    mensaje_defecto="El DPO revisa y sella el diagnóstico, pero no lo responde. Elige a otra persona.",
    action_required="elegir_otra_persona",
)
registrar(ENCARGADO_SIN_ROL, ENCARGADO_ES_DPO)
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
