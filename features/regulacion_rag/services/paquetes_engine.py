# ¤regulation-code
# ¤paquete-normativo
"""Versionado, edición y publicación del paquete normativo (REG-01).

La lectura es un SELECT directo (lopdp_app solo tiene SELECT). Toda escritura llama a las funciones
SECURITY DEFINER de la migración reg01_paquetes_normativos, que guardan las invariantes en la base:
operador activo, solo borrador editable, plazo con unidad y nada sin verificar publicado.
Quién es operador lo decide antes la API con la identidad del token verificado.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import TextClause, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.errors import ErrorNegocio
from features.regulacion_rag.domain import errores
from features.regulacion_rag.domain.paquete import (
    DetallePaquete,
    Paquete,
    Parametro,
    ParametroEntrada,
    es_plazo,
)

_PREFIJO_ERROR = "REG01:"


def _traducir(exc: DBAPIError) -> ErrorNegocio:
    """Convierte 'REG01:<CODIGO>' de la base en el ErrorNegocio de la sala; lo demás se propaga."""
    mensaje = str(getattr(exc.orig, "args", [""])[0] if exc.orig is not None else exc)
    if _PREFIJO_ERROR in mensaje:
        codigo = mensaje.split(_PREFIJO_ERROR, 1)[1].split()[0].strip()
        if codigo in errores.CODIGOS_REG01:
            return ErrorNegocio(errores.CODIGOS_REG01[codigo])
    raise exc


async def _llamar(session: AsyncSession, sql: TextClause, params: dict) -> Optional[str]:
    try:
        return (await session.execute(sql, params)).scalar()
    except DBAPIError as exc:
        raise _traducir(exc) from None


async def listar_paquetes(session: AsyncSession) -> list[Paquete]:
    filas = (await session.execute(text("""
    SELECT p.id, p.codigo, p.nombre, p.version, p.estado, p.creado_por, p.creado_en,
           p.publicado_por, p.publicado_en, p.retirado_en,
           (SELECT count(*) FROM parametros_normativos x
             WHERE x.paquete_id = p.id AND NOT x.verificado) AS sin_verificar
      FROM paquetes_normativos p
     ORDER BY p.codigo, p.creado_en, p.id
"""))).mappings()
    return [Paquete(**dict(f)) for f in filas]


async def obtener_paquete(session: AsyncSession, paquete_id: str) -> Paquete:
    fila = (
        await session.execute(text("""
    SELECT p.id, p.codigo, p.nombre, p.version, p.estado, p.creado_por, p.creado_en,
           p.publicado_por, p.publicado_en, p.retirado_en,
           (SELECT count(*) FROM parametros_normativos x
             WHERE x.paquete_id = p.id AND NOT x.verificado) AS sin_verificar
      FROM paquetes_normativos p
     WHERE p.id = :id
"""), {"id": paquete_id})
    ).mappings().first()
    if fila is None:
        raise ErrorNegocio(errores.PAQUETE_NO_ENCONTRADO)
    return Paquete(**dict(fila))


async def listar_parametros(session: AsyncSession, paquete_id: str) -> list[Parametro]:
    filas = (
        await session.execute(
            text("""
    SELECT x.clave, x.valor, x.unidad, x.termino_legal, x.articulo, x.fuente_url, x.verificado,
           x.verificado_por, o.nombre AS verificado_por_nombre, x.verificado_en,
           x.actualizado_por, x.actualizado_en
      FROM parametros_normativos x
      LEFT JOIN operadores_plataforma o ON o.id = x.verificado_por
     WHERE x.paquete_id = :id ORDER BY x.clave
"""), {"id": paquete_id}
        )
    ).mappings()
    return [Parametro(**dict(f)) for f in filas]


async def detalle_paquete(session: AsyncSession, paquete_id: str) -> DetallePaquete:
    paquete = await obtener_paquete(session, paquete_id)
    return DetallePaquete(paquete=paquete, parametros=await listar_parametros(session, paquete_id))


async def paquete_publicado(session: AsyncSession, codigo: str) -> Paquete:
    fila = (
        await session.execute(
            text("""
    SELECT p.id, p.codigo, p.nombre, p.version, p.estado, p.creado_por, p.creado_en,
           p.publicado_por, p.publicado_en, p.retirado_en,
           (SELECT count(*) FROM parametros_normativos x
             WHERE x.paquete_id = p.id AND NOT x.verificado) AS sin_verificar
      FROM paquetes_normativos p
     WHERE p.codigo = :codigo AND p.estado = 'publicado'
"""), {"codigo": codigo}
        )
    ).mappings().first()
    if fila is None:
        raise ErrorNegocio(errores.PAQUETE_NO_ENCONTRADO)
    return Paquete(**dict(fila))


async def parametros_publicados(session: AsyncSession, codigo: str) -> list[Parametro]:
    """R4: el cálculo de vencimientos lee valor y unidad del paquete publicado, nunca una constante."""
    return await listar_parametros(session, (await paquete_publicado(session, codigo)).id)


async def crear_version(session: AsyncSession, operador_id: str, codigo: str, version: str) -> Paquete:
    nuevo_id = await _llamar(
        session,
        text("SELECT public.reg01_crear_version(:op, :codigo, :version)"),
        {"op": operador_id, "codigo": codigo, "version": version.strip()},
    )
    return await obtener_paquete(session, nuevo_id)


async def fijar_parametro(
    session: AsyncSession, operador_id: str, paquete_id: str, clave: str, entrada: ParametroEntrada
) -> Parametro:
    # La base vuelve a comprobarlo; aquí se responde antes y con el mismo código.
    if es_plazo(clave) and entrada.unidad is None:
        raise ErrorNegocio(errores.UNIDAD_REQUERIDA)
    await _llamar(
        session,
        text(
            "SELECT public.reg01_fijar_parametro(:op, :pid, :clave, :valor, :unidad, :termino, :articulo, "
            ":fuente, :verificado)"
        ),
        {
            "op": operador_id,
            "pid": paquete_id,
            "clave": clave,
            "valor": entrada.valor,
            "unidad": entrada.unidad,
            "termino": entrada.termino_legal,
            "articulo": entrada.articulo,
            "fuente": entrada.fuente_url,
            "verificado": entrada.verificado,
        },
    )
    fila = (
        await session.execute(
            text("""
    SELECT x.clave, x.valor, x.unidad, x.termino_legal, x.articulo, x.fuente_url, x.verificado,
           x.verificado_por, o.nombre AS verificado_por_nombre, x.verificado_en,
           x.actualizado_por, x.actualizado_en
      FROM parametros_normativos x
      LEFT JOIN operadores_plataforma o ON o.id = x.verificado_por
     WHERE x.paquete_id = :id AND x.clave = :clave
"""),
            {"id": paquete_id, "clave": clave},
        )
    ).mappings().first()
    return Parametro(**dict(fila))


async def publicar(session: AsyncSession, operador_id: str, paquete_id: str) -> tuple[Paquete, Optional[str]]:
    """Publica el borrador y retira la versión anterior en la misma transacción. Devuelve la anterior."""
    anterior = await _llamar(
        session, text("SELECT public.reg01_publicar(:op, :pid)"), {"op": operador_id, "pid": paquete_id}
    )
    return await obtener_paquete(session, paquete_id), anterior
