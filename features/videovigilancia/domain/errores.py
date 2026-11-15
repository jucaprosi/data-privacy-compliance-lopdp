# ¤videovigilancia-cctv ¤adpa
"""Errores de dominio de la sala Videovigilancia. Se lanzan como ErrorNegocio con código estable y estado HTTP."""
# === CCTV-01 ===
from app_core.errors import ErrorNegocio

CCTV_AUDIO_AMBIENTAL_PROHIBIDO = "CCTV_AUDIO_AMBIENTAL_PROHIBIDO"
CCTV_CODEC_NO_OPTIMIZADO = "CCTV_CODEC_NO_OPTIMIZADO"
CCTV_CONFIGURACION_NO_CONFORME = "CCTV_CONFIGURACION_NO_CONFORME"
CCTV_ACTIVIDAD_RAT_NO_ENCONTRADA = "CCTV_ACTIVIDAD_RAT_NO_ENCONTRADA"

_ESTADOS = {
    CCTV_AUDIO_AMBIENTAL_PROHIBIDO: (422, "La cámara no puede registrar audio ambiental."),
    CCTV_CODEC_NO_OPTIMIZADO: (422, "La cámara debe grabar en H.265 (o H.265+)."),
    CCTV_CONFIGURACION_NO_CONFORME: (
        422, "La cámara debe grabar solo por eventos de movimiento y con la máscara de privacidad activa."),
    CCTV_ACTIVIDAD_RAT_NO_ENCONTRADA: (404, "La actividad de tratamiento no existe en esta organización."),
}


def error(codigo: str) -> ErrorNegocio:
    """ErrorNegocio con el estado y el texto fijo del código; nunca lleva datos de la organización."""
    estado, texto = _ESTADOS[codigo]
    return ErrorNegocio(codigo, detail=texto, status_code=estado)
# === fin CCTV-01 ===
