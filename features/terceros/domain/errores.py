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
