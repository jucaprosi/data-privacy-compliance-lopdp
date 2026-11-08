# ¤seguridad ¤seguridad-tenant ¤copiloto-ia
"""Límite de peticiones (SEC-13): núcleo compartido, disponible para cualquier sala.

La interfaz pública es `Limitador` (con `LimitadorPostgres` y `LimitadorMemoria`), el catálogo de
políticas y `clave_limite`. Cambiar el almacén (p. ej. a Memorystore) no cambia esta interfaz.
"""
from app_core.limites.limitador import (
    Limitador,
    LimitadorMemoria,
    LimitadorPostgres,
    LimiteNoDisponible,
    Resultado,
    clave_limite,
)
from app_core.limites.politicas import (
    POLITICAS,
    Politica,
    cargar_politicas,
    politicas_de_ruta,
)

__all__ = [
    "Limitador",
    "LimitadorMemoria",
    "LimitadorPostgres",
    "LimiteNoDisponible",
    "Resultado",
    "clave_limite",
    "POLITICAS",
    "Politica",
    "cargar_politicas",
    "politicas_de_ruta",
]
