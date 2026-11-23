# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
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
# === CCTV-02 ===
CCTV_CLIP_PROTEGIDO_POR_HOLD_LEGAL = "CCTV_CLIP_PROTEGIDO_POR_HOLD_LEGAL"
CCTV_CLIP_NO_ENCONTRADO = "CCTV_CLIP_NO_ENCONTRADO"
CCTV_EXPEDIENTE_ORIGEN_INVALIDO = "CCTV_EXPEDIENTE_ORIGEN_INVALIDO"
CCTV_EXPEDIENTE_NO_ENCONTRADO = "CCTV_EXPEDIENTE_NO_ENCONTRADO"
CCTV_ACTA_NO_ENCONTRADA = "CCTV_ACTA_NO_ENCONTRADA"

_ESTADOS.update({
    CCTV_CLIP_PROTEGIDO_POR_HOLD_LEGAL: (
        409,
        "El clip de videovigilancia está bajo Hold Legal y no puede ser destruido (INV_LOPDP_CCTV_LEGAL_HOLD_OVERRIDE).",
    ),
    CCTV_CLIP_NO_ENCONTRADO: (
        404,
        "El clip de videovigilancia no existe en esta organización.",
    ),
    CCTV_EXPEDIENTE_ORIGEN_INVALIDO: (
        422,
        "El tipo de expediente de origen debe ser INCIDENTE o ARCOP.",
    ),
    CCTV_EXPEDIENTE_NO_ENCONTRADO: (
        404,
        "El expediente de origen (incidente o solicitud ARCOP) no existe.",
    ),
    CCTV_ACTA_NO_ENCONTRADA: (
        404,
        "El acta quincenal de destrucción no fue encontrada.",
    ),
})
# === fin CCTV-02 ===
