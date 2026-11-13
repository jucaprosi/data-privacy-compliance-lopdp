# ¤incidentes
"""Compuerta pública de la sala ADPA: Incidentes y vulneraciones (INC-01)."""
from features.incidentes.domain.models import (
    ROLES_CONSULTA,
    ROLES_REGISTRO,
    SEVERIDADES,
    FechaDeteccionFutura,
    Incidente,
)
from features.incidentes.services.bitacora_engine import (
    listar_incidentes,
    primer_incidente_alterado,
    registrar_incidente,
)

__all__ = [
    "ROLES_CONSULTA",
    "ROLES_REGISTRO",
    "SEVERIDADES",
    "FechaDeteccionFutura",
    "Incidente",
    "listar_incidentes",
    "primer_incidente_alterado",
    "registrar_incidente",
]


# === ADPA-05 ===
# ¤adpa Los códigos de error de esta sala viven en features/incidentes/domain/errores.py y se registran al importarlo.
from features.incidentes.domain import errores as _errores_sala  # noqa: E402,F401
# === fin ADPA-05 ===

# === ORG-24 ===
# === fin ORG-24 ===
