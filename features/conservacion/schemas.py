# ¤conservacion
"""Contratos de entrada y salida de la sala Conservación y Bloqueo."""
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

AccionVencimiento = Literal["BLOQUEO", "ANONIMIZACION", "SUPRESION"]
EstadoPolitica = Literal["ACTIVA", "BLOQUEADA", "EJECUTADA"]


class PoliticaEntrada(BaseModel):
    """`plazo_meses` se valida en el servicio (CONSERVACION_PLAZO_INVALIDO), no aquí, para dar el código estable."""

    actividad_rat_id: str = Field(min_length=1, max_length=64)
    plazo_meses: int
    accion_vencimiento: AccionVencimiento
    fecha_proxima_revision: Optional[date] = None


class PoliticaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actividad_rat_id: str
    plazo_meses: int
    accion_vencimiento: AccionVencimiento
    fecha_proxima_revision: date
    estado: EstadoPolitica
    acta_ejecucion_hash: Optional[str] = None
    creado_en: Optional[datetime] = None
    vencida: bool = False
