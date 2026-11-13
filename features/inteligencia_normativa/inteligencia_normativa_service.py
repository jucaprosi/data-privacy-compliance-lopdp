# ¤inteligencia-normativa ¤vigilancia-spdp ¤adpa
"""Compuerta de la sala Inteligencia Normativa (NORM-01): monitoreo de la SPDP y lectura del corpus."""
from __future__ import annotations

from typing import Any, Callable

from sqlalchemy import text

from features.inteligencia_normativa.domain import errores
from features.inteligencia_normativa.domain.errores import ErrorNormativo, ResolucionNoEncontrada
from features.inteligencia_normativa.schemas import (
    FiltrosResoluciones,
    ResolucionDetalle,
    ResolucionResumen,
    ResumenCorrida,
    VersionResolucion,
)
from features.inteligencia_normativa.services import monitoreo
from features.inteligencia_normativa.services.conector_spdp import ConectorSpdp

__all__ = [
    "ErrorNormativo",
    "FiltrosResoluciones",
    "ejecutar_monitoreo",
    "errores",
    "inyectar_dependencias_de_prueba",
    "listar_resoluciones",
    "obtener_resolucion",
]

_conector_de_prueba: ConectorSpdp | None = None
_almacen_de_prueba: Any = None
_sesion_de_prueba: Callable[[], Any] | None = None


def inyectar_dependencias_de_prueba(*, conector=None, almacen=None, sesion_factory=None) -> None:
    """SOLO PARA PRUEBAS: conector con servidor simulado, almacén en memoria y fábrica de sesiones."""
    global _conector_de_prueba, _almacen_de_prueba, _sesion_de_prueba
    _conector_de_prueba, _almacen_de_prueba, _sesion_de_prueba = conector, almacen, sesion_factory


def _sesion():
    if _sesion_de_prueba is not None:
        return _sesion_de_prueba()
    from app_core.db.session import async_session_factory

    return async_session_factory()


async def ejecutar_monitoreo(origen: str = "manual") -> ResumenCorrida:
    """Una corrida de monitoreo (la lanza Cloud Scheduler a las 05:00 de Guayaquil o una persona a mano)."""
    kwargs: dict[str, Any] = {"conector": _conector_de_prueba or ConectorSpdp()}
    if _almacen_de_prueba is not None:
        kwargs["almacen"] = _almacen_de_prueba
    if _sesion_de_prueba is not None:
        kwargs["sesion_factory"] = _sesion_de_prueba
    return await monitoreo.ejecutar(origen, **kwargs)


def _resumen(f) -> ResolucionResumen:
    return ResolucionResumen(
        id=f.id, numero_resolucion=f.numero_resolucion, anio_emision=f.anio_emision, titulo=f.titulo,
        seccion_fuente=f.seccion_fuente, estado=f.estado, archivo_sha256=f.archivo_sha256,
        detectada_en=f.detectada_en,
    )


async def listar_resoluciones(filtros: FiltrosResoluciones | None = None) -> list[ResolucionResumen]:
    filtros = filtros or FiltrosResoluciones()
    async with _sesion() as sesion:
        filas = (await sesion.execute(
            text("SELECT id::text AS id, numero_resolucion, anio_emision, titulo, seccion_fuente, estado, "
                 "archivo_sha256, detectada_en FROM normativa_resoluciones "
                 "WHERE (CAST(:e AS text) IS NULL OR estado = :e) "
                 "AND (CAST(:s AS text) IS NULL OR seccion_fuente = :s) "
                 "AND (CAST(:a AS integer) IS NULL OR anio_emision = :a) "
                 "ORDER BY detectada_en DESC, numero_resolucion LIMIT :l"),
            {"e": filtros.estado, "s": filtros.seccion, "a": filtros.anio, "l": filtros.limite},
        )).all()
    return [_resumen(f) for f in filas]


async def obtener_resolucion(id_resolucion: str) -> ResolucionDetalle:
    async with _sesion() as sesion:
        f = (await sesion.execute(
            text("SELECT id::text AS id, numero_resolucion, anio_emision, titulo, seccion_fuente, estado, "
                 "archivo_sha256, detectada_en, organo_emisor, materia, fecha_publicacion, url_fuente, "
                 "ruta_original, tamano_bytes, revisada_por, revisada_en FROM normativa_resoluciones "
                 "WHERE id = CAST(:i AS uuid)"),
            {"i": id_resolucion},
        )).first()
        if f is None:
            raise ResolucionNoEncontrada()
        versiones = (await sesion.execute(
            text("SELECT id::text AS id, archivo_sha256, ruta_original, detectada_en, motivo "
                 "FROM normativa_versiones WHERE resolucion_id = CAST(:i AS uuid) ORDER BY detectada_en, id"),
            {"i": id_resolucion},
        )).all()
    return ResolucionDetalle(
        **_resumen(f).model_dump(), organo_emisor=f.organo_emisor, materia=f.materia,
        fecha_publicacion=f.fecha_publicacion, url_fuente=f.url_fuente, ruta_original=f.ruta_original,
        tamano_bytes=f.tamano_bytes, revisada_por=f.revisada_por, revisada_en=f.revisada_en,
        versiones=[VersionResolucion(id=v.id, archivo_sha256=v.archivo_sha256, ruta_original=v.ruta_original,
                                     detectada_en=v.detectada_en, motivo=v.motivo) for v in versiones],
    )
