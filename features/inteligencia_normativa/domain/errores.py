# ¤inteligencia-normativa ¤vigilancia-spdp ¤adpa
"""Errores de dominio de la sala Inteligencia Normativa (NORM-01)."""

NORMATIVA_ARCHIVO_NO_PDF = "NORMATIVA_ARCHIVO_NO_PDF"
NORMATIVA_ARCHIVO_DEMASIADO_GRANDE = "NORMATIVA_ARCHIVO_DEMASIADO_GRANDE"
NORMATIVA_NUMERO_NO_RECONOCIDO = "NORMATIVA_NUMERO_NO_RECONOCIDO"
NORMATIVA_FUENTE_BLOQUEADA = "NORMATIVA_FUENTE_BLOQUEADA"
NORMATIVA_FUENTE_NO_DISPONIBLE = "NORMATIVA_FUENTE_NO_DISPONIBLE"
NORMATIVA_FUENTE_SIN_CONFIGURAR = "NORMATIVA_FUENTE_SIN_CONFIGURAR"
NORMATIVA_ALMACEN_NO_DISPONIBLE = "NORMATIVA_ALMACEN_NO_DISPONIBLE"
NORMATIVA_RESOLUCION_NO_ENCONTRADA = "NORMATIVA_RESOLUCION_NO_ENCONTRADA"


class ErrorNormativo(Exception):
    """Error de la sala con un código estable; el texto nunca lleva la URL ni datos de la fuente."""

    codigo = "NORMATIVA_ERROR"

    def __init__(self, detalle: str = "") -> None:
        super().__init__(self.codigo)
        self.detalle = detalle


class ArchivoNoPdf(ErrorNormativo):
    codigo = NORMATIVA_ARCHIVO_NO_PDF


class ArchivoDemasiadoGrande(ErrorNormativo):
    codigo = NORMATIVA_ARCHIVO_DEMASIADO_GRANDE


class NumeroNoReconocido(ErrorNormativo):
    codigo = NORMATIVA_NUMERO_NO_RECONOCIDO


class FuenteBloqueada(ErrorNormativo):
    """403, 429 o página de verificación: la corrida se detiene y no se reintenta (R4)."""

    codigo = NORMATIVA_FUENTE_BLOQUEADA


class FuenteNoDisponible(ErrorNormativo):
    """Errores transitorios (5xx, tiempo agotado) que agotaron los reintentos."""

    codigo = NORMATIVA_FUENTE_NO_DISPONIBLE


class FuenteSinConfigurar(ErrorNormativo):
    codigo = NORMATIVA_FUENTE_SIN_CONFIGURAR


class AlmacenNoDisponible(ErrorNormativo):
    codigo = NORMATIVA_ALMACEN_NO_DISPONIBLE


class ResolucionNoEncontrada(ErrorNormativo):
    codigo = NORMATIVA_RESOLUCION_NO_ENCONTRADA
