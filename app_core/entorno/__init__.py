# ¤entorno-pruebas
"""Identidad del entorno (EP-01): única fuente de `APP_ENV` para el resto del backend."""
from app_core.entorno.guardias import (
    ENTORNOS_VALIDOS,
    ENTORNOS_FICTICIOS,
    ErrorArranqueEntorno,
    datos_ficticios,
    entorno_actual,
    validar_arranque,
)

__all__ = [
    "ENTORNOS_VALIDOS",
    "ENTORNOS_FICTICIOS",
    "ErrorArranqueEntorno",
    "datos_ficticios",
    "entorno_actual",
    "validar_arranque",
]
