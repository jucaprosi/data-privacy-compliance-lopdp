# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa ¤implementacion
"""Códigos de error de negocio de la sala Formación.

Viven en la sala que los lanza y se registran en CATALOGO_ERRORES al importarse; ninguna tarea
escribe en app_core/errors.py. Cada tarea añade sus códigos solo dentro de su sección reservada.
"""
from app_core.errors import CATALOGO_ERRORES, CodigoErrorNegocio

# === ADPA-09 ===
# ¤adpa
def registrar(*codigos: CodigoErrorNegocio) -> None:
    """Añade los códigos al catálogo común; un código ya registrado distinto es un error de diseño."""
    for codigo in codigos:
        previo = CATALOGO_ERRORES.get(codigo.codigo)
        if previo is not None and previo != codigo:
            raise ValueError(f"Código de error duplicado: {codigo.codigo}")
        CATALOGO_ERRORES[codigo.codigo] = codigo
# === fin ADPA-09 ===

# === FOR-01 ===
EXAMEN_YA_RENDIDO = CodigoErrorNegocio(
    codigo="EXAMEN_YA_RENDIDO",
    status_code=409,
    mensaje_defecto="Ya rendiste este examen.",
    action_required=None,
)

EXAMEN_NO_INICIADO = CodigoErrorNegocio(
    codigo="EXAMEN_NO_INICIADO",
    status_code=409,
    mensaje_defecto="Debes iniciar la evaluación antes de enviar tus respuestas.",
    action_required=None,
)

CONTENIDO_SIN_PREGUNTAS = CodigoErrorNegocio(
    codigo="CONTENIDO_SIN_PREGUNTAS",
    status_code=409,
    mensaje_defecto="El contenido formativo no cuenta con preguntas en su banco de evaluación.",
    action_required=None,
)

RESPUESTAS_INCOMPLETAS = CodigoErrorNegocio(
    codigo="RESPUESTAS_INCOMPLETAS",
    status_code=422,
    mensaje_defecto="El número de respuestas no coincide con las preguntas de la evaluación o contiene opciones inválidas.",
    action_required=None,
)

PREGUNTAS_CONGELADAS = CodigoErrorNegocio(
    codigo="PREGUNTAS_CONGELADAS",
    status_code=409,
    mensaje_defecto="El banco de preguntas se encuentra congelado porque ya existen participaciones iniciadas.",
    action_required=None,
)

ACCION_FUERA_DE_FECHAS = CodigoErrorNegocio(
    codigo="ACCION_FUERA_DE_FECHAS",
    status_code=409,
    mensaje_defecto="Esta formación se puede rendir solo dentro de las fechas programadas.",
    action_required=None,
)

PERSONA_NO_VINCULADA = CodigoErrorNegocio(
    codigo="PERSONA_NO_VINCULADA",
    status_code=403,
    mensaje_defecto="Tu correo no está registrado en el inventario de personas. Pide al administrador de tu organización que lo registre.",
    action_required=None,
)

registrar(
    EXAMEN_YA_RENDIDO,
    EXAMEN_NO_INICIADO,
    CONTENIDO_SIN_PREGUNTAS,
    RESPUESTAS_INCOMPLETAS,
    PREGUNTAS_CONGELADAS,
    ACCION_FUERA_DE_FECHAS,
    PERSONA_NO_VINCULADA,
)
# === fin FOR-01 ===
