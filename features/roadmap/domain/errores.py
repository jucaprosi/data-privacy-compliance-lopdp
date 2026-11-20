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

# === RET-02 ===
RM_ALMACEN_NO_DISPONIBLE = CodigoErrorNegocio(
    "RM_ALMACEN_NO_DISPONIBLE",
    503,
    "El almacenamiento de evidencias no está disponible en este entorno.",
)
RM_CLAVE_OBJETO_INVALIDA = CodigoErrorNegocio(
    "RM_CLAVE_OBJETO_INVALIDA",
    403,
    "La clave del objeto no pertenece a la organización activa.",
)
registrar(RM_ALMACEN_NO_DISPONIBLE, RM_CLAVE_OBJETO_INVALIDA)
# === fin RET-02 ===

# === RM-25b ===
ROL_SIN_VALIDACION_FINAL = CodigoErrorNegocio(
    "ROL_SIN_VALIDACION_FINAL",
    403,
    "La validación final de la evidencia corresponde al DPO o al auditor.",
)
PRIMERA_VALIDACION_PENDIENTE = CodigoErrorNegocio(
    "PRIMERA_VALIDACION_PENDIENTE",
    409,
    "La evidencia todavía no tiene la primera validación del coordinador.",
)
VALIDADOR_REPETIDO = CodigoErrorNegocio(
    "VALIDADOR_REPETIDO",
    409,
    "Quien sube la evidencia, quien hace la primera validación y quien hace la final son personas distintas.",
)
registrar(ROL_SIN_VALIDACION_FINAL, PRIMERA_VALIDACION_PENDIENTE, VALIDADOR_REPETIDO)
# === fin RM-25b ===

# === RM-27 ===
# === fin RM-27 ===
