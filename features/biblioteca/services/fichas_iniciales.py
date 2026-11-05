# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Servicio BIB-208: cobertura de captura/salida de las ocho fichas iniciales.

Los datos de otras salas llegan por puertos que arma el router con sus compuertas (RAT y Roadmap):
Biblioteca no las importa. El tenant sale siempre de la sesión. Nada de aquí escribe en el RAT ni en
el plan: RAT-01 devuelve propuestas documentales y PLA-01 una instantánea de solo lectura.
"""
from collections.abc import Awaitable, Callable, Mapping, Sequence
from datetime import date
from pydantic import BaseModel
from app_core.errors import ErrorNegocio
from features.biblioteca.plantillas.captura import (
    ContextoServidor, EntradaFicha, ResultadoFicha, evaluar_tabla,
)
from features.biblioteca.plantillas.exportaciones import InstantaneaPlan, ResultadoRAT, exportar_plan, proponer_rat
from features.biblioteca.plantillas.mapas import CODIGOS, MapaFicha, mapa, mapas
from features.biblioteca.plantillas.secciones import evaluar_secciones

LeerActividades = Callable[[object, str], Awaitable[Sequence[Mapping]]]
LeerAcciones = Callable[[object, str, str], Awaitable[Sequence[Mapping]]]


# ¤adpa
class CampoPublico(BaseModel):
    clave: str
    etiqueta: str
    tipo: str
    requisito: str
    valores: list[str]
    editable: bool
    columna: str | None
    seccion: str | None


# ¤adpa
class MapaPublico(BaseModel):
    codigo: str
    modo: str
    version_esquema: str
    plantilla: str
    interfaz: str
    secciones: list[str]
    colecciones: list[str]
    estado_generacion: str
    campos: list[CampoPublico]


def _publico(m: MapaFicha) -> MapaPublico:
    return MapaPublico(
        codigo=m.codigo, modo=m.modo, version_esquema=m.version_esquema, plantilla=m.plantilla, interfaz=m.interfaz,
        secciones=list(m.secciones), colecciones=sorted(m.colecciones), estado_generacion=m.estado_generacion,
        campos=[CampoPublico(clave=c.clave, etiqueta=c.etiqueta, tipo=c.tipo, requisito=c.requisito,
                             valores=list(c.valores), editable=c.editable and c.requisito != "D",
                             columna=c.columna, seccion=c.seccion) for c in m.campos],
    )


def _exigir(codigo: str) -> MapaFicha:
    encontrado = mapa(codigo)
    if encontrado is None:
        raise ErrorNegocio("BIB_FICHA_INICIAL_DESCONOCIDA")
    return encontrado


# ¤adpa
def listar_mapas() -> list[MapaPublico]:
    return [_publico(mapas()[c]) for c in CODIGOS]


# ¤adpa
def obtener_mapa(codigo: str) -> MapaPublico:
    return _publico(_exigir(codigo))


async def _tratamientos(session, tenant_id: str, leer: LeerActividades) -> list[Mapping]:
    return list(await leer(session, tenant_id))


# ¤adpa
async def evaluar_ficha(session, tenant_id: str, actor_id: str, codigo: str, entrada: EntradaFicha,
                        leer_actividades: LeerActividades) -> ResultadoFicha | ResultadoRAT:
    """Evalúa una captura sin guardarla: pendientes, versión siguiente y salida hasta la última fila real."""
    m = _exigir(codigo)
    actividades = await _tratamientos(session, tenant_id, leer_actividades)
    if codigo == "RAT-01":
        return proponer_rat(m, entrada, actividades)
    validos = frozenset(str(a["id"]) for a in actividades)
    if m.modo == "tabla":
        return evaluar_tabla(m, entrada, validos)
    contexto = ContextoServidor(organizacion_id=tenant_id, actor_id=actor_id, fecha=date.today())
    return evaluar_secciones(m, entrada, contexto, validos)


# ¤adpa
async def instantanea_plan(session, tenant_id: str, roadmap_id: str, fecha_corte: str | None,
                           leer_acciones: LeerAcciones) -> InstantaneaPlan:
    try:
        corte = date.fromisoformat(fecha_corte) if fecha_corte else date.today()
    except ValueError as exc:
        raise ErrorNegocio("BIB_FICHA_INICIAL_FECHA_CORTE") from exc
    acciones = await leer_acciones(session, tenant_id, roadmap_id)
    return exportar_plan(_exigir("PLA-01"), acciones, corte)
