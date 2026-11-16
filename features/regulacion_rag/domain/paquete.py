# ¤regulation-code
# ¤paquete-normativo
"""Modelos del paquete normativo como dato (REG-01).

Un paquete (LOPDP, NIIF18) tiene versiones; cada versión lleva parámetros (plazos con unidad y
término legal), requisitos y controles comunes. Solo el operador de la plataforma lo edita, y un valor
sin verificar no se publica (R1). La especificación vive en governance/especificaciones/REG-01.md.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

EstadoPaquete = Literal["borrador", "publicado", "retirado"]
UnidadPlazo = Literal["habiles", "calendario"]
TerminoLegal = Literal["plazo", "termino"]

PREFIJO_PLAZO = "plazo_"

CLAVES_MINIMAS: tuple[str, ...] = (
    "plazo_derechos_dias",
    "plazo_vulneracion_encargado_dias",
    "plazo_vulneracion_autoridad_dias",
    "plazo_vulneracion_titulares_dias",
    "autoridad",
    "canal_notificacion",
)


def es_plazo(clave: str) -> bool:
    """R4: toda clave plazo_* lleva unidad."""
    return clave.startswith(PREFIJO_PLAZO)


class Paquete(BaseModel):
    id: str
    codigo: str
    nombre: str
    version: str
    estado: EstadoPaquete
    creado_por: str
    creado_en: datetime
    publicado_por: Optional[str] = None
    publicado_en: Optional[datetime] = None
    retirado_en: Optional[datetime] = None
    sin_verificar: int = 0


class Parametro(BaseModel):
    clave: str
    valor: str
    unidad: Optional[UnidadPlazo] = None
    termino_legal: Optional[TerminoLegal] = None
    articulo: str = ""
    fuente_url: str = ""
    verificado: bool = False
    verificado_por: Optional[str] = None
    verificado_por_nombre: Optional[str] = None
    verificado_en: Optional[datetime] = None
    actualizado_por: str
    actualizado_en: datetime


class ParametroEntrada(BaseModel):
    valor: str = Field(min_length=1, max_length=2000)
    unidad: Optional[UnidadPlazo] = None
    termino_legal: Optional[TerminoLegal] = None
    articulo: str = Field(default="", max_length=2000)
    fuente_url: str = Field(default="", max_length=2000)
    verificado: bool = False


class VersionEntrada(BaseModel):
    version: str = Field(min_length=1, max_length=16)


class Impacto(BaseModel):
    """R3. Lo que aún no se puede medir se dice explícitamente: nunca un impacto nulo falso."""

    plantillas: list[str] = Field(default_factory=list)
    plantillas_pendiente: bool = True
    organizaciones: Optional[int] = None
    organizaciones_pendiente: bool = True


class Publicacion(BaseModel):
    paquete: Paquete
    impacto: Impacto


class DetallePaquete(BaseModel):
    paquete: Paquete
    parametros: list[Parametro]
