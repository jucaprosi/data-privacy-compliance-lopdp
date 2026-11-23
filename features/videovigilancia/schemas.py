# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤videovigilancia-cctv
"""Esquemas de entrada y salida de la sala Videovigilancia."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SolicitudCamara(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre_ubicacion: str = Field(min_length=1, max_length=160)
    codec: str = Field(min_length=1, max_length=16)
    modo_grabacion: str = Field(min_length=1, max_length=32)
    audio_ambiental_activo: bool = False
    mascara_privacidad_activa: bool = True
    plazo_retencion_dias: int = Field(default=15, ge=1, le=30)
    actividad_rat_id: str | None = Field(default=None, min_length=1, max_length=64)


class CamaraSalida(BaseModel):
    id: str
    nombre_ubicacion: str
    codec: str
    modo_grabacion: str
    audio_ambiental_activo: bool
    mascara_privacidad_activa: bool
    plazo_retencion_dias: int
    estado_conformidad: str
    actividad_rat_id: str | None = None
    bucket_destino: str
    creado_en: datetime | None = None
