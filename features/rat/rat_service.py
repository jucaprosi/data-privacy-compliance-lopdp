# ¤¤security-engineer
"""Compuerta pública de la sala ADPA: RAT Maestro."""
# === RAT-01 ===
from sqlalchemy.ext.asyncio import AsyncSession

from features.rat.domain.models import ActividadRAT
from features.rat.services.rat_engine import (
    crear_o_actualizar_actividad, obtener_actividades_tenant,
    editar_actividad, eliminar_actividad,
)


# ¤rat
async def registrar_actividad_rat(
    session: AsyncSession, actividad: ActividadRAT, user_id: str | None = None,
) -> ActividadRAT:
    guardada = await crear_o_actualizar_actividad(session, actividad, user_id)
    return guardada


# ¤rat
async def listar_actividades_rat(
    session: AsyncSession, tenant_id: str,
) -> list[ActividadRAT]:
    return await obtener_actividades_tenant(session, tenant_id)


# ¤rat
async def editar_actividad_rat(
    session: AsyncSession, tenant_id: str, rat_id: str, cambios: dict,
    user_id: str | None = None,
) -> ActividadRAT | None:
    actividad = await editar_actividad(session, tenant_id, rat_id, cambios, user_id)
    return actividad


# ¤rat
async def eliminar_actividad_rat(
    session: AsyncSession, tenant_id: str, rat_id: str, user_id: str | None = None,
) -> bool:
    eliminada = await eliminar_actividad(session, tenant_id, rat_id, user_id)
    return eliminada
# === fin RAT-01 ===


# === RAT-02 ===
from features.rat.services.plantilla_engine import (  # noqa: E402
    PlantillaNoDisponible,
    aplicar_plantilla as aplicar_plantilla_rat,
    plantillas_disponibles as plantillas_rat_disponibles,
)
# === fin RAT-02 ===
