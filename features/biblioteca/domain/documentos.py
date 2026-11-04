# ¤adpa
# ¤¤developer-architect
"""Documentos de la organización (BIB-107): contratos, puerto de rellenado y reglas puras."""
import hashlib
import re
from datetime import date, datetime
from typing import Any, Literal, Protocol
from pydantic import BaseModel, ConfigDict, Field

Origen = Literal["plantilla", "propio", "subido"]
Estado = Literal["borrador", "en_revision", "aprobado", "vencido"]
MESES_REVISION = 12
DIAS_POR_VENCER = 30
# Variable `{{ambito.campo}}` o `{{fecha_emision}}`; las etiquetas de bloque (`{{#si …}}`, `{{/si}}`) no empiezan por letra.
_VARIABLE = re.compile(r"\{\{\s*([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)?)\s*\}\}")
_FALTA = re.compile(r"⟦falta: ([a-z][a-z0-9_.]*)⟧")


# ¤adpa
class Contrato(BaseModel):
    # Sin recortar espacios: el contenido se devuelve tal como se guardó y su hash lo sigue acreditando.
    model_config = ConfigDict(extra="forbid")


# ¤adpa
class CrearDocumento(Contrato):
    plantilla_id: str = Field(min_length=1, max_length=36)
    fecha_emision: date | None = None
    contexto: dict[str, Any] = Field(default_factory=dict)
    tarea_hoja_ruta_id: str | None = Field(default=None, min_length=1, max_length=64)


# ¤adpa
class CambiarDocumento(Contrato):
    contenido_markdown: str = Field(min_length=1, max_length=200000)
    revision: int = Field(ge=1)


# ¤adpa
class DocumentoResumen(Contrato):
    id: str
    codigo: str
    nombre: str
    origen: Origen
    plantilla_version: str | None
    estado: Estado
    editado: bool
    proxima_revision: date
    revision: int
    creado_por: str
    creado_en: datetime
    actualizado_en: datetime


# ¤adpa
class Documento(DocumentoResumen):
    plantilla_id: str | None
    contenido_markdown: str
    variables_faltantes: list[str]
    aprobado_por: str | None
    aprobado_en: datetime | None
    sha256: str
    fecha_emision: date
    tarea_hoja_ruta_id: str | None


# ¤adpa
class Pendientes(Contrato):
    borrador: int
    en_revision: int
    por_vencer: int
    vencidos: int
    total: int


# ¤adpa
class EventoHistorial(Contrato):
    revision: int
    accion: Literal["creado", "editado"]
    sha256: str
    actor_id: str
    creado_en: datetime


# ¤adpa
class PuertoRellenado(Protocol):
    """BIB-201 lo implementa. Puede ser síncrono o corrutina: el servicio acepta ambos."""
    def rellenar(self, plantilla: dict, organizacion: dict, contexto: dict) -> tuple[str, list[str]]: ...


# ¤adpa
class RellenadoLiteral:
    """Rellenado por defecto: no resuelve nada; cada variable queda como faltante visible."""
    def rellenar(self, plantilla: dict, organizacion: dict, contexto: dict) -> tuple[str, list[str]]:
        cuerpo = plantilla["cuerpo_md"]
        faltantes = list(dict.fromkeys(_VARIABLE.findall(cuerpo)))
        return _VARIABLE.sub(lambda m: f"⟦falta: {m.group(1)}⟧", cuerpo), faltantes


# ¤adpa
def faltantes_de(contenido: str) -> list[str]:
    """Variables que el borrador todavía muestra como `⟦falta: …⟧`."""
    return list(dict.fromkeys(_FALTA.findall(contenido)))


# ¤adpa
def huella(contenido: str) -> str:
    return hashlib.sha256(contenido.encode("utf-8")).hexdigest()


# ¤adpa
def sumar_meses(base: date, meses: int) -> date:
    indice = base.year * 12 + base.month - 1 + meses
    anio, mes = divmod(indice, 12)
    mes += 1
    siguiente = date(anio + (mes == 12), mes % 12 + 1, 1)
    ultimo = (siguiente - date.resolution).day
    return date(anio, mes, min(base.day, ultimo))


# ¤adpa
def meses_de_revision(metadatos: dict | None) -> int:
    meses = (metadatos or {}).get("revision_meses", MESES_REVISION)
    return meses if isinstance(meses, int) and not isinstance(meses, bool) and 1 <= meses <= 120 else MESES_REVISION


# ¤adpa
def estado_efectivo(estado: str, proxima_revision: date, hoy: date) -> str:
    """`vencido` nunca lo pide un usuario: se calcula al leer un aprobado con la revisión pasada."""
    return "vencido" if estado == "aprobado" and proxima_revision < hoy else estado
