# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa
"""Códigos de error de negocio de la sala auditoria_capa.

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

# === CAPA-03 ===
# === fin CAPA-03 ===

# === CAPA-04 ===
AUDITOR_EJECUTOR = CodigoErrorNegocio(
    codigo="AUDITOR_EJECUTOR",
    status_code=403,
    mensaje_defecto="No puedes verificar este control porque participaste en su ejecución. Lo verifica otra persona del equipo.",
    action_required=None,
)

AUDITORIA_INCOMPLETA = CodigoErrorNegocio(
    codigo="AUDITORIA_INCOMPLETA",
    status_code=409,
    mensaje_defecto="Aún hay controles de esta área sin verificar. Complétalos antes de firmar el acta.",
    action_required=None,
)

ACTA_YA_FIRMADA = CodigoErrorNegocio(
    codigo="ACTA_YA_FIRMADA",
    status_code=409,
    mensaje_defecto="El acta de esta área ya está firmada.",
    action_required=None,
)

ACCION_NO_CERRADA = CodigoErrorNegocio(
    codigo="ACCION_NO_CERRADA",
    status_code=409,
    mensaje_defecto="La acción vinculada al hallazgo no ha sido completada o no tiene evidencia aprobada.",
    action_required=None,
)

DIAG_SIN_RESULTADO = CodigoErrorNegocio(
    codigo="DIAG_SIN_RESULTADO",
    status_code=404,
    mensaje_defecto="Aún no hay un diagnóstico sellado. Sella el diagnóstico antes de crear una auditoría.",
    action_required=None,
)

ACTA_NO_ENCONTRADA = CodigoErrorNegocio(
    codigo="ACTA_NO_ENCONTRADA",
    status_code=404,
    mensaje_defecto="No encontramos el acta de esta área.",
    action_required=None,
)

registrar(
    AUDITOR_EJECUTOR,
    AUDITORIA_INCOMPLETA,
    ACTA_YA_FIRMADA,
    ACCION_NO_CERRADA,
    DIAG_SIN_RESULTADO,
    ACTA_NO_ENCONTRADA,
)
# === fin CAPA-04 ===
