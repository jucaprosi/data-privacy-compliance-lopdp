# ¤adpa
# ¤¤developer-architect
"""Contratos de la generación de Word y Excel (BIB-205).

La generación parte de una instantánea inmutable: texto íntegro de la plantilla y su huella, esquema de
campos, valores de la organización y del formulario, y la procedencia (opcional hasta que BIB-202 la
rellene). El archivo se calcula solo desde esa instantánea, así que dos generaciones de la misma
instantánea dan los mismos bytes.
"""
import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal
from features.biblioteca.domain.base import Contrato

Modo = Literal["borrador", "revision"]
Formato = Literal["docx", "xlsx"]
ESTADOS = {"borrador": "borrador", "revision": "para_revision"}
MIME = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


# ¤adpa
class PedirGeneracion(Contrato):
    modo: Modo
    formato: Formato


# ¤adpa
class Generacion(Contrato):
    id: str
    borrador_id: str
    modo: Modo
    formato: Formato
    estado: Literal["borrador", "para_revision"]
    plantilla_sha256: str
    instantanea_sha256: str
    archivo_sha256: str
    nombre_archivo: str
    bytes: int
    faltantes: list[str]
    creado_en: datetime


# ¤adpa
class Guia(Contrato):
    """Lo que no va en el documento de uso: instrucciones, ejemplos y fuentes normativas."""
    codigo: str
    guia_markdown: str
    fuentes: str


# ¤adpa
def _serializable(valor: object) -> object:
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    if isinstance(valor, (list, tuple)):
        return [_serializable(v) for v in valor]
    if isinstance(valor, dict):
        return {str(k): _serializable(v) for k, v in valor.items()}
    return getattr(valor, "value", valor)


# ¤adpa
@dataclass(frozen=True)
class InstantaneaGeneracion:
    """Todo lo que decide el contenido del archivo. Se guarda tal cual y se resume en `sha256`."""
    version_id: str
    plantilla_md: str
    plantilla_sha256: str
    esquema: list[dict]
    organizacion: dict
    contexto: dict
    fecha_emision: str
    procedencia: dict | None = field(default=None)

    def como_dict(self) -> dict:
        return {"version_id": self.version_id, "plantilla_md": self.plantilla_md,
                "plantilla_sha256": self.plantilla_sha256, "esquema": self.esquema,
                "organizacion": _serializable(self.organizacion), "contexto": _serializable(self.contexto),
                "fecha_emision": self.fecha_emision, "procedencia": _serializable(self.procedencia)}

    @property
    def sha256(self) -> str:
        canonico = json.dumps(self.como_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonico.encode("utf-8")).hexdigest()

    @classmethod
    def desde_dict(cls, datos: dict) -> "InstantaneaGeneracion":
        return cls(**{k: datos.get(k) for k in ("version_id", "plantilla_md", "plantilla_sha256", "esquema",
                                                "organizacion", "contexto", "fecha_emision", "procedencia")})
