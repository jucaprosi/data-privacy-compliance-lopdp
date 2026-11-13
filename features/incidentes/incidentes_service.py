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

async def contar_vulneraciones_para_ficha(session, tenant_id: str) -> dict:
    """Total de incidentes registrados del tenant (ficha de la organización, ORG-24).

    La bitácora no tiene columna de estado: la bitácora no tiene estado: se cuentan los incidentes registrados.
    """
    from sqlalchemy import text

    n = (await session.execute(text("SELECT count(*) FROM incidentes WHERE tenant_id = :t"), {"t": tenant_id})).scalar_one()
    return {"vulneraciones_registradas": int(n)}


__all__ += ["contar_vulneraciones_para_ficha"]
# === fin ORG-24 ===

# === INC-03 ===
# === fin INC-03 ===
