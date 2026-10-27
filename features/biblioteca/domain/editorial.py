# ¤adpa
# ¤¤developer-architect
"""Reglas puras de administración editorial; publicación siempre explícita."""
import base64
import binascii
import hashlib
import io
import zipfile
from datetime import date, datetime
from enum import Enum
from typing import Literal
from pydantic import Field
from defusedxml import ElementTree as XML
from defusedxml.common import DefusedXmlException
from xml.etree.ElementTree import ParseError
from api.errores import ErrorNegocio
from features.biblioteca.domain.base import Contrato

MAX_BYTES = 10 * 1024 * 1024


# ¤adpa
class Capacidad(str, Enum):
    EDITOR = "editor"
    TECNICO = "revisor_tecnico"
    JURIDICO = "revisor_juridico"
    PUBLICADOR = "publicador"


# ¤adpa
class Ficha(Contrato):
    nombre: str = Field(min_length=1, max_length=200)
    objetivo: str = Field(min_length=1, max_length=4000)
    fuentes: str = Field(min_length=1, max_length=4000)
    fecha_revision: date
    instrucciones: str = Field(min_length=1, max_length=8000)
    dependencias: str = Field(min_length=1, max_length=4000)
    restricciones: str = Field(min_length=1, max_length=4000)


# ¤adpa
class CrearVersion(Contrato):
    codigo: str = Field(pattern=r"^[A-Z][A-Z0-9-]{1,39}$")
    version: str = Field(max_length=40, pattern=r"^[0-9]+\.[0-9]+(?:\.[0-9]+)?$")
    formato: Literal["DOCX", "XLSX"]
    ficha: Ficha | None = None
    sustituye_id: str | None = Field(default=None, max_length=36)


# ¤adpa
class EditarFicha(Contrato):
    ficha: Ficha
    generacion: int = Field(ge=1)


# ¤adpa
class ArchivoMaestro(Contrato):
    nombre: str = Field(pattern=r"^[^/\\]{1,160}\.(docx|xlsx)$")
    contenido_base64: str = Field(min_length=1, max_length=(MAX_BYTES * 4 // 3 + 4))
    generacion: int = Field(ge=1)


# ¤adpa
class Dictamen(Contrato):
    tipo: Literal["tecnica", "juridica"]
    aprobado: bool
    comentario: str = Field(min_length=1, max_length=4000)
    generacion: int = Field(ge=1)


# ¤adpa
class Transicion(Contrato):
    generacion: int = Field(ge=1)
    motivo: str = Field(min_length=1, max_length=2000)


# ¤adpa
class VersionMaestra(Contrato):
    id: str
    codigo: str
    version: str
    formato: Literal["DOCX", "XLSX"]
    ficha: Ficha | None
    responsable_id: str
    autores: list[str]
    estado: Literal["en_revision", "publicada", "retirada", "sustituida"]
    generacion: int
    nombre_archivo: str | None
    sha256: str | None
    sustituye_id: str | None
    creada_en: datetime


# ¤adpa
class RevisionEditorial(Contrato):
    version_id: str
    generacion: int
    tipo: Literal["tecnica", "juridica"]
    aprobado: bool
    revisor_id: str
    comentario: str
    creada_en: datetime


# ¤adpa
class VistaEditorial(Contrato):
    actor_id: str
    capacidades: list[Capacidad]
    versiones: list[VersionMaestra]
    revisiones: list[RevisionEditorial]


# ¤adpa
class EventoEditorial(Contrato):
    actor_id: str
    alcance: Literal["editorial_global"]
    accion: str
    generacion: int
    motivo: str | None
    creada_en: datetime


# ¤adpa
def validar_archivo(archivo: ArchivoMaestro, formato: str) -> tuple[bytes, str]:
    """Valida contenedor OOXML sin extraer. No acredita antivirus (BIB-106)."""
    try:
        datos = base64.b64decode(archivo.contenido_base64, validate=True)
    except (ValueError, binascii.Error):
        raise ErrorNegocio("BIB_ARCHIVO_INVALIDO") from None
    if not datos or len(datos) > MAX_BYTES:
        raise ErrorNegocio("BIB_ARCHIVO_INVALIDO")
    if not archivo.nombre.lower().endswith("." + formato.lower()):
        raise ErrorNegocio("BIB_ARCHIVO_INVALIDO")
    raiz = "word/document.xml" if formato == "DOCX" else "xl/workbook.xml"
    try:
        with zipfile.ZipFile(io.BytesIO(datos)) as contenedor:
            entradas = contenedor.infolist()
            nombres = [e.filename for e in entradas]
            if (len(entradas) > 2000 or sum(e.file_size for e in entradas) > 50 * 1024 * 1024
                    or len(nombres) != len(set(nombres))
                    or not {"[Content_Types].xml", raiz}.issubset(nombres)
                    or any(e.flag_bits & 1 or e.filename.startswith("/")
                           or ".." in e.filename.split("/") for e in entradas)
                    or any("vbaproject" in n.lower() for n in nombres)):
                raise ErrorNegocio("BIB_ARCHIVO_INVALIDO")
            namespace = ("http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                         if formato == "DOCX" else "http://schemas.openxmlformats.org/spreadsheetml/2006/main")
            etiqueta = "document" if formato == "DOCX" else "workbook"
            tipos = XML.fromstring(contenedor.read("[Content_Types].xml"))
            contenido_xml = XML.fromstring(contenedor.read(raiz))
            mime = ("application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
                    if formato == "DOCX" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml")
            # OPC (ECMA-376-2): el Override de la parte raíz manda; sin él, rige el Default de ".xml".
            declarado = any(e.get("PartName") == "/" + raiz and e.get("ContentType") == mime for e in tipos)
            por_defecto = (not any(e.get("PartName") == "/" + raiz for e in tipos)
                           and any((e.get("Extension") or "").lower() == "xml" and e.get("ContentType") == mime
                                   for e in tipos))
            if (contenido_xml.tag != "{" + namespace + "}" + etiqueta
                    or tipos.tag != "{http://schemas.openxmlformats.org/package/2006/content-types}Types"
                    or not (declarado or por_defecto)):
                raise ErrorNegocio("BIB_ARCHIVO_INVALIDO")
            # CRC y apertura de cada entrada, con tamaño total acotado previamente.
            if contenedor.testzip() is not None:
                raise ErrorNegocio("BIB_ARCHIVO_INVALIDO")
    except (zipfile.BadZipFile, RuntimeError, OSError, ParseError, DefusedXmlException):
        raise ErrorNegocio("BIB_ARCHIVO_INVALIDO") from None
    return datos, hashlib.sha256(datos).hexdigest()


# ¤adpa
def exigir_separacion(actor: str, autores: list[str]) -> None:
    if actor in autores:
        raise ErrorNegocio("BIB_AUTOR_NO_INDEPENDIENTE")


# ¤adpa
def exigir_sustitucion(publicada_id: str | None, sustituye_id: str | None) -> None:
    """Con una versión publicada vigente, solo cabe sustituirla explícitamente."""
    if publicada_id is not None and sustituye_id != publicada_id:
        raise ErrorNegocio("BIB_SUSTITUCION_REQUERIDA")


# ¤adpa
def exigir_publicable(version: dict, revisiones: list[dict], actor: str) -> None:
    exigir_separacion(actor, version["autores"])
    if version["estado"] != "en_revision":
        raise ErrorNegocio("BIB_VERSION_INMUTABLE")
    if not version.get("sha256") or not version.get("responsable_id") or not version.get("ficha"):
        raise ErrorNegocio("BIB_PUBLICACION_INCOMPLETA")
    ficha = Ficha.model_validate(version["ficha"])
    if any(not str(v).strip() for v in ficha.model_dump().values()):
        raise ErrorNegocio("BIB_PUBLICACION_INCOMPLETA")
    aprobadas = {r["tipo"] for r in revisiones
                 if r["aprobado"] and r["generacion"] == version["generacion"]
                 and r["revisor_id"] not in version["autores"]}
    if not {"tecnica", "juridica"}.issubset(aprobadas):
        raise ErrorNegocio("BIB_REVISION_PENDIENTE")
