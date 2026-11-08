# ¤¤backend-developer
"""Observabilidad de la plataforma (OPS-07) ¤observabilidad: registro JSON sin datos personales."""
from app_core.observabilidad.registro import (
    FormateadorNube,
    configurar_registro,
    fijar_contexto,
    limpiar_contexto,
    registrar_error,
    request_id_actual,
    sanear,
)

__all__ = [
    "FormateadorNube",
    "configurar_registro",
    "fijar_contexto",
    "limpiar_contexto",
    "registrar_error",
    "request_id_actual",
    "sanear",
]
