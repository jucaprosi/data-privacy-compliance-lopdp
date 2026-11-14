# ¤dlp-muestreo
"""Esquemas de entrada y salida. La entrada se valida a mano en la ruta para que ningún error devuelva la muestra."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Infotype = Literal["EC_CEDULA_MOD10", "EC_RUC", "EMAIL", "PHONE", "SALUD"]


class SolicitudEscaneo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fuente_nombre: str = Field(min_length=1, max_length=160)
    limite_muestra: int = 250
    filas: list[str]


class SolicitudVinculo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actividad_rat_id: str = Field(min_length=1, max_length=64)
    infotypes: list[Infotype] = Field(min_length=1, max_length=5)


class EscaneoSalida(BaseModel):
    id: str
    fuente_nombre: str
    limite_muestra: int
    filas_evaluadas: int | None = None
    infotypes_detectados: dict[str, int]
    contiene_datos_sensibles: bool
    actividad_rat_id: str | None
    creado_por: str | None
    creado_en: datetime | None
