# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
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
from app_core.errors import ErrorNegocio  # noqa: E402
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

# === RAT-06 ===
from features.rat.services.exportacion_engine import exportar_rat as exportar_rat_vigente  # noqa: E402,F401
# === fin RAT-06 ===

# === BIB-208 ===
from dataclasses import asdict as _asdict  # noqa: E402


async def actividades_para_biblioteca(session: AsyncSession, tenant_id: str) -> list[dict]:
    """Lectura de las actividades del tenant para anclar RAT-01 en Biblioteca; no escribe en el RAT."""
    return [_asdict(a) for a in await obtener_actividades_tenant(session, tenant_id)]
# === fin BIB-208 ===


# === ADPA-05 ===
# ¤adpa Los códigos de error de esta sala viven en features/rat/domain/errores.py y se registran al importarlo.
from features.rat.domain import errores as _errores_sala  # noqa: E402,F401
# === fin ADPA-05 ===


# === RAT-07 ===
from pydantic import ValidationError as _ValidationError  # noqa: E402

from features.rat.domain.consentimiento import (  # noqa: E402
    ColectivoEntrada, RegistroEntrada, campos_identificadores_presentes,
)
from features.rat.domain.errores import (
    COLECTIVO_NO_ENCONTRADO, TITULAR_IDENTIFICADO, VALIDACION_CONSENTIMIENTO,
)  # noqa: E402
from features.rat.services import consentimientos_engine as _consentimientos  # noqa: E402


def _validar_entrada(modelo, cuerpo: dict):
    """R1: un campo de identidad o ajeno al modelo es TITULAR_IDENTIFICADO; el resto, errores por campo."""
    propios = set(modelo.model_fields)
    if campos_identificadores_presentes(cuerpo) or set(cuerpo) - propios:
        raise ErrorNegocio(TITULAR_IDENTIFICADO)
    try:
        return modelo.model_validate(cuerpo)
    except _ValidationError as exc:
        raise ErrorNegocio(
            VALIDACION_CONSENTIMIENTO,
            detail="; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors()),
        ) from exc


async def _colectivo_existente(session, tenant_id: str, colectivo_id: str) -> dict:
    colectivo = await _consentimientos.leer_colectivo(session, tenant_id, colectivo_id)
    if colectivo is None:
        raise ErrorNegocio(COLECTIVO_NO_ENCONTRADO)
    return colectivo


async def listar_colectivos_rat(session, tenant_id: str, rat_id: str) -> list[dict]:
    await _ficha_existente(session, tenant_id, rat_id)
    return await _consentimientos.listar_colectivos(session, tenant_id, rat_id)


async def crear_colectivo_rat(session, tenant_id: str, rat_id: str, cuerpo: dict, user_id: str | None) -> dict:
    datos = _validar_entrada(ColectivoEntrada, cuerpo)
    await _ficha_existente(session, tenant_id, rat_id)
    return await _consentimientos.crear_colectivo(
        session, tenant_id, rat_id, datos.model_dump(mode="json"), user_id)


async def editar_colectivo_rat(session, tenant_id: str, colectivo_id: str, cuerpo: dict) -> dict:
    datos = _validar_entrada(ColectivoEntrada, cuerpo)
    await _colectivo_existente(session, tenant_id, colectivo_id)
    return await _consentimientos.actualizar_colectivo(
        session, tenant_id, colectivo_id, datos.model_dump(mode="json"))


async def registrar_consentimiento_rat(session, tenant_id: str, colectivo_id: str, cuerpo: dict,
                                       user_id: str | None) -> dict:
    datos = _validar_entrada(RegistroEntrada, cuerpo)
    await _colectivo_existente(session, tenant_id, colectivo_id)
    return await _consentimientos.registrar_consentimiento(
        session, tenant_id, colectivo_id, datos.model_dump(), user_id)


async def consentimientos_de_colectivo(session, tenant_id: str, colectivo_id: str, desde=None, hasta=None) -> dict:
    await _colectivo_existente(session, tenant_id, colectivo_id)
    return await _consentimientos.listar_registros(session, tenant_id, colectivo_id, desde, hasta)
# === fin RAT-07 ===

# === RAT-08 ===
async def resolver_area_responsable_viva(
    session: AsyncSession, tenant_id: str, area_id: str | None, area_responsable_respaldo: str,
) -> str:
    """Resuelve el nombre actual del área viva si area_id está definida; en su defecto devuelve el texto de respaldo."""
    if not area_id:
        return area_responsable_respaldo
    from app_core.pasillo.organizacion import area_del_tenant
    area = await area_del_tenant(session, tenant_id, area_id)
    return area["nombre"] if area else area_responsable_respaldo


async def validar_area_o_resolver_nombre(
    session: AsyncSession, tenant_id: str, area_id: str
) -> str | None:
    """Valida que el area_id pertenezca al tenant y retorna su nombre, o None si no existe o fue borrada."""
    from app_core.pasillo.organizacion import area_del_tenant
    area = await area_del_tenant(session, tenant_id, area_id)
    return area["nombre"] if area else None


async def enriquecer_actividades_con_areas(
    session: AsyncSession, tenant_id: str, actividades: list
) -> list[dict]:
    """Enriquece una lista de actividades RAT con los nombres vivos de las áreas vinculadas."""
    from dataclasses import asdict
    from app_core.pasillo.organizacion import listar_areas
    areas = await listar_areas(session, tenant_id)
    areas_vivas = {a["id"]: a["nombre"] for a in areas}
    lista = []
    for act in actividades:
        d = asdict(act) if hasattr(act, "__dataclass_fields__") else dict(act)
        if d.get("area_id") and d["area_id"] in areas_vivas:
            d["area_responsable"] = areas_vivas[d["area_id"]]
        lista.append(d)
    return lista
# === fin RAT-08 ===
