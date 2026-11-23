# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤demo
"""Purga física de las demos vencidas (DEMO-05, DEMO-05c, DEMO-05d).

Orden: objetos del tenant, filas de todas las tablas con `tenant_id`, fila del tenant y comprobación de
0 filas. Nunca toca la plantilla. La fila de `demo_sesiones` se conserva hasta 90 días después de vencer:
`ON DELETE SET NULL` vacía su `tenant_id` al borrar el tenant y su persona al borrar la persona ficticia.
La purga nunca hace UPDATE ni INSERT (DEMO-05c R5): corre como `purga_demo`, con solo SELECT y DELETE.
Las tablas con trigger de inmutabilidad las borra `purga_demo_borrar_inmutables`, que solo existe en la base
de la demo (DEMO-05d): `purga_demo` no es dueño de nada y no puede desactivar un trigger.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterator, Union

from sqlalchemy import String, cast, column, delete, func, select, table, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import IntegrityError

from features.demo.demo_service import PLANTILLA_TENANT_ID

from .almacen import Almacen
from .usuarios import leer_candidatos_usuarios, purgar_usuarios_ficticios

DIAS_DE_RETENCION = 90
#: Tablas con un trigger que lanza en DELETE (DEMO-05d §1), en el orden en que las borra la función.
TABLAS_INMUTABLES = (
    "biblioteca_documentos_historial",
    "biblioteca_descargas",
    "biblioteca_eventos_documento",
    "dpo_consultas_mensajes",
    "dpo_consultas",
)
FUNCION_INMUTABLES = "purga_demo_borrar_inmutables"
#: No se purgan con `_borrar_filas`: `tenants` se borra al final, `demo_sesiones` se conserva y las
#: inmutables las borra la función antes que el resto.
TABLAS_EXENTAS = frozenset({"demo_sesiones", "tenants", *TABLAS_INMUTABLES})

Destino = Union[Engine, Connection]


class ErrorPurga(RuntimeError):
    """La purga no dejó 0 filas u objetos; el job sale con error."""


@dataclass
class Informe:
    tenants: list[str] = field(default_factory=list)
    objetos: int = 0
    filas: int = 0
    sesiones_caducadas: int = 0


_SQL_VENCIDOS = (
    "SELECT t.id FROM tenants t WHERE t.es_demo AND t.id <> :plantilla "
    "AND EXISTS (SELECT 1 FROM demo_sesiones s WHERE s.tenant_id = t.id AND s.estado = 'vencida') "
    "AND NOT EXISTS (SELECT 1 FROM demo_sesiones s WHERE s.tenant_id = t.id AND s.estado = 'activa') "
    "ORDER BY t.id"
)
# Catálogo y no information_schema: este solo enseña las columnas sobre las que el rol tiene algún permiso,
# y una tabla nueva sin GRANT quedaría fuera de la purga y de la guardia (DEMO-05c R9).
_SQL_TABLAS = (
    "SELECT c.relname FROM pg_catalog.pg_class c JOIN pg_catalog.pg_attribute a "
    "ON a.attrelid = c.oid AND a.attname = 'tenant_id' AND a.attnum > 0 AND NOT a.attisdropped "
    "WHERE c.relnamespace = 'public'::regnamespace AND c.relkind IN ('r', 'p') "
    "ORDER BY c.relname"
)


@contextmanager
def transaccion(destino: Destino) -> Iterator[Connection]:
    """Con un `Engine`, abre y confirma su transacción; con una `Connection`, un savepoint que no confirma."""
    if isinstance(destino, Connection):
        with destino.begin_nested():
            yield destino
    else:
        with destino.begin() as con:
            yield con


def tenants_vencidos(con: Connection) -> list[str]:
    return [f[0] for f in con.execute(text(_SQL_VENCIDOS), {"plantilla": PLANTILLA_TENANT_ID})]


def tablas_con_tenant(con: Connection) -> list[str]:
    return [f[0] for f in con.execute(text(_SQL_TABLAS)) if f[0] not in TABLAS_EXENTAS]


def _de_tenant(tabla: str, tenant_id: str):
    """Condición `tenant_id::text = :t` sobre una tabla; SQLAlchemy cita el identificador."""
    return table(tabla, column("tenant_id")), cast(column("tenant_id"), String) == tenant_id


def _borrar_filas(con: Connection, tenant_id: str, tablas: list[str]) -> int:
    """Borra por pasadas: una tabla con FK a otra de la lista espera a que la hija se vacíe."""
    pendientes, total = list(tablas), 0
    while pendientes:
        siguientes = []
        for tabla in pendientes:
            try:
                with con.begin_nested():
                    objetivo, condicion = _de_tenant(tabla, tenant_id)
                    total += con.execute(delete(objetivo).where(condicion)).rowcount
            except IntegrityError:
                siguientes.append(tabla)
        if len(siguientes) == len(pendientes):
            raise ErrorPurga(f"no se pudo vaciar por claves foráneas: {', '.join(siguientes)}")
        pendientes = siguientes
    return total


_SQL_HAY_FUNCION = f"SELECT to_regprocedure('public.{FUNCION_INMUTABLES}(character varying)') IS NOT NULL"


def _borrar_inmutables(con: Connection, tenant_id: str) -> int:
    """Borra las tablas inmutables del tenant con la función de DEMO-05d, que solo existe en la base de la demo.

    En el Job, la guardia (`falta_funcion_inmutables`) exige la función antes de borrar nada. En una base sin
    `politicas_purga.sql` no se toca ninguna de esas tablas: si el tenant tuviera filas en ellas,
    `comprobar_cero_filas` lo detecta y la transacción revierte. Nunca hay un borrado a medias.
    """
    if not con.execute(text(_SQL_HAY_FUNCION)).scalar_one():
        return 0
    return con.execute(text(f"SELECT public.{FUNCION_INMUTABLES}(CAST(:t AS character varying))"),
                       {"t": tenant_id}).scalar_one()


def comprobar_cero_filas(con: Connection, tenant_id: str, tablas: list[str]) -> None:
    """Falla si queda alguna fila del tenant en una tabla con `tenant_id`, en `tenants` o en `demo_sesiones`."""
    restos = {}
    for tabla in tablas:
        objetivo, condicion = _de_tenant(tabla, tenant_id)
        n = con.execute(select(func.count()).select_from(objetivo).where(condicion)).scalar_one()
        if n:
            restos[tabla] = n
    if con.execute(text("SELECT count(*) FROM tenants WHERE id = :t"), {"t": tenant_id}).scalar_one():
        restos["tenants"] = 1
    if con.execute(text("SELECT count(*) FROM demo_sesiones WHERE tenant_id = :t"), {"t": tenant_id}).scalar_one():
        restos["demo_sesiones"] = 1
    if restos:
        raise ErrorPurga(f"quedan filas del tenant tras la purga: {restos}")


def purgar_tenant(destino: Destino, almacen: Almacen, tenant_id: str) -> tuple[int, int]:
    """Objetos primero, filas después. Devuelve (objetos, filas). Si queda algo, revierte y falla."""
    if tenant_id == PLANTILLA_TENANT_ID:
        raise ErrorPurga("la plantilla nunca se purga.")
    prefijo = f"{tenant_id}/"
    claves = almacen.listar(prefijo)
    fuera = [c for c in claves if not c.partition("/")[2].startswith(prefijo)]
    if fuera:
        raise ErrorPurga("el almacén listó objetos fuera del prefijo del tenant; no se borra nada.")
    if claves:
        almacen.borrar(claves)
    if almacen.listar(prefijo):
        raise ErrorPurga(f"quedan objetos con el prefijo del tenant {tenant_id}.")
    with transaccion(destino) as con:
        tablas = tablas_con_tenant(con)
        candidatos = leer_candidatos_usuarios(con, tenant_id)
        filas = _borrar_inmutables(con, tenant_id)
        filas += _borrar_filas(con, tenant_id, tablas)
        filas += con.execute(text("DELETE FROM tenants WHERE id = :t AND es_demo"), {"t": tenant_id}).rowcount
        filas += purgar_usuarios_ficticios(con, candidatos)
        comprobar_cero_filas(con, tenant_id, [*tablas, *TABLAS_INMUTABLES])
    return len(claves), filas


def caducar_sesiones(destino: Destino, ahora: datetime) -> int:
    """Borra las filas de `demo_sesiones` vencidas hace más de 90 días."""
    with transaccion(destino) as con:
        return con.execute(
            text("DELETE FROM demo_sesiones WHERE estado = 'vencida' AND terminada_en < :limite"),
            {"limite": ahora - timedelta(days=DIAS_DE_RETENCION)}).rowcount


def purgar(destino: Destino, almacen: Almacen, ahora: datetime) -> Informe:
    informe = Informe()
    if isinstance(destino, Connection):
        vencidos = tenants_vencidos(destino)
    else:
        with destino.connect() as con:
            vencidos = tenants_vencidos(con)
    for tenant_id in vencidos:
        objetos, filas = purgar_tenant(destino, almacen, tenant_id)
        informe.tenants.append(tenant_id)
        informe.objetos += objetos
        informe.filas += filas
    informe.sesiones_caducadas = caducar_sesiones(destino, ahora)
    return informe
