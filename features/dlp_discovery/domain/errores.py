# ¤dlp-muestreo
# === DLP-01 ===
"""Errores de la sala. Ningún mensaje lleva valores de la muestra: solo códigos y números de control."""


class ErrorDlp(Exception):
    codigo = "DLP_ERROR"
    estado_http = 400
    mensaje = "No se pudo escanear la muestra."

    def __init__(self, mensaje: str | None = None) -> None:
        super().__init__(mensaje or self.mensaje)
        self.detalle = mensaje or self.mensaje


class MuestraExcedeLimite(ErrorDlp):
    codigo = "DLP_MUESTRA_EXCEDE_LIMITE"
    estado_http = 422
    mensaje = "La muestra supera el máximo de filas permitido."


class InfotypeNoPermitido(ErrorDlp):
    codigo = "DLP_INFOTYPE_NO_PERMITIDO"
    estado_http = 422
    mensaje = "El servicio devolvió un tipo de dato fuera de la lista permitida."


class EscaneoNoEncontrado(ErrorDlp):
    codigo = "DLP_ESCANEO_NO_ENCONTRADO"
    estado_http = 404
    mensaje = "El escaneo no existe en esta organización."


class ActividadRatNoEncontrada(ErrorDlp):
    codigo = "DLP_ACTIVIDAD_RAT_NO_ENCONTRADA"
    estado_http = 404
    mensaje = "La actividad de tratamiento no existe en esta organización."


class CategoriaNoDetectada(ErrorDlp):
    codigo = "DLP_CATEGORIA_NO_DETECTADA"
    estado_http = 422
    mensaje = "Solo se pueden vincular tipos de datos encontrados en el escaneo."


class AdaptadorDlpDesactivado(ErrorDlp):
    """Falla cerrada: sin el brief del propietario y la confirmación del CTO no sale nada hacia Cloud DLP."""

    codigo = "DLP_ADAPTADOR_DESACTIVADO"
    estado_http = 503
    mensaje = "El servicio de descubrimiento no está habilitado para esta organización."
# === fin DLP-01 ===
