"""Plantillas sectoriales del RAT (RAT-02).

Una plantilla es un catálogo de actividades típicas de un sector que el coordinador puede cargar en
el RAT de su organización, eligiendo cuáles aplican. Hoy existe la de salud
(`domain/plantillas/salud.json`, matriz de trabajo SALUDATA). Bases legales y plazos de conservación
son «sugerido, validar»: se cargan en el RAT con esa advertencia en las observaciones.
"""
import json
from functools import lru_cache
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from features.organizacion.organizacion_service import get_tenant_config
from features.rat.domain.models import ActividadRAT, BaseLegitimacion, CategoriaTitular
from features.rat.services.rat_engine import crear_o_actualizar_actividad, obtener_actividades_tenant

DIRECTORIO = Path(__file__).resolve().parent.parent / "domain" / "plantillas"
SECTORES = ("salud",)


class PlantillaNoDisponible(LookupError):
    """La organización no es del sector de la plantilla, o la plantilla no existe."""


@lru_cache(maxsize=None)
def cargar_plantilla(sector: str) -> dict:
    if sector not in SECTORES:
        raise PlantillaNoDisponible(f"No hay plantilla para el sector «{sector}»")
    return json.loads((DIRECTORIO / f"{sector}.json").read_text(encoding="utf-8"))


def sector_de_la_organizacion(sector_registrado: str | None) -> str | None:
    """Sector de plantilla que corresponde al sector libre de la ficha («Salud», «Clínica de salud»…)."""
    texto = (sector_registrado or "").strip().lower()
    return next((s for s in SECTORES if s in texto), None)


def _actividad(tenant_id: str, plantilla: dict, entrada: dict) -> ActividadRAT:
    datos = dict(entrada["actividad"])
    datos["base_legal"] = BaseLegitimacion(datos["base_legal"])
    datos["categorias_titulares"] = [CategoriaTitular(c) for c in datos["categorias_titulares"]]
    aviso = (
        f"Cargada desde la plantilla «{plantilla['fuente']['titulo']}» ({plantilla['version']}). "
        f"Base legal sugerida: {entrada['base_legal_sugerida']['texto']}. "
        f"Conservación sugerida: {entrada['conservacion_sugerida']['texto']}. "
        "Ambas son sugerencias: validarlas antes de darlas por definitivas."
    )
    datos["observaciones_dpo"] = (datos.get("observaciones_dpo") or "") + (" " if datos.get("observaciones_dpo") else "") + aviso
    return ActividadRAT(tenant_id=tenant_id, **datos)


async def plantillas_disponibles(session: AsyncSession, tenant_id: str) -> list[dict]:
    """Plantillas que la organización puede cargar, con sus actividades y el actor sugerido."""
    sector = sector_de_la_organizacion((await get_tenant_config(session, tenant_id)).get("sector"))
    if sector is None:
        return []
    plantilla = cargar_plantilla(sector)
    return [{
        "sector": sector,
        "version": plantilla["version"],
        "fuente": plantilla["fuente"]["titulo"],
        "actividades": [
            {
                "codigo": e["actividad"]["codigo"],
                "nombre": e["actividad"]["nombre"],
                "finalidad": e["actividad"]["finalidad"],
                "actor_sugerido": e["actor_sugerido"],
            }
            for e in plantilla["actividades"]
        ],
    }]


async def aplicar_plantilla(
    session: AsyncSession, tenant_id: str, user_id: str, sector: str, codigos: list[str],
) -> dict:
    """Crea en el RAT las actividades elegidas que aún no estén cargadas desde esta plantilla."""
    if sector_de_la_organizacion((await get_tenant_config(session, tenant_id)).get("sector")) != sector:
        raise PlantillaNoDisponible(f"La plantilla «{sector}» no corresponde al sector de la organización")
    plantilla = cargar_plantilla(sector)
    por_codigo = {e["actividad"]["codigo"]: e for e in plantilla["actividades"]}
    desconocidos = sorted(set(codigos) - set(por_codigo))
    if desconocidos:
        raise ValueError(f"Actividades que no están en la plantilla: {', '.join(desconocidos)}")

    origen = f"plantilla:{sector}"
    ya_cargados = {
        a.codigo for a in await obtener_actividades_tenant(session, tenant_id) if a.origen == origen
    }
    creadas, omitidas = [], []
    for codigo in dict.fromkeys(codigos):
        if codigo in ya_cargados:
            omitidas.append(codigo)
            continue
        guardada = await crear_o_actualizar_actividad(
            session, _actividad(tenant_id, plantilla, por_codigo[codigo]), user_id
        )
        creadas.append(guardada.codigo)
    return {"sector": sector, "creadas": creadas, "omitidas": omitidas}
