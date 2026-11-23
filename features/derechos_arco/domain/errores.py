# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa
"""Códigos de error de negocio de la sala derechos_arco.

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

# === DER-01 ===
# TEXTO PROVISIONAL: los mensajes de interfaz los cierra UX/UI; aquí solo describen el hecho técnico.
registrar(
    CodigoErrorNegocio("IDENTIDAD_NO_VERIFICADA", 409, "Falta verificar la identidad del titular."),
    CodigoErrorNegocio("SOLICITUD_RESPONDIDA", 409, "La solicitud ya fue respondida."),
    CodigoErrorNegocio("VARIABLES_INCOMPLETAS", 422, "El modelo tiene variables sin valor."),
    CodigoErrorNegocio("RESPUESTA_SIN_EVIDENCIA", 422, "La respuesta no quedó custodiada como evidencia."),
    CodigoErrorNegocio("SOLICITUD_NO_ENCONTRADA", 404, "No se encontró la solicitud."),
    CodigoErrorNegocio("MODELO_NO_ENCONTRADO", 404, "No se encontró el modelo de respuesta."),
)
# === fin DER-01 ===

# === DER-02 ===
registrar(
    CodigoErrorNegocio("PORTAL_LIMITE", 429, "Tasa de solicitudes superada. Intente más tarde."),
)
# === fin DER-02 ===
