# ¤boveda-cloud
"""Esquemas de entrada y salida de la sala Bóveda Cloud."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EstadoSuscripcion = Literal["ACTIVA", "CUOTA_EXCEDIDA", "SUSPENDIDA"]
TipoConsumo = Literal["almacenamiento", "egress"]


class SolicitudAlta(BaseModel):
    """Alta de una organización en un paquete; las cuotas solo se aceptan (y se exigen) en paquetes personalizados."""

    model_config = ConfigDict(extra="forbid")

    tenant_id: str = Field(min_length=1, max_length=64)
    paquete_codigo: str = Field(min_length=1, max_length=32)
    cuota_almacenamiento_bytes: int | None = Field(default=None, gt=0)
    cuota_egress_mensual_bytes: int | None = Field(default=None, gt=0)


class SuscripcionSalida(BaseModel):
    paquete_codigo: str
    paquete_nombre: str
    cuota_almacenamiento_bytes: int
    uso_almacenamiento_bytes: int
    cuota_egress_mensual_bytes: int
    uso_egress_mensual_bytes: int
    certificaciones_heredadas: list[str]
    estado: EstadoSuscripcion
