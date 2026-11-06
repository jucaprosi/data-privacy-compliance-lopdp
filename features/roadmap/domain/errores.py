# ¤adpa ¤roadmap
"""Códigos de error de negocio de la Hoja de Ruta.

Viven en la sala que los lanza y se registran en CATALOGO_ERRORES al importarse.
Este archivo lo creó FE-26 solo con su sección; ADPA-05 añadirá a su alrededor el andamiaje común
de la sala (su `registrar()` y las secciones reservadas). Cada tarea escribe solo en su sección.
"""
from app_core.errors import CATALOGO_ERRORES, CodigoErrorNegocio

# === FE-26 ===
RM_EVIDENCIA_NO_DISPONIBLE = CodigoErrorNegocio(
    "RM_EVIDENCIA_NO_DISPONIBLE",
    409,
    "Esta plataforma no guarda archivos de evidencia: la evidencia del diagnóstico es declarada por el DPO.",
)
_previo = CATALOGO_ERRORES.get(RM_EVIDENCIA_NO_DISPONIBLE.codigo)
if _previo is not None and _previo != RM_EVIDENCIA_NO_DISPONIBLE:
    raise ValueError(f"Código de error duplicado: {RM_EVIDENCIA_NO_DISPONIBLE.codigo}")
CATALOGO_ERRORES[RM_EVIDENCIA_NO_DISPONIBLE.codigo] = RM_EVIDENCIA_NO_DISPONIBLE
# === fin FE-26 ===
