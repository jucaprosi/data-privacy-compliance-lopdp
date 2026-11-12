# ¤adpa
"""Códigos de error de negocio de la sala evidencias.

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

# === EVI-01 ===
# ¤evidencias Documentos guardados y comprobados por el servidor.
ALMACEN_NO_DISPONIBLE = CodigoErrorNegocio(
    codigo="EVI_ALMACEN_NO_DISPONIBLE",
    status_code=503,
    mensaje_defecto="El almacén de documentos no está disponible en este entorno.",
)
CLAVE_NO_ENCONTRADA = CodigoErrorNegocio(
    codigo="EVI_CLAVE_NO_ENCONTRADA",
    status_code=404,
    mensaje_defecto="No hay un archivo subido para esa clave en tu organización.",
)
ARCHIVO_INVALIDO = CodigoErrorNegocio(
    codigo="EVI_ARCHIVO_INVALIDO",
    status_code=422,
    mensaje_defecto="El archivo subido no coincide con lo declarado (tamaño o formato).",
)
HUELLA_NO_COINCIDE = CodigoErrorNegocio(
    codigo="EVI_HUELLA_NO_COINCIDE",
    status_code=422,
    mensaje_defecto="La huella que calculó el navegador no coincide con la del archivo guardado.",
)
RETENCION_NO_FIJADA = CodigoErrorNegocio(
    codigo="EVI_RETENCION_NO_FIJADA",
    status_code=502,
    mensaje_defecto="No se pudo fijar la retención del archivo; el documento no se registró.",
)
SIN_PERMISO_PARA_SUBIR = CodigoErrorNegocio(
    codigo="EVI_SIN_PERMISO_PARA_SUBIR",
    status_code=403,
    mensaje_defecto="Tu rol no puede subir documentos en esta etapa del diagnóstico.",
)
SIN_PERMISO_PARA_VINCULAR = CodigoErrorNegocio(
    codigo="EVI_SIN_PERMISO_PARA_VINCULAR",
    status_code=403,
    mensaje_defecto="Solo el DPO vincula documentos a controles antes del diagnóstico real.",
)
VINCULOS_CERRADOS = CodigoErrorNegocio(
    codigo="EVI_VINCULOS_CERRADOS",
    status_code=409,
    mensaje_defecto="El diagnóstico real ya está sellado: los vínculos no se pueden cambiar.",
)
DOCUMENTO_NO_ENCONTRADO = CodigoErrorNegocio(
    codigo="EVI_DOCUMENTO_NO_ENCONTRADO",
    status_code=404,
    mensaje_defecto="El documento no existe en tu organización.",
)
registrar(
    ALMACEN_NO_DISPONIBLE, CLAVE_NO_ENCONTRADA, ARCHIVO_INVALIDO, HUELLA_NO_COINCIDE, RETENCION_NO_FIJADA,
    SIN_PERMISO_PARA_SUBIR, SIN_PERMISO_PARA_VINCULAR, VINCULOS_CERRADOS, DOCUMENTO_NO_ENCONTRADO,
)
# === fin EVI-01 ===

# === EVI-02 ===
# ¤evidencias-vigencia Vigencia, visibilidad y paquete para inspección.
VISIBILIDAD_INVALIDA = CodigoErrorNegocio(
    codigo="EVI_VISIBILIDAD_INVALIDA",
    status_code=422,
    mensaje_defecto="La visibilidad solo admite roles que consultan evidencias.",
)
SIN_PERMISO_PARA_ATRIBUTOS = CodigoErrorNegocio(
    codigo="EVI_SIN_PERMISO_PARA_ATRIBUTOS",
    status_code=403,
    mensaje_defecto="Solo el DPO define la vigencia y la visibilidad de un documento.",
)
SIN_VISIBILIDAD = CodigoErrorNegocio(
    codigo="EVI_SIN_VISIBILIDAD",
    status_code=403,
    mensaje_defecto="Tu rol no tiene visibilidad sobre este documento.",
)
PAQUETE_VACIO = CodigoErrorNegocio(
    codigo="EVI_PAQUETE_VACIO",
    status_code=409,
    mensaje_defecto="No hay documentos vigentes y visibles para tu rol que incluir en el paquete.",
)
PAQUETE_DEMASIADO_GRANDE = CodigoErrorNegocio(
    codigo="EVI_PAQUETE_DEMASIADO_GRANDE",
    status_code=413,
    mensaje_defecto="El paquete supera el tamaño máximo; descárgalo por partes.",
)
PAQUETE_INTEGRIDAD = CodigoErrorNegocio(
    codigo="EVI_PAQUETE_INTEGRIDAD",
    status_code=502,
    mensaje_defecto="Un documento del almacén no coincide con su huella registrada; el paquete no se generó.",
)
registrar(
    VISIBILIDAD_INVALIDA, SIN_PERMISO_PARA_ATRIBUTOS, SIN_VISIBILIDAD, PAQUETE_VACIO, PAQUETE_DEMASIADO_GRANDE,
    PAQUETE_INTEGRIDAD,
)
# === fin EVI-02 ===
