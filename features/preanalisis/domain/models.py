"""Contrato de dominio de la sala Pre-análisis (pre-llenado asistido, la IA propone y el humano decide)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CONTROL_ID_MIN: int = 1
CONTROL_ID_MAX: int = 80

EstadoPropuesta = Literal["Conforme", "Parcial", "Sin sustento"]
ESTADOS_VALIDOS: tuple[str, ...] = ("Conforme", "Parcial", "Sin sustento")
ESTADO_SIN_SUSTENTO: str = "Sin sustento"

MAX_BYTES_ARCHIVO: int = 25 * 1024 * 1024
MAX_PAGINAS_PDF: int = 300
MAX_BYTES_DOCUMENT_XML: int = 30 * 1024 * 1024
MAX_CARACTERES_TEXTO: int = 2_000_000
MAX_CARACTERES_ENVIO_MODELO: int = 6000
MAX_FRAGMENTOS_ANALISIS: int = 12
MAX_CARACTERES_FRAGMENTO: int = 2000

LIMITACIONES: tuple[str, ...] = (
    "Un documento acredita como máximo que la práctica está documentada (E1); "
    "E2 y E3 requieren evidencia operativa o auditable declarada por el auditor.",
    "El silencio de un documento no implica incumplimiento.",
    "El enmascarado de datos personales es parcial.",
)
ADVERTENCIA_ENMASCARADO: str = (
    "El enmascarado de datos personales es parcial: detecta cédulas, RUC, teléfonos y correos de Ecuador, "
    "pero no todos los nombres propios ni otros datos. Revise el contenido antes de compartirlo."
)


class ErrorPreanalisis(Exception):
    """Base de errores de la sala."""


class FormatoNoSoportado(ErrorPreanalisis):
    """Extensión no analizable (p. ej. imágenes: no hay OCR)."""


class ArchivoDemasiadoGrande(ErrorPreanalisis):
    """El archivo excede el límite de tamaño."""


class DocumentoIlegible(ErrorPreanalisis):
    """El archivo está corrupto, cifrado, vacío o excede límites defensivos."""


class ProveedorNoDisponible(ErrorPreanalisis):
    """No hay proveedor de IA configurado."""


class ProveedorFallo(ErrorPreanalisis):
    """El proveedor de IA falló (detalle interno nunca expuesto)."""


class ControlContexto(BaseModel):
    model_config = ConfigDict(extra="ignore")

    control_id: int = Field(..., ge=CONTROL_ID_MIN, le=CONTROL_ID_MAX)
    control: str = Field("", max_length=500)
    enunciado: str = Field("", max_length=4000)
    evidencia_esperada: str = Field("", max_length=4000)
    referencia_normativa: str = Field("", max_length=1000)


class Fragmento(BaseModel):
    model_config = ConfigDict(extra="ignore")

    texto: str = Field(..., min_length=1, max_length=MAX_CARACTERES_FRAGMENTO)
    origen: str = Field("", max_length=200)


class FragmentoRelevante(BaseModel):
    texto: str
    origen: str
    relevancia: float = Field(..., ge=0.0, le=1.0)


class PreparacionResultado(BaseModel):
    formato: str
    caracteres_totales: int
    fragmentos: list[FragmentoRelevante]
    pii_enmascarada: int
    advertencias: list[str]


class CitaModelo(BaseModel):
    fragmento: str = ""
    motivo: str = ""


class PropuestaModelo(BaseModel):
    """Esquema pedido al modelo; ``estado`` es texto libre para que la validación determinista decida."""

    estado: str = ""
    citas: list[CitaModelo] = Field(default_factory=list)
    razonamiento: str = ""


class Cita(BaseModel):
    fragmento: str
    motivo: str


class PropuestaValidada(BaseModel):
    estado: EstadoPropuesta
    nivel_evidencia_maximo: Literal[0, 1]
    citas: list[Cita]
    citas_descartadas: int
    razonamiento: str
    limitaciones: list[str]
    modelo: str


@dataclass(frozen=True)
class Segmento:
    origen: str
    texto: str


@dataclass(frozen=True)
class ExtraccionResultado:
    formato: str
    segmentos: list[Segmento] = field(default_factory=list)
    caracteres_totales: int = 0
    truncado: bool = False


@dataclass(frozen=True)
class EstadoProveedor:
    disponible: bool
    proveedor: str | None
    modelo: str | None
    motivo: str | None
