# ¤adpa
# ¤¤developer-architect
# ¤rbac-tenant
"""Trabajos de generación persistentes e idempotentes (BIB-207).

- Una petición se identifica por organización, borrador, revisión del borrador y clave de idempotencia:
  repetirla devuelve el mismo trabajo (y, cuando termine, la misma generación). La unicidad la garantiza la
  base (`UNIQUE` + `ON CONFLICT DO NOTHING`), no una lectura previa.
- Estados: pendiente → generando → listo | fallido. `reclamar` pasa a generando solo un trabajo pendiente o
  uno cuyo intento venció (`TIEMPO_LIMITE`), así una caída del worker se recupera.
- `ejecutar` genera y marca listo en el mismo punto de guardado: si algo falla no queda generación suelta, y
  un trabajo listo no vuelve a generar. El fallo queda visible con su código y se puede reintentar.
- Solo quien lo pidió, o la administración o el DPD de la organización, reintenta. La RLS limita al tenant.
Generar no aprueba el documento ni cierra acciones.
"""
from collections.abc import Mapping
from datetime import datetime
from typing import Literal
from uuid import uuid4
from pydantic import Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from api.errores import ErrorNegocio
from app_core.errors import CATALOGO_ERRORES
from features.biblioteca.domain.base import Contrato
from features.biblioteca.domain.generacion import Formato, Modo, PedirGeneracion
from features.biblioteca.services.borradores import FuentesDatos
from features.biblioteca.services.generacion import generar
import features.biblioteca.domain.errores  # noqa: F401  registra los códigos de Biblioteca al importarse

TIEMPO_LIMITE = 120.0  # segundos que puede durar un intento antes de considerarse caído
SUPERVISORES = ("admin_organizacion", "dpo")
Estado = Literal["pendiente", "generando", "listo", "fallido"]
COLUMNAS = ("id, borrador_id, revision_borrador, clave, modo, formato, estado, intentos, generacion_id, "
            "error_codigo, error_detalle, creado_por, creado_en, actualizado_en, "
            "(estado='generando' AND tomado_en < now() - make_interval(secs => CAST(:lim AS double precision))) "
            "AS vencido")
LEER = f"SELECT {COLUMNAS} FROM biblioteca_trabajos WHERE id=:id"
POR_CLAVE = (f"SELECT {COLUMNAS} FROM biblioteca_trabajos WHERE tenant_id=:t AND borrador_id=:b "
             "AND revision_borrador=:rev AND clave=:clave")
LISTAR = f"SELECT {COLUMNAS} FROM biblioteca_trabajos WHERE borrador_id=:b ORDER BY creado_en DESC, id LIMIT 50"
REVISION = "SELECT revision FROM biblioteca_borradores WHERE id=:id"
INSERTAR = ("INSERT INTO biblioteca_trabajos(id, tenant_id, borrador_id, revision_borrador, clave, modo, formato, "
            "creado_por) VALUES (:id, :t, :b, :rev, :clave, :modo, :formato, :u) "
            "ON CONFLICT (tenant_id, borrador_id, revision_borrador, clave) DO NOTHING")
RECLAMAR = ("UPDATE biblioteca_trabajos SET estado='generando', intentos=intentos+1, tomado_en=now(), "
            "error_codigo=NULL, error_detalle=NULL, actualizado_en=now() WHERE id=:id AND (estado='pendiente' OR "
            "(estado='generando' AND tomado_en < now() - make_interval(secs => CAST(:lim AS double precision)))) "
            "RETURNING id")
COMPLETAR = ("UPDATE biblioteca_trabajos SET estado='listo', generacion_id=:g, actualizado_en=now() "
             "WHERE id=:id AND estado='generando' AND generacion_id IS NULL RETURNING id")
FALLAR = ("UPDATE biblioteca_trabajos SET estado='fallido', error_codigo=:codigo, error_detalle=:detalle, "
          "actualizado_en=now() WHERE id=:id AND estado='generando'")
REINTENTAR = ("UPDATE biblioteca_trabajos SET estado='pendiente', tomado_en=NULL, error_codigo=NULL, "
              "error_detalle=NULL, actualizado_en=now() WHERE id=:id AND (estado='fallido' OR (estado='generando' "
              "AND tomado_en < now() - make_interval(secs => CAST(:lim AS double precision)))) RETURNING id")


# ¤adpa
class PedirTrabajo(Contrato):
    modo: Modo
    formato: Formato
    clave: str = Field(pattern=r"^[A-Za-z0-9_-]{8,80}$", description="Clave de idempotencia del cliente")


# ¤adpa
class Trabajo(Contrato):
    id: str
    borrador_id: str
    revision_borrador: int
    clave: str
    modo: Modo
    formato: Formato
    estado: Estado
    intentos: int
    generacion_id: str | None
    error_codigo: str | None
    error_detalle: str | None
    creado_por: str
    creado_en: datetime
    actualizado_en: datetime
    vencido: bool = False


# ¤adpa
async def _fijar_contexto(session: AsyncSession, tenant_id: str, actor: str) -> None:
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true), "
                               "set_config('app.current_user_id', :u, true)"), {"t": tenant_id, "u": actor})


# ¤adpa
def _trabajo(fila: Mapping) -> Trabajo:
    return Trabajo(**{**dict(fila), "vencido": bool(fila["vencido"])})


# ¤adpa
async def _leer(session: AsyncSession, trabajo_id: str) -> Trabajo:
    fila = (await session.execute(text(LEER), {"id": trabajo_id, "lim": TIEMPO_LIMITE})).mappings().first()
    if fila is None:  # la RLS oculta los de otra organización
        raise ErrorNegocio("BIB_TRABAJO_NO_ENCONTRADO")
    return _trabajo(fila)


# ¤adpa
async def _revision(session: AsyncSession, borrador_id: str) -> int:
    revision = (await session.execute(text(REVISION), {"id": borrador_id})).scalar()
    if revision is None:
        raise ErrorNegocio("BIB_BORRADOR_NO_ENCONTRADO")
    return revision


# ¤adpa
async def solicitar(session: AsyncSession, tenant_id: str, actor: str, borrador_id: str,
                    pedido: PedirTrabajo) -> tuple[Trabajo, bool]:
    """(trabajo, creado). La misma clave sobre la misma revisión devuelve el trabajo ya existente."""
    await _fijar_contexto(session, tenant_id, actor)
    revision = await _revision(session, borrador_id)
    datos = {"t": tenant_id, "b": borrador_id, "rev": revision, "clave": pedido.clave, "lim": TIEMPO_LIMITE}
    creado = (await session.execute(text(INSERTAR), {
        **datos, "id": str(uuid4()), "modo": pedido.modo, "formato": pedido.formato, "u": actor})).rowcount == 1
    trabajo = _trabajo((await session.execute(text(POR_CLAVE), datos)).mappings().one())
    if (trabajo.modo, trabajo.formato) != (pedido.modo, pedido.formato):
        raise ErrorNegocio("BIB_TRABAJO_CLAVE_REUTILIZADA")
    return trabajo, creado


# ¤adpa
async def obtener(session: AsyncSession, tenant_id: str, actor: str, trabajo_id: str) -> Trabajo:
    await _fijar_contexto(session, tenant_id, actor)
    return await _leer(session, trabajo_id)


# ¤adpa
async def listar(session: AsyncSession, tenant_id: str, actor: str, borrador_id: str) -> list[Trabajo]:
    await _fijar_contexto(session, tenant_id, actor)
    await _revision(session, borrador_id)
    filas = (await session.execute(text(LISTAR), {"b": borrador_id, "lim": TIEMPO_LIMITE})).mappings()
    return [_trabajo(f) for f in filas]


# ¤adpa
async def reclamar(session: AsyncSession, tenant_id: str, actor: str, trabajo_id: str) -> bool:
    """Pasa a «generando» un trabajo pendiente o vencido. False si otro intento lo tiene o ya terminó."""
    await _fijar_contexto(session, tenant_id, actor)
    return (await session.execute(text(RECLAMAR), {"id": trabajo_id, "lim": TIEMPO_LIMITE})).scalar() is not None


# ¤adpa
async def ejecutar(session: AsyncSession, fuentes: FuentesDatos, tenant_id: str, actor: str,
                   trabajo_id: str) -> Trabajo:
    """Genera un trabajo ya reclamado. Generación y estado «listo» se confirman juntos o no se confirman."""
    await _fijar_contexto(session, tenant_id, actor)
    trabajo = await _leer(session, trabajo_id)
    if trabajo.estado != "generando" or trabajo.generacion_id is not None:
        return trabajo  # ya listo, fallido o sin reclamar: nada que hacer y nada se duplica
    punto = await session.begin_nested()
    try:
        if await _revision(session, trabajo.borrador_id) != trabajo.revision_borrador:
            raise ErrorNegocio("BIB_TRABAJO_REVISION_CAMBIADA")
        g = await generar(session, fuentes, tenant_id, actor, trabajo.borrador_id,
                          PedirGeneracion(modo=trabajo.modo, formato=trabajo.formato))
        if (await session.execute(text(COMPLETAR), {"g": g.id, "id": trabajo_id})).scalar() is None:
            raise ErrorNegocio("BIB_TRABAJO_NO_REINTENTABLE")  # otro intento terminó antes: se descarta este
        await punto.commit()
    except ErrorNegocio as e:
        await punto.rollback()
        await _fallar(session, trabajo_id, e.code, e.detail)
    except Exception:  # noqa: BLE001  el detalle técnico no se muestra; el trabajo queda reintentable
        await punto.rollback()
        await _fallar(session, trabajo_id, "BIB_TRABAJO_FALLO_INTERNO", None)
    return await _leer(session, trabajo_id)


# ¤adpa
async def _fallar(session: AsyncSession, trabajo_id: str, codigo: str, detalle: str | None) -> None:
    mensaje = detalle or (CATALOGO_ERRORES[codigo].mensaje_defecto if codigo in CATALOGO_ERRORES else codigo)
    await session.execute(text(FALLAR), {"id": trabajo_id, "codigo": codigo, "detalle": mensaje[:500]})


# ¤adpa
async def reintentar(session: AsyncSession, tenant_id: str, actor: str, rol: str, trabajo_id: str) -> Trabajo:
    """Vuelve a «pendiente» un trabajo fallido o vencido. El reintento reutiliza el mismo trabajo."""
    await _fijar_contexto(session, tenant_id, actor)
    trabajo = await _leer(session, trabajo_id)
    if trabajo.creado_por != actor and rol not in SUPERVISORES:
        raise ErrorNegocio("BIB_TRABAJO_NO_AUTORIZADO")
    if (await session.execute(text(REINTENTAR), {"id": trabajo_id, "lim": TIEMPO_LIMITE})).scalar() is None:
        raise ErrorNegocio("BIB_TRABAJO_NO_REINTENTABLE")
    return await _leer(session, trabajo_id)


__all__ = ["PedirTrabajo", "Trabajo", "TIEMPO_LIMITE", "solicitar", "obtener", "listar", "reclamar", "ejecutar",
           "reintentar"]
