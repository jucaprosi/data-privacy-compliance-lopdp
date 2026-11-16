# ¤inteligencia-normativa ¤adpa
"""Contratos tipados de la compuerta de Inteligencia Normativa (NORM-01)."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

Seccion = Literal["resoluciones", "marco_normativo", "consultas_absueltas"]
EstadoResolucion = Literal["pendiente_revision", "homologada", "observada", "vigente", "reformada", "derogada"]
Origen = Literal["programado", "manual"]
EstadoCorrida = Literal["ok", "parcial", "fallida"]


class ResumenCorrida(BaseModel):
    id: str
    origen: Origen
    estado: EstadoCorrida
    inicio: datetime
    fin: datetime
    documentos_vistos: int = 0
    nuevos: int = 0
    versiones_nuevas: int = 0
    errores: int = 0
    codigos_error: list[str] = Field(default_factory=list)


class FiltrosResoluciones(BaseModel):
    estado: Optional[EstadoResolucion] = None
    seccion: Optional[Seccion] = None
    anio: Optional[int] = Field(default=None, ge=1990, le=2100)
    limite: int = Field(default=50, ge=1, le=200)


class ResolucionResumen(BaseModel):
    id: str
    numero_resolucion: str
    anio_emision: int
    titulo: str
    seccion_fuente: Seccion
    estado: EstadoResolucion
    archivo_sha256: str
    detectada_en: datetime


class VersionResolucion(BaseModel):
    id: str
    archivo_sha256: str
    ruta_original: str
    detectada_en: datetime
    motivo: Literal["republicacion", "fe_de_erratas", "cambio_en_fuente"]


class ResolucionDetalle(ResolucionResumen):
    organo_emisor: Optional[str] = None
    materia: Optional[str] = None
    fecha_publicacion: Optional[date] = None
    url_fuente: str
    ruta_original: str
    tamano_bytes: int
    revisada_por: Optional[str] = None
    revisada_en: Optional[datetime] = None
    versiones: list[VersionResolucion] = Field(default_factory=list)
