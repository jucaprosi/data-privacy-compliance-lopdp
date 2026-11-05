# ¤adpa
# ¤¤developer-architect
"""Códigos de error de negocio de Biblioteca.

Viven en la sala que los lanza y se registran en CATALOGO_ERRORES al importarse; ninguna tarea
escribe en app_core/errors.py. Cada tarea pendiente añade sus códigos solo dentro de su sección.
Los códigos de BIB-105 se quedan en app_core/errors.py.
"""
from app_core.errors import CATALOGO_ERRORES, CodigoErrorNegocio


# ¤adpa
def registrar(*codigos: CodigoErrorNegocio) -> None:
    """Añade los códigos al catálogo común; un código ya registrado distinto es un error de diseño."""
    for codigo in codigos:
        previo = CATALOGO_ERRORES.get(codigo.codigo)
        if previo is not None and previo != codigo:
            raise ValueError(f"Código de error duplicado: {codigo.codigo}")
        CATALOGO_ERRORES[codigo.codigo] = codigo


# === BIB-112 ===
# Infraestructura de esta sala: registrar() y las secciones reservadas de abajo.
# === fin BIB-112 ===

# === BIB-102 ===
registrar(
    CodigoErrorNegocio("BIB_SIN_ACCESO", 403, "No tienes acceso a la Biblioteca de esta organización."),
    CodigoErrorNegocio("BIB_FILTRO_INVALIDO", 422, "El filtro del catálogo no es válido."),
)
# === fin BIB-102 ===

# === BIB-103 ===
registrar(
    CodigoErrorNegocio('BIB_PLANTILLA_NO_ENCONTRADA', 404, 'No se encontró la plantilla.'),
    CodigoErrorNegocio('BIB_COPIA_SOLO_SMARTCIDI', 422,
                       'Solo se copian las plantillas SMARTCIDI; «Mi plantilla» se edita como versión nueva.'),
)
# === fin BIB-103 ===

# === BIB-104 ===
registrar(
    CodigoErrorNegocio("BIB_DESCARGA_DENEGADA", 403, "No tienes permiso para descargar plantillas de esta organización."),
    CodigoErrorNegocio("BIB_PLANTILLA_NO_DESCARGABLE", 422, "Solo se pueden descargar versiones publicadas en formato DOCX o XLSX."),
    CodigoErrorNegocio("BIB_ARCHIVO_NO_DISPONIBLE", 404, "El archivo maestro de esta versión no está disponible para descarga."),
    CodigoErrorNegocio("BIB_TOKEN_DESCARGA_INVALIDO", 401, "El enlace temporal de descarga es inválido o ha caducado."),
)
# === fin BIB-104 ===

# === BIB-106 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-106 ===

# === BIB-107 ===
registrar(
    CodigoErrorNegocio('BIB_DOCUMENTO_NO_ENCONTRADO', 404, 'No se encontró el documento en tu organización.'),
    CodigoErrorNegocio('BIB_PLANTILLA_NO_DISPONIBLE', 404, 'La plantilla no existe o no está publicada.'),
    CodigoErrorNegocio('BIB_DOCUMENTO_REVISION_DESFASADA', 409, 'El documento cambió desde que lo abriste; recárgalo antes de guardar.'),
    CodigoErrorNegocio('BIB_DOCUMENTO_NO_EDITABLE', 409, 'Solo se edita un documento en borrador.'),
    CodigoErrorNegocio('BIB_TAREA_AJENA', 422, 'La tarea de la hoja de ruta no existe en tu organización.'),
)
# === fin BIB-107 ===

# === BIB-201 ===
registrar(
    CodigoErrorNegocio("BIB_BORRADOR_NO_ENCONTRADO", 404, "No se encontró el borrador en tu organización."),
    # BIB_PLANTILLA_NO_DISPONIBLE ya está definido en la sección BIB-107 (mismo código y mismo 404).
    CodigoErrorNegocio("BIB_REVISION_DESFASADA", 409, "El borrador cambió desde que lo abriste; recárgalo antes de guardar."),
    CodigoErrorNegocio("BIB_CONTEXTO_INVALIDO", 422, "Alguna respuesta del formulario no corresponde a esta plantilla."),
    CodigoErrorNegocio("BIB_VARIABLES_FALTANTES", 422, "Completa las variables faltantes antes de pasar a revisión."),
)
# === fin BIB-201 ===

# === BIB-202 ===
registrar(
    CodigoErrorNegocio("BIB_PROCEDENCIA_SIN_INSTANTANEA", 404, "Este documento aún no tiene datos reutilizados emitidos."),
    CodigoErrorNegocio("BIB_PROCEDENCIA_CAMPO_DESCONOCIDO", 422, "Ese dato no existe en las fuentes de tu organización."),
)
# === fin BIB-202 ===

# === BIB-203 ===
registrar(
    CodigoErrorNegocio("BIB_FILA_TABLA_INVALIDA", 422, "Esa tabla no admite captura; PLA se lee del plan."),
    CodigoErrorNegocio("BIB_FILAS_DEMASIADAS", 422, "Se pegan hasta 100 filas por vez."),
    CodigoErrorNegocio("BIB_FILAS_INVALIDAS", 422, "Hay filas con errores; no se guardó ninguna."),
    CodigoErrorNegocio("BIB_FILA_NO_ENCONTRADA", 404, "No se encontró la fila en tu organización."),
    CodigoErrorNegocio("BIB_FILA_REVISION_DESFASADA", 409, "La fila cambió desde que la abriste; recárgala antes de guardar."),
)
# === fin BIB-203 ===

# === BIB-204 ===
registrar(
    CodigoErrorNegocio('BIB_EXCLUSION_EXIGE_JURIDICO', 403, 'Una obligación confirmada exige revisión jurídica para su exclusión.'),
    CodigoErrorNegocio('BIB_MODIFICACION_INVALIDA', 422, 'Una modificación humana conserva motivo, evidencia, autor y fecha.'),
    CodigoErrorNegocio('BIB_REGLA_NO_ENCONTRADA', 404, 'No se encontró la regla de aplicabilidad especificada.'),
)
# === fin BIB-204 ===

# === BIB-205 ===
registrar(
    CodigoErrorNegocio("BIB_GEN_INCOMPLETA", 422, "Para generar para revisión deben estar completos los campos obligatorios y condicionales."),
    CodigoErrorNegocio("BIB_GEN_NO_ENCONTRADA", 404, "No se encontró la generación solicitada."),
    CodigoErrorNegocio("BIB_GEN_SALIDA_INVALIDA", 422, "El documento generado conserva marcas de plantilla sin resolver."),
    CodigoErrorNegocio("BIB_GEN_FORMULA_NO_AUTORIZADA", 422, "La hoja de cálculo solo admite fórmulas autorizadas."),
)
# === fin BIB-205 ===

# === BIB-206 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-206 ===

# === BIB-207 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-207 ===

# === BIB-208 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-208 ===

# === BIB-301 ===
registrar(
    CodigoErrorNegocio("BIB_DOCUMENTO_NO_REVISABLE", 409, "Solo un borrador vigente puede enviarse a revisión."),
    CodigoErrorNegocio("BIB_DOCUMENTO_INCOMPLETO", 422, "Completa las variables pendientes antes de revisar."),
    CodigoErrorNegocio("BIB_SEPARACION_FUNCIONES", 409, "Quien redacta o asigna no puede aprobar esta revisión."),
    CodigoErrorNegocio("BIB_REVISION_NO_ENCONTRADA", 404, "No se encontró la revisión en tu organización."),
    CodigoErrorNegocio("BIB_REVISION_NO_AUTORIZADA", 403, "No estás asignado para realizar esta decisión."),
    CodigoErrorNegocio("BIB_REVISION_DOCUMENTAL_DESFASADA", 409, "La versión fija ya no coincide con el documento."),
    CodigoErrorNegocio("BIB_AUTORIDAD_NO_VIGENTE", 403, "No existe una autoridad de aprobación delegada y vigente."),
)
# === fin BIB-301 ===

# === BIB-302 ===
registrar(
    CodigoErrorNegocio("BIB_ENLACE_ACCION_AJENA", 422, "La acción no existe en tu organización."),
    CodigoErrorNegocio("BIB_ENLACE_REVISION_INVALIDA", 422, "La revisión indicada no existe en este documento."),
    CodigoErrorNegocio("BIB_ENLACE_NO_ENCONTRADO", 404, "No se encontró el enlace documental."),
)
# === fin BIB-302 ===

# === BIB-303 ===
registrar(
    CodigoErrorNegocio("BIB_VERIF_ACCION_AJENA", 422, "La acción no existe en tu organización."),
    CodigoErrorNegocio("BIB_EVIDENCIA_NO_ENCONTRADA", 404, "No se encontró la evidencia de esta acción."),
    CodigoErrorNegocio("BIB_EVIDENCIA_PERMISOS_INVALIDOS", 422, "Indica permisos con roles válidos de la organización."),
    CodigoErrorNegocio("BIB_EVIDENCIA_REVISION_INCOMPLETA", 422, "Indica el documento y su revisión juntos."),
    CodigoErrorNegocio("BIB_VERIF_EVIDENCIA_ILEGIBLE", 422, "Una evidencia ilegible no puede declararse conforme."),
    CodigoErrorNegocio("BIB_VERIF_EFICACIA_PENDIENTE", 422, "Este control exige eficacia conforme antes de aceptar el cierre."),
    CodigoErrorNegocio("BIB_VERIF_REVISOR_AUTOR", 409, "Quien registró la evidencia no puede verificarla."),
    CodigoErrorNegocio("BIB_VERIF_FECHA_FUTURA", 422, "La fecha de verificación no puede ser futura."),
)
# === fin BIB-303 ===

# === BIB-304 ===
registrar(
    CodigoErrorNegocio("BIB_IMPACTO_VERSION_NO_ENCONTRADA", 404, "No se encontró la versión para analizar."),
    CodigoErrorNegocio("BIB_IMPACTO_VERSION_NO_PUBLICADA", 409, "El impacto exige una versión publicada que sustituya otra."),
    CodigoErrorNegocio("BIB_IMPACTO_NO_ENCONTRADO", 404, "No se encontró el impacto en tu organización."),
    CodigoErrorNegocio("BIB_IMPACTO_DECISION_INVALIDA", 422, "Registra una decisión válida y su motivo."),
)
# === fin BIB-304 ===

# === BIB-305 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-305 ===

# === BIB-306 ===
registrar(
    CodigoErrorNegocio("BIB_BLOQUEO_LEGAL_ACTIVO", 409, "El documento tiene un bloqueo legal activo y no puede eliminarse."),
    CodigoErrorNegocio("BIB_RETENCION_ACTIVA", 409, "El plazo de conservación del documento sigue activo."),
    CodigoErrorNegocio("BIB_POLITICA_CONSERVACION_PENDIENTE", 409, "No existe una política de conservación aprobada para eliminar el documento."),
)
# === fin BIB-306 ===

# === BIB-401 ===
# Reservado; códigos a cargo de su ficha (usar registrar()).
# === fin BIB-401 ===

# === BIB-402 ===
registrar(
    CodigoErrorNegocio("VINCULO_REF_INEXISTENTE", 422,
                       "El tratamiento, control o tarea indicado no existe en tu organización."),
)
# === fin BIB-402 ===
