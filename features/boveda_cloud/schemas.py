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


class SolicitudUrlSubida(BaseModel):
    """BOV-02: lo que declara el cliente antes de subir; el destino lo decide el servidor por `retencion_dias`."""

    model_config = ConfigDict(extra="forbid")

    categoria: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,39}$")
    retencion_dias: int = Field(gt=0, le=36500)
    tamano_bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")


class UrlFirmadaSalida(BaseModel):
    """Solo la URL firmada V4 y lo que el navegador debe enviar: los bytes nunca pasan por la API."""

    objeto_id: str
    url: str
    metodo: Literal["PUT", "GET"]
    cabeceras: dict[str, str]
    caduca_en_segundos: int
    bucket_destino: str | None = None
