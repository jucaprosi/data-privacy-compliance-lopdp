# ¤adpa
# ¤¤security-engineer
"""Controles de un archivo externo (BIB-106): contenido OOXML real, límites ZIP, macros y enlaces externos.

No interpreta el contenido del documento: solo inspecciona la estructura del paquete. El análisis de
malware es un puerto aparte; sin escáner configurado la carga queda `pendiente` y nunca descargable.
Un doble en pruebas no acredita escaneo operativo.
"""
import io
import re
import zipfile
from typing import Literal, Protocol
from app_core.errors import ErrorNegocio

TAMANO_MAXIMO = 10 * 1024 * 1024
MAX_ENTRADAS = 2000
MAX_DESCOMPRIMIDO = 100 * 1024 * 1024
MAX_RATIO = 100
PARTE_PRINCIPAL = {"DOCX": "word/document.xml", "XLSX": "xl/workbook.xml"}
EXTENSION = {"DOCX": ".docx", "XLSX": ".xlsx"}
# Enlaces externos admitidos: solo hipervínculos navegables. Plantillas adjuntas, OLE, libros vinculados o
# imágenes remotas traen contenido de fuera al abrir el archivo y se rechazan.
_RELACION = re.compile(rb"<Relationship\b[^>]*>", re.I)
_EXTERNO = re.compile(rb'TargetMode\s*=\s*"External"', re.I)
_HIPERVINCULO = re.compile(rb'Type\s*=\s*"[^"]*/relationships/hyperlink"', re.I)
_MACRO_TIPO = re.compile(rb"macroEnabled|vbaProject", re.I)

ResultadoAnalisis = Literal["limpio", "infectado", "error"]


# ¤adpa
class PuertoAnalisis(Protocol):
    """Escáner de malware. Devuelve limpio, infectado o error; nunca se le pide interpretar el documento."""
    def analizar(self, contenido: bytes, nombre: str) -> ResultadoAnalisis: ...


_analizador: PuertoAnalisis | None = None


# ¤adpa
def registrar_analizador(analizador: PuertoAnalisis | None) -> None:
    """El escáner operativo se registra aquí al decidirse el proveedor (decisión pendiente de la ficha)."""
    global _analizador
    _analizador = analizador


# ¤adpa
def analizar(contenido: bytes, nombre: str) -> str:
    """`pendiente` si no hay escáner; `error` si el escáner falla o responde algo desconocido."""
    if _analizador is None:
        return "pendiente"
    try:
        resultado = _analizador.analizar(contenido, nombre)
    except Exception:
        return "error"
    return resultado if resultado in ("limpio", "infectado", "error") else "error"


# ¤adpa
def exigir_extension(nombre_archivo: str, formato: str) -> None:
    if not nombre_archivo.lower().endswith(EXTENSION[formato]):
        raise ErrorNegocio("BIB_CARGA_FORMATO_INVALIDO", f"El archivo debe tener extensión {EXTENSION[formato]}.")


# ¤adpa
def inspeccionar(contenido: bytes, formato: str) -> None:
    """Rechaza lo que no es un paquete OOXML del formato declarado o trae macros o enlaces no autorizados."""
    if not 0 < len(contenido) <= TAMANO_MAXIMO:
        raise ErrorNegocio("BIB_CARGA_TAMANO_INVALIDO")
    try:
        paquete = zipfile.ZipFile(io.BytesIO(contenido))
        entradas = paquete.infolist()
    except (zipfile.BadZipFile, ValueError, OSError):
        raise ErrorNegocio("BIB_CARGA_FORMATO_INVALIDO") from None
    if len(entradas) > MAX_ENTRADAS:
        raise ErrorNegocio("BIB_CARGA_ZIP_PELIGROSO")
    total = 0
    for entrada in entradas:
        nombre = entrada.filename
        if nombre.startswith(("/", "\\")) or ".." in nombre.replace("\\", "/").split("/") or entrada.flag_bits & 0x1:
            raise ErrorNegocio("BIB_CARGA_ZIP_PELIGROSO")
        total += entrada.file_size
        if total > MAX_DESCOMPRIMIDO or entrada.file_size > MAX_RATIO * max(entrada.compress_size, 1):
            raise ErrorNegocio("BIB_CARGA_ZIP_PELIGROSO")
    nombres = {e.filename for e in entradas}
    if "[Content_Types].xml" not in nombres or PARTE_PRINCIPAL[formato] not in nombres:
        raise ErrorNegocio("BIB_CARGA_FORMATO_INVALIDO")
    try:
        tipos = paquete.read("[Content_Types].xml")
        if any(n.lower().endswith(("vbaproject.bin", "vbadata.xml")) for n in nombres) or _MACRO_TIPO.search(tipos):
            raise ErrorNegocio("BIB_CARGA_MACROS")
        for nombre in nombres:
            if not nombre.endswith(".rels"):
                continue
            for relacion in _RELACION.findall(paquete.read(nombre)):
                if _EXTERNO.search(relacion) and not _HIPERVINCULO.search(relacion):
                    raise ErrorNegocio("BIB_CARGA_ENLACE_EXTERNO")
    except (zipfile.BadZipFile, KeyError, OSError, RuntimeError):
        raise ErrorNegocio("BIB_CARGA_FORMATO_INVALIDO") from None
