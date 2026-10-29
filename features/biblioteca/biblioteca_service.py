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

# === BIB-101 ===
# Reservado; implementación a cargo de su ficha.
# === fin BIB-101 ===

# === BIB-102 ===
# Reservado; implementación a cargo de su ficha.
# === fin BIB-102 ===

# === BIB-103 ===
# Reservado; implementación a cargo de su ficha.
# === fin BIB-103 ===

# === BIB-104 ===
# Reservado; implementación a cargo de su ficha.
# === fin BIB-104 ===

# === BIB-106 ===
# Reservado; implementación a cargo de su ficha.
# === fin BIB-106 ===

# === BIB-107 ===
# Reservado; implementación a cargo de su ficha.
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
# Reservado; implementación a cargo de su ficha.
# === fin BIB-201 ===

# === BIB-202 ===
# Reservado; implementación a cargo de su ficha.
# === fin BIB-202 ===

# === BIB-203 ===
# Reservado; implementación a cargo de su ficha.
# === fin BIB-203 ===

# === BIB-204 ===
# Reservado; implementación a cargo de su ficha.
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
# Reservado; implementación a cargo de su ficha.
# === fin BIB-301 ===

# === BIB-302 ===
# Reservado; implementación a cargo de su ficha.
# === fin BIB-302 ===

# === BIB-303 ===
# Reservado; implementación a cargo de su ficha.
# === fin BIB-303 ===

# === BIB-304 ===
# Reservado; implementación a cargo de su ficha.
# === fin BIB-304 ===

# === BIB-305 ===
# Reservado; implementación a cargo de su ficha.
# === fin BIB-305 ===

# === BIB-306 ===
# Reservado; implementación a cargo de su ficha.
# === fin BIB-306 ===

# === BIB-307 ===
# Reservado; implementación a cargo de su ficha.
# === fin BIB-307 ===
