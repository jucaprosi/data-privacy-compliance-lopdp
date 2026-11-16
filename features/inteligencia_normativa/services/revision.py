# ¤inteligencia-normativa ¤vigilancia-spdp ¤adpa
"""NORM-02: catálogo con filtros, bitácora, revisión humana y lectura del original.

La revisión la hace solo el operador de la plataforma (el corpus es global); la compuerta recibe ya la identidad
verificada. El original se sirve por el backend con un `LectorOriginales` (el adaptador real llega con EVI-04).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, Protocol

from pydantic import BaseModel, Field
from sqlalchemy import text

from features.inteligencia_normativa.domain.errores import (
    EstadoNoPermitido,
    NotaObligatoria,
    OriginalNoDisponible,
    ResolucionNoEncontrada,
)
from features.inteligencia_normativa.schemas import EstadoCorrida, Origen, ResolucionResumen
from features.inteligencia_normativa.services.monitoreo import _como_normativa

ESTADOS_REVISION = ("vigente", "observada", "reformada", "derogada")
LARGO_MINIMO_NOTA = 10


class LectorOriginales(Protocol):
    """Puerto de lectura del original custodiado; devuelve None si no existe."""

    def leer(self, clave: str) -> Optional[bytes]: ...


class LectorOriginalesCerrado:
    """Por defecto falla cerrado: sin adaptador real no se sirve ningún original."""

    def leer(self, clave: str) -> Optional[bytes]:
        raise OriginalNoDisponible()


class FiltrosCatalogo(BaseModel):
    numero: Optional[str] = Field(default=None, max_length=100)
    anio: Optional[int] = Field(default=None, ge=1990, le=2100)
    q: Optional[str] = Field(default=None, max_length=200)
    organo: Optional[str] = Field(default=None, max_length=200)
    materia: Optional[str] = Field(default=None, max_length=200)
    estado: Optional[str] = None
    pagina: int = Field(default=1, ge=1)
    por_pagina: int = Field(default=25, ge=1, le=100)


class PaginaResoluciones(BaseModel):
    total: int
    pagina: int
    por_pagina: int
    items: list[ResolucionResumen]


class ResolucionConNota(BaseModel):
    id: str
    estado: str
    revisada_por: Optional[str] = None
    revisada_en: Optional[datetime] = None
    nota_revision: Optional[str] = None


class CorridaBitacora(BaseModel):
    id: str
    origen: Origen
    estado: EstadoCorrida
    inicio: datetime
    fin: Optional[datetime] = None
    documentos_vistos: int = 0
    nuevos: int = 0
    versiones_nuevas: int = 0
    errores: int = 0


def _like(valor: str) -> str:
    escapado = valor.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escapado}%"


_COLUMNAS = ("id::text AS id, numero_resolucion, anio_emision, titulo, seccion_fuente, estado, "
             "archivo_sha256, detectada_en")
_DONDE = (
    "WHERE (CAST(:num AS text) IS NULL OR numero_resolucion ILIKE :num ESCAPE '\\') "
    "AND (CAST(:a AS integer) IS NULL OR anio_emision = :a) "
    "AND (CAST(:q AS text) IS NULL OR titulo ILIKE :q ESCAPE '\\' OR numero_resolucion ILIKE :q ESCAPE '\\') "
    "AND (CAST(:o AS text) IS NULL OR organo_emisor ILIKE :o ESCAPE '\\') "
    "AND (CAST(:m AS text) IS NULL OR materia ILIKE :m ESCAPE '\\') "
    "AND (CAST(:e AS text) IS NULL OR estado = :e) "
)


async def listar_catalogo(sesion, filtros: FiltrosCatalogo) -> PaginaResoluciones:
    params: dict[str, Any] = {
        "num": _like(filtros.numero) if filtros.numero else None, "a": filtros.anio,
        "q": _like(filtros.q) if filtros.q else None, "o": _like(filtros.organo) if filtros.organo else None,
        "m": _like(filtros.materia) if filtros.materia else None, "e": filtros.estado,
    }
    total = (await sesion.execute(text(f"SELECT count(*) FROM normativa_resoluciones {_DONDE}"), params)).scalar_one()
    filas = (await sesion.execute(
        text(f"SELECT {_COLUMNAS} FROM normativa_resoluciones {_DONDE}"
             "ORDER BY detectada_en DESC, numero_resolucion LIMIT :l OFFSET :off"),
        {**params, "l": filtros.por_pagina, "off": (filtros.pagina - 1) * filtros.por_pagina},
    )).all()
    items = [ResolucionResumen(
        id=f.id, numero_resolucion=f.numero_resolucion, anio_emision=f.anio_emision, titulo=f.titulo,
        seccion_fuente=f.seccion_fuente, estado=f.estado, archivo_sha256=f.archivo_sha256,
        detectada_en=f.detectada_en) for f in filas]
    return PaginaResoluciones(total=total, pagina=filtros.pagina, por_pagina=filtros.por_pagina, items=items)


async def nota_de_revision(sesion, id_resolucion: str) -> ResolucionConNota:
    f = (await sesion.execute(
        text("SELECT id::text AS id, estado, revisada_por, revisada_en, nota_revision "
             "FROM normativa_resoluciones WHERE id = CAST(:i AS uuid)"), {"i": id_resolucion},
    )).first()
    if f is None:
        raise ResolucionNoEncontrada()
    return ResolucionConNota(id=f.id, estado=f.estado, revisada_por=f.revisada_por,
                             revisada_en=f.revisada_en, nota_revision=f.nota_revision)


async def listar_bitacora(sesion, limite: int = 50) -> list[CorridaBitacora]:
    filas = (await sesion.execute(
        text("SELECT id::text AS id, origen, estado, inicio, fin, documentos_vistos, nuevos, versiones_nuevas, "
             "errores FROM normativa_monitoreo_logs ORDER BY inicio DESC LIMIT :l"), {"l": limite},
    )).all()
    return [CorridaBitacora(id=f.id, origen=f.origen, estado=f.estado, inicio=f.inicio, fin=f.fin,
                            documentos_vistos=f.documentos_vistos, nuevos=f.nuevos,
                            versiones_nuevas=f.versiones_nuevas, errores=f.errores) for f in filas]


async def registrar_revision(sesion, id_resolucion: str, estado: str, nota: str, usuario_id: str) -> ResolucionConNota:
    """Cambia el estado con quién, cuándo y la nota. El rol de escritura es el del monitoreo (`lopdp_normativa`)."""
    if estado not in ESTADOS_REVISION:
        raise EstadoNoPermitido()
    nota_limpia = (nota or "").strip()
    if len(nota_limpia) < LARGO_MINIMO_NOTA:
        raise NotaObligatoria()
    await _como_normativa(sesion)
    actualizadas = (await sesion.execute(
        text("UPDATE normativa_resoluciones SET estado = :e, revisada_por = :u, revisada_en = now(), "
             "nota_revision = :n WHERE id = CAST(:i AS uuid)"),
        {"e": estado, "u": usuario_id, "n": nota_limpia, "i": id_resolucion},
    )).rowcount
    if not actualizadas:
        raise ResolucionNoEncontrada()
    await sesion.commit()
    return await nota_de_revision(sesion, id_resolucion)


async def clave_original(sesion, id_resolucion: str) -> str:
    fila = (await sesion.execute(
        text("SELECT ruta_original FROM normativa_resoluciones WHERE id = CAST(:i AS uuid)"), {"i": id_resolucion},
    )).first()
    if fila is None:
        raise ResolucionNoEncontrada()
    return fila.ruta_original


def leer_original(lector: LectorOriginales, clave: str) -> bytes:
    contenido = lector.leer(clave)
    if contenido is None:
        raise OriginalNoDisponible()
    return contenido
