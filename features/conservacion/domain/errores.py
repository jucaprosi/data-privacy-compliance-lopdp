# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa ¤conservacion
"""Códigos de error de negocio de la sala Conservación y Bloqueo.

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

# === CON-01 ===
from app_core.errors import ErrorNegocio

CONSERVACION_POLITICA_NO_ENCONTRADA = "CONSERVACION_POLITICA_NO_ENCONTRADA"
CONSERVACION_PLAZO_INVALIDO = "CONSERVACION_PLAZO_INVALIDO"
CONSERVACION_YA_EJECUTADA = "CONSERVACION_YA_EJECUTADA"
CONSERVACION_ACTIVIDAD_NO_ENCONTRADA = "CONSERVACION_ACTIVIDAD_NO_ENCONTRADA"

registrar(
    CodigoErrorNegocio("CONSERVACION_POLITICA_NO_ENCONTRADA", 404, "La política de conservación no existe."),
    CodigoErrorNegocio("CONSERVACION_PLAZO_INVALIDO", 422, "El plazo de conservación debe ser de al menos un mes."),
    CodigoErrorNegocio("CONSERVACION_YA_EJECUTADA", 409, "La política ya se ejecutó y su acta no se modifica."),
    CodigoErrorNegocio(
        "CONSERVACION_ACTIVIDAD_NO_ENCONTRADA", 404, "La actividad del registro de tratamientos no existe."
    ),
)


def error(codigo: str) -> ErrorNegocio:
    """ErrorNegocio con el estado y el texto fijo del código; nunca lleva datos de la organización."""
    definicion = CATALOGO_ERRORES[codigo]
    return ErrorNegocio(codigo, detail=definicion.mensaje_defecto, status_code=definicion.status_code)
# === fin CON-01 ===
