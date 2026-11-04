# ¤adpa
# ¤¤developer-architect
"""Compuerta pública Biblioteca; las demás salas no importan sus internos."""
from features.biblioteca.domain.base import (
    DocumentoEmpresa, EventoDocumento, ObjetoDocumento, PuertoAuditoria,
    PuertoDocumentos, PuertoObjetos, RevisionDocumento,
)
from features.biblioteca.domain.editorial import (
    ArchivoMaestro, Capacidad, CrearVersion, Dictamen, EditarFicha, Ficha, Transicion,
    VersionMaestra, RevisionEditorial, VistaEditorial, EventoEditorial,
    exigir_publicable, exigir_separacion, exigir_sustitucion, validar_archivo,
)
from features.biblioteca.services.editorial import (
    cargar, crear, editar, historial, listar, publicar, retirar, revisar,
)

# === BIB-105 ===
__all__ = ["DocumentoEmpresa", "EventoDocumento", "ObjetoDocumento", "PuertoAuditoria",
           "PuertoDocumentos", "PuertoObjetos", "RevisionDocumento", "ArchivoMaestro", "Capacidad",
           "CrearVersion", "Dictamen", "EditarFicha", "Ficha", "Transicion", "exigir_publicable",
           "exigir_separacion", "exigir_sustitucion", "validar_archivo", "cargar", "crear", "editar", "historial",
           "listar", "publicar", "retirar", "revisar", "VersionMaestra", "RevisionEditorial",
           "VistaEditorial", "EventoEditorial"]
# === fin BIB-105 ===

# === BIB-112 ===
from features.biblioteca.domain import errores  # noqa: F401  registra los códigos de Biblioteca al importarse
# === fin BIB-112 ===

# === BIB-101 ===
# Reservado; implementación a cargo de su ficha.
# === fin BIB-101 ===

# === BIB-102 ===
from features.biblioteca.services.catalogo import PlantillaCatalogo, descargable, listar_catalogo
__all__ += ["PlantillaCatalogo", "descargable", "listar_catalogo"]
# === fin BIB-102 ===

# === BIB-103 ===
from features.biblioteca.services.ficha import obtener_ficha
from features.biblioteca.services.mis_plantillas import crear_copia
__all__ += ["obtener_ficha", "crear_copia"]
# === fin BIB-103 ===

# === BIB-104 ===
from features.biblioteca.services.archivos import (
    ObjetoArchivoMaestro,
    cabeceras_descarga,
    generar_token_descarga,
    nombre_descarga,
    tipo_mime,
    verificar_token_descarga,
)
from features.biblioteca.services.descarga import (
    EnlaceDescarga,
    ejecutar_descarga,
    generar_enlace_descarga,
    registrar_auditoria_descarga,
)

__all__ += [
    "EnlaceDescarga",
    "ObjetoArchivoMaestro",
    "cabeceras_descarga",
    "ejecutar_descarga",
    "generar_enlace_descarga",
    "generar_token_descarga",
    "nombre_descarga",
    "registrar_auditoria_descarga",
    "tipo_mime",
    "verificar_token_descarga",
]
# === fin BIB-104 ===

# === BIB-106 ===
# Reservado; implementación a cargo de su ficha.
# === fin BIB-106 ===

# === BIB-107 ===
from features.biblioteca.domain.documentos import (
    CambiarDocumento, CrearDocumento, Documento, DocumentoResumen, EventoHistorial, Pendientes,
    PuertoRellenado, RellenadoLiteral,
)
from features.biblioteca.services.documentos import cambiar_documento, crear_documento, registrar_rellenador
from features.biblioteca.services.documentos_consulta import (
    historial_documento, listar_documentos, obtener_documento, pendientes,
)
__all__ += ["CambiarDocumento", "CrearDocumento", "Documento", "DocumentoResumen", "EventoHistorial", "Pendientes",
            "PuertoRellenado", "RellenadoLiteral", "cambiar_documento", "crear_documento", "registrar_rellenador",
            "historial_documento", "listar_documentos", "obtener_documento", "pendientes"]
# === fin BIB-107 ===

# === BIB-108 ===
from features.biblioteca.services.importacion import (
    CLAVE_INICIAL, cargar_manifiesto, construir_manifiesto, importar, verificar_manifiesto,
)
__all__ += ["CLAVE_INICIAL", "cargar_manifiesto", "construir_manifiesto", "importar", "verificar_manifiesto"]
# === fin BIB-108 ===

# === BIB-109 ===
from features.biblioteca.domain.editorial import CrearVersionMd, VersionMaestraMd, VistaEditorialMd
from features.biblioteca.domain.plantillas_md import exigir_plantilla_cargable, validar_plantilla_md
from features.biblioteca.services.editorial import crear_version_md
from features.biblioteca.services.plantillas_md import (
    cargar_plantilla_md, cargar_plantillas_pmv, listar_publicadas, verificar_plantillas_pmv,
)
# Con versiones MD en la base, la API editorial de BIB-105 responde con estos contratos ampliados.
VersionMaestra = VersionMaestraMd
VistaEditorial = VistaEditorialMd
__all__ += ["CrearVersionMd", "exigir_plantilla_cargable", "validar_plantilla_md", "crear_version_md",
            "cargar_plantilla_md", "cargar_plantillas_pmv", "listar_publicadas", "verificar_plantillas_pmv"]
# === fin BIB-109 ===

# === BIB-201 ===
from features.biblioteca.domain.esquemas import (
    AvisoActivo, Borrador, CampoContexto, EntradaBorrador, GuardarBorrador, avisos_activos, leer_plantilla,
)
from features.biblioteca.services.borradores import (
    FuentesDatos, crear_borrador, guardar_borrador, obtener_borrador,
)
from features.biblioteca.services.rellenado import fichas_de_actividades, rellenar
from features.biblioteca.services.validacion import es_revisable, exigir_revisable, validar_contexto
# El puerto PuertoRellenado (BIB-107) se cumple con `rellenar(plantilla, organizacion, contexto)`; la línea
# `registrar_rellenador(rellenar)` la añade la ficha que se integre después de las dos.
__all__ += ["AvisoActivo", "Borrador", "CampoContexto", "EntradaBorrador", "GuardarBorrador", "avisos_activos",
            "leer_plantilla", "FuentesDatos", "crear_borrador", "guardar_borrador", "obtener_borrador",
            "fichas_de_actividades", "rellenar", "es_revisable", "exigir_revisable", "validar_contexto"]
# === fin BIB-201 ===

# === BIB-202 ===
from features.biblioteca.domain.procedencia import (
    AvisoCambios, CambioFuente, EntradaPropuesta, Instantanea, OrigenCampo, PropuestaCorreccion, RegistroFuente,
)
from features.biblioteca.services.procedencia import (
    PuertoFuentes, cambios_de_fuente, emitir_instantanea, instantanea_emitida, procedencia_actual,
    proponer_correccion,
)
__all__ += ["AvisoCambios", "CambioFuente", "EntradaPropuesta", "Instantanea", "OrigenCampo", "PropuestaCorreccion",
            "RegistroFuente", "PuertoFuentes", "cambios_de_fuente", "emitir_instantanea", "instantanea_emitida",
            "procedencia_actual", "proponer_correccion"]
# === fin BIB-202 ===

# === BIB-203 ===
from features.biblioteca.services.filas import (
    EditarFila, Fila, FilaPlan, PegarFilas, Previa, PuertoTratamientos, confirmar_filas, editar_fila,
    esquemas as esquemas_filas, filas_del_plan, listar_filas, validar_filas,
)
__all__ += ["EditarFila", "Fila", "FilaPlan", "PegarFilas", "Previa", "PuertoTratamientos", "confirmar_filas",
            "editar_fila", "esquemas_filas", "filas_del_plan", "listar_filas", "validar_filas"]
# === fin BIB-203 ===

# === BIB-204 ===
from features.biblioteca.domain.reglas import (
    EvaluacionPlantilla,
    HechosOrganizacion,
    ModificacionHumana,
    NaturalezaPlantilla,
    ReglaEvaluada,
    ResultadoAplicabilidad,
)
from features.biblioteca.services.aplicabilidad import (
    FuentesAplicabilidad,
    evaluar_aplicabilidad_organizacion,
    extraer_hechos,
    registrar_modificacion_aplicabilidad,
)

__all__ += [
    'EvaluacionPlantilla',
    'HechosOrganizacion',
    'ModificacionHumana',
    'NaturalezaPlantilla',
    'ReglaEvaluada',
    'ResultadoAplicabilidad',
    'FuentesAplicabilidad',
    'evaluar_aplicabilidad_organizacion',
    'extraer_hechos',
    'registrar_modificacion_aplicabilidad',
]
# === fin BIB-204 ===

# === BIB-205 ===
# Reservado; implementación a cargo de su ficha.
# === fin BIB-205 ===

# === BIB-206 ===
# Reservado; implementación a cargo de su ficha.
# === fin BIB-206 ===

# === BIB-207 ===
# Reservado; implementación a cargo de su ficha.
# === fin BIB-207 ===

# === BIB-208 ===
# Reservado; implementación a cargo de su ficha.
# === fin BIB-208 ===

# === BIB-301 ===
from features.biblioteca.domain.revisiones import (
    AprobarRevision, DelegarAutoridad, DictamenRevision, EnviarRevision, RevisionDocumental,
)
from features.biblioteca.services.revision_aprobacion import (
    abrir_nueva_revision, aprobar_revision, delegar_autoridad, devolver_revision, enviar_a_revision, obtener_revision,
)
from features.biblioteca.services.documentos_consulta import contexto as fijar_contexto_revision
__all__ += ["AprobarRevision", "DelegarAutoridad", "DictamenRevision", "EnviarRevision", "RevisionDocumental",
            "abrir_nueva_revision", "aprobar_revision", "delegar_autoridad", "devolver_revision", "enviar_a_revision", "obtener_revision",
            "fijar_contexto_revision"]
# === fin BIB-301 ===

# === BIB-302 ===
from features.biblioteca.services.enlaces import (
    CrearEnlace, EnlaceDocumento, crear_enlace, eliminar_enlace, listar_documentos_de_accion, listar_enlaces,
)
__all__ += ["CrearEnlace", "EnlaceDocumento", "crear_enlace", "eliminar_enlace",
            "listar_documentos_de_accion", "listar_enlaces"]
# === fin BIB-302 ===

# === BIB-303 ===
from features.biblioteca.services.verificacion import (
    Evidencia, ExpedienteVerificacion, RegistrarEvidencia, RegistrarVerificacion, Verificacion,
    VerificadorEvidencia, obtener_expediente, registrar_evidencia, registrar_verificacion,
)
__all__ += ["Evidencia", "ExpedienteVerificacion", "RegistrarEvidencia", "RegistrarVerificacion", "Verificacion",
            "VerificadorEvidencia", "obtener_expediente", "registrar_evidencia", "registrar_verificacion"]
# === fin BIB-303 ===

# === BIB-304 ===
from features.biblioteca.services.impacto import (
    crear_analisis, decidir, listar_organizacion, obtener_analisis, preparar_avisos, registrar_intento,
)
__all__ += ["crear_analisis", "decidir", "listar_organizacion", "obtener_analisis",
            "preparar_avisos", "registrar_intento"]
# === fin BIB-304 ===

# === BIB-305 ===
# Reservado; implementación a cargo de su ficha.
# === fin BIB-305 ===

# === BIB-306 ===
from features.biblioteca.services.conservacion import (
    CambiarConservacion, ConservacionDocumento, cambiar_conservacion, exigir_eliminable, obtener_conservacion,
)
from features.biblioteca.services.historial import (
    EventoCronologia, RegistrarEvento, RestaurarRevision, cronologia, registrar_evento, restaurar_revision,
)
__all__ += ["CambiarConservacion", "ConservacionDocumento", "cambiar_conservacion", "exigir_eliminable",
            "obtener_conservacion", "EventoCronologia", "RegistrarEvento", "RestaurarRevision", "cronologia",
            "registrar_evento", "restaurar_revision"]
# === fin BIB-306 ===

# === BIB-307 ===
# Reservado; implementación a cargo de su ficha.
# === fin BIB-307 ===

# === BIB-401 ===
# Reservado; implementación a cargo de su ficha.
# === fin BIB-401 ===

# === BIB-402 ===
from features.biblioteca.services.vinculos_engine import (
    DocumentoVinculado, EntradaVinculos, PuertoEvidencias, PuertoHallazgos, PuertoReferencias, Vinculo,
    VinculosDocumento, al_aprobar_documento, al_cambiar_tratamiento, documentos_de_tratamiento, es_control,
    listar_vinculos, reemplazar_vinculos,
)
__all__ += ["DocumentoVinculado", "EntradaVinculos", "PuertoEvidencias", "PuertoHallazgos", "PuertoReferencias",
            "Vinculo", "VinculosDocumento", "al_aprobar_documento", "al_cambiar_tratamiento",
            "documentos_de_tratamiento", "es_control", "listar_vinculos", "reemplazar_vinculos"]
# === fin BIB-402 ===
