# ¤adpa
"""Códigos de error de negocio de la sala organizacion.

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

# === ORG-15 ===
# === fin ORG-15 ===

# === ORG-17 ===
# ¤inventario
INVENTARIO_NO_ENCONTRADO = CodigoErrorNegocio(
    codigo="INVENTARIO_NO_ENCONTRADO", status_code=404,
    mensaje_defecto="El elemento del inventario no existe en esta organización.", action_required=None,
)
INVENTARIO_DUPLICADO = CodigoErrorNegocio(
    codigo="INVENTARIO_DUPLICADO", status_code=409,
    mensaje_defecto="Ya existe un elemento igual en el inventario.", action_required=None,
)
INVENTARIO_REFERENCIA_INVALIDA = CodigoErrorNegocio(
    codigo="INVENTARIO_REFERENCIA_INVALIDA", status_code=422,
    mensaje_defecto="El área, la persona o el tratamiento indicados no existen en esta organización.",
    action_required=None,
)
INVENTARIO_CEDULA_INVALIDA = CodigoErrorNegocio(
    codigo="INVENTARIO_CEDULA_INVALIDA", status_code=422,
    mensaje_defecto="La cédula no es válida.", action_required=None,
)
INVENTARIO_CIFRADO_NO_CONFIGURADO = CodigoErrorNegocio(
    codigo="INVENTARIO_CIFRADO_NO_CONFIGURADO", status_code=503,
    mensaje_defecto="El servidor no tiene configurada la clave para guardar cédulas cifradas.",
    action_required=None,
)
registrar(
    INVENTARIO_NO_ENCONTRADO, INVENTARIO_DUPLICADO, INVENTARIO_REFERENCIA_INVALIDA,
    INVENTARIO_CEDULA_INVALIDA, INVENTARIO_CIFRADO_NO_CONFIGURADO,
)
# === fin ORG-17 ===

# === ORG-18 ===
# ¤inventario
SEDE_PRINCIPAL_DUPLICADA = CodigoErrorNegocio(
    codigo="SEDE_PRINCIPAL_DUPLICADA", status_code=409,
    mensaje_defecto="La organización ya tiene una sede principal.", action_required=None,
)
NO_ES_ENCARGADA = CodigoErrorNegocio(
    codigo="NO_ES_ENCARGADA", status_code=409,
    mensaje_defecto="Los clientes solo existen cuando la organización trata datos por encargo.", action_required=None,
)
CONTRATO_NO_ENCONTRADO = CodigoErrorNegocio(
    codigo="CONTRATO_NO_ENCONTRADO", status_code=422,
    mensaje_defecto="El contrato indicado no está registrado como evidencia de la organización.", action_required=None,
)
SEDE_NO_ENCONTRADA = CodigoErrorNegocio(
    codigo="SEDE_NO_ENCONTRADA", status_code=404,
    mensaje_defecto="La sede no existe en esta organización.", action_required=None,
)
CLIENTE_NO_ENCONTRADO = CodigoErrorNegocio(
    codigo="CLIENTE_NO_ENCONTRADO", status_code=404,
    mensaje_defecto="El cliente no existe en esta organización.", action_required=None,
)
CLIENTE_DUPLICADO = CodigoErrorNegocio(
    codigo="CLIENTE_DUPLICADO", status_code=409,
    mensaje_defecto="Ya hay un cliente vigente con ese RUC.", action_required=None,
)
registrar(
    SEDE_PRINCIPAL_DUPLICADA, NO_ES_ENCARGADA, CONTRATO_NO_ENCONTRADO,
    SEDE_NO_ENCONTRADA, CLIENTE_NO_ENCONTRADO, CLIENTE_DUPLICADO,
)
# === fin ORG-18 ===

# === ORG-20 ===
EXPORTACION_EN_CURSO = CodigoErrorNegocio(
    codigo="EXPORTACION_EN_CURSO", status_code=409,
    mensaje_defecto="Ya hay una exportación en preparación.", action_required=None,
)
EXPORTACION_CADUCADA = CodigoErrorNegocio(
    codigo="EXPORTACION_CADUCADA", status_code=410,
    mensaje_defecto="El enlace de la exportación caducó.", action_required=None,
)
EXPORTACION_NO_ENCONTRADA = CodigoErrorNegocio(
    codigo="EXPORTACION_NO_ENCONTRADA", status_code=404,
    mensaje_defecto="La exportación no existe en esta organización.", action_required=None,
)
EXPORTACION_NO_LISTA = CodigoErrorNegocio(
    codigo="EXPORTACION_NO_LISTA", status_code=409,
    mensaje_defecto="La exportación todavía no está lista.", action_required=None,
)
EXPORTACION_INCOMPLETA = CodigoErrorNegocio(
    codigo="EXPORTACION_INCOMPLETA", status_code=409,
    mensaje_defecto="Se requiere una exportación completa y lista de los últimos 30 días para cerrar la organización.",
    action_required=None,
)
ALMACEN_EXPORTACION_NO_DISPONIBLE = CodigoErrorNegocio(
    codigo="ALMACEN_EXPORTACION_NO_DISPONIBLE", status_code=503,
    mensaje_defecto="El almacén de exportaciones no está disponible.", action_required=None,
)
PAPELERA_ENTIDAD_DESCONOCIDA = CodigoErrorNegocio(
    codigo="PAPELERA_ENTIDAD_DESCONOCIDA", status_code=404,
    mensaje_defecto="Ese tipo de elemento no tiene papelera.", action_required=None,
)
PAPELERA_ELEMENTO_NO_ENCONTRADO = CodigoErrorNegocio(
    codigo="PAPELERA_ELEMENTO_NO_ENCONTRADO", status_code=404,
    mensaje_defecto="El elemento no está en la papelera de esta organización.", action_required=None,
)
registrar(
    EXPORTACION_EN_CURSO, EXPORTACION_CADUCADA, EXPORTACION_NO_ENCONTRADA, EXPORTACION_NO_LISTA,
    EXPORTACION_INCOMPLETA, ALMACEN_EXPORTACION_NO_DISPONIBLE, PAPELERA_ENTIDAD_DESCONOCIDA,
    PAPELERA_ELEMENTO_NO_ENCONTRADO,
)
# === fin ORG-20 ===
