# ¤adpa
"""Códigos de error de negocio de la sala terceros.

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

# === TER-01 ===
# ¤hallazgos Contrato y garantía del tercero (especificación TER-01 §2).
EVIDENCIA_NO_ENCONTRADA = CodigoErrorNegocio(
    "EVIDENCIA_NO_ENCONTRADA", 422, "El documento indicado no está custodiado en esta organización."
)
TERCERO_NO_ENCONTRADO = CodigoErrorNegocio("TERCERO_NO_ENCONTRADO", 404, "No se encontró el tercero en tu organización.")
registrar(EVIDENCIA_NO_ENCONTRADA, TERCERO_NO_ENCONTRADO)
# === fin TER-01 ===


# === TER-02 ===
CODIGO_ENLACE_NO_VALIDO = CodigoErrorNegocio(
    "CODIGO_ENLACE_NO_VALIDO", 404, "Este enlace ya no está disponible"
)
DIAS_VIGENCIA_FUERA_DE_RANGO = CodigoErrorNegocio(
    "DIAS_VIGENCIA_FUERA_DE_RANGO", 422, "Elige entre 1 y 30 días de vigencia para el enlace."
)
RESPUESTA_INCOMPLETA = CodigoErrorNegocio(
    "RESPUESTA_INCOMPLETA", 422, "Completa todas las respuestas obligatorias y sus evidencias."
)
CUESTIONARIO_NO_RESPONDIDO = CodigoErrorNegocio(
    "CUESTIONARIO_NO_RESPONDIDO", 409, "El proveedor aún no respondió. Podrás revisarlo cuando envíe sus respuestas."
)
PROXIMA_REVISION_OBLIGATORIA = CodigoErrorNegocio(
    "PROXIMA_REVISION_OBLIGATORIA", 422, "Elige la fecha de la próxima revisión."
)
CUESTIONARIO_NO_ENCONTRADO = CodigoErrorNegocio(
    "CUESTIONARIO_NO_ENCONTRADO", 404, "No se encontró el cuestionario en tu organización."
)
ARCHIVO_DEMASIADO_GRANDE = CodigoErrorNegocio(
    "ARCHIVO_DEMASIADO_GRANDE", 422, "El archivo supera los 10 MB."
)
registrar(
    CODIGO_ENLACE_NO_VALIDO,
    DIAS_VIGENCIA_FUERA_DE_RANGO,
    RESPUESTA_INCOMPLETA,
    CUESTIONARIO_NO_RESPONDIDO,
    PROXIMA_REVISION_OBLIGATORIA,
    CUESTIONARIO_NO_ENCONTRADO,
    ARCHIVO_DEMASIADO_GRANDE,
)
# === fin TER-02 ===
