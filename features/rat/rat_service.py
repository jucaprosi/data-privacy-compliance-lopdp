# ¤¤security-engineer
"""Compuerta pública de la sala ADPA: RAT Maestro."""
# === RAT-01 ===
from sqlalchemy.ext.asyncio import AsyncSession

from features.rat.domain.models import ActividadRAT, BaseLegitimacion, CategoriaTitular
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

# === RAT-02 ===
from features.rat.services.plantilla_engine import (  # noqa: E402
    PlantillaNoDisponible,
    aplicar_plantilla as aplicar_plantilla_rat,
    plantillas_disponibles as plantillas_rat_disponibles,
)
# === fin RAT-02 ===

# === RAT-05 ===
from api.errores import ErrorNegocio  # noqa: E402
from features.rat.domain.models import CondicionHabilitante  # noqa: E402,F401
from features.rat.domain.validaciones import RAT_NO_ENCONTRADO, evaluar_reglas  # noqa: E402,F401
from features.rat.services.rat_engine import PostgresRATRepository  # noqa: E402
from features.rat.services.validaciones_engine import validar_ficha  # noqa: E402
from features.rat.services.versiones_engine import leer_version, listar_versiones  # noqa: E402


async def _ficha_existente(session, tenant_id: str, rat_id: str) -> ActividadRAT:
    ficha = await PostgresRATRepository(session).leer_con_bajas(tenant_id, rat_id)
    if ficha is None:
        raise ErrorNegocio(RAT_NO_ENCONTRADO)
    return ficha


async def validaciones_de_ficha(session, tenant_id: str, rat_id: str, user_id: str) -> dict:
    return await validar_ficha(session, await _ficha_existente(session, tenant_id, rat_id), user_id)


async def versiones_de_ficha(session, tenant_id: str, rat_id: str) -> list[dict]:
    await _ficha_existente(session, tenant_id, rat_id)
    return await listar_versiones(session, tenant_id, rat_id)


async def version_de_ficha(session, tenant_id: str, rat_id: str, numero: int) -> dict:
    await _ficha_existente(session, tenant_id, rat_id)
    contenido = await leer_version(session, tenant_id, rat_id, numero)
    if contenido is None:
        raise ErrorNegocio(RAT_NO_ENCONTRADO, detail="La versión pedida no existe para esta ficha.")
    return contenido
# === fin RAT-05 ===
