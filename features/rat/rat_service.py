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

# === RAT-03 ===
from features.rat.services.eipd_engine import (
    RiesgoEIPD, crear_eipd as _crear_eipd, editar_eipd as _editar_eipd,
    aprobar_eipd as _aprobar_eipd, obtener_eipd as _obtener_eipd,
)
from features.rat.services.mtge_engine import evaluar_deriva_riesgo_eipd


async def obtener_actividad_rat(session, tenant_id: str, rat_id: str):
    actividades = await listar_actividades_rat(session, tenant_id)
    return next((a for a in actividades if a.id == rat_id), None)


async def crear_eipd_rat(session, tenant_id, rat_id, descripcion, riesgos):
    actividad = await obtener_actividad_rat(session, tenant_id, rat_id)
    if actividad is None:
        return None
    return await _crear_eipd(session, tenant_id, rat_id, descripcion,
                             actividad.volumen_titulares_12_meses, riesgos)


async def leer_eipd_rat(session, tenant_id, eipd_id):
    return await _obtener_eipd(session, tenant_id, eipd_id)


async def editar_eipd_rat(session, tenant_id, eipd_id, descripcion):
    return await _editar_eipd(session, tenant_id, eipd_id, descripcion)


async def aprobar_eipd_rat(session, tenant_id, eipd_id, user_id):
    eipd = await _obtener_eipd(session, tenant_id, eipd_id)
    if eipd is None:
        return None
    actividad = await obtener_actividad_rat(session, tenant_id, eipd["rat_id"])
    if actividad is None:
        return None
    return await _aprobar_eipd(session, tenant_id, eipd_id, user_id,
                               actividad.volumen_titulares_12_meses, actividad.categorias_datos)


async def comprobar_deriva_eipd_rat(session, tenant_id, rat_id):
    actividad = await obtener_actividad_rat(session, tenant_id, rat_id)
    if actividad is None:
        return False
    return await evaluar_deriva_riesgo_eipd(
        session, tenant_id, rat_id, actividad.volumen_titulares_12_meses, actividad.categorias_datos,
    )
# === fin RAT-03 ===
