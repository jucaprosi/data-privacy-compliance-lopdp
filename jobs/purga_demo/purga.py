# -*- coding: utf-8 -*-
# ¤demo
"""Purga física de las demos vencidas (DEMO-05).

Orden: objetos del tenant, filas de todas las tablas con `tenant_id`, fila del tenant y comprobación de
0 filas. Nunca toca la plantilla. La fila de `demo_sesiones` se conserva (con `tenant_id` y persona en
nulo por `ON DELETE SET NULL`) hasta 90 días después de vencer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import IntegrityError

from features.demo.demo_service import PLANTILLA_TENANT_ID

from .almacen import Almacen

DIAS_DE_RETENCION = 90
#: No se purgan por tenant: `tenants` se borra al final y `demo_sesiones` se conserva.
TABLAS_EXENTAS = frozenset({"demo_sesiones", "tenants"})


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
_SQL_TABLAS = (
    "SELECT c.table_name FROM information_schema.columns c JOIN information_schema.tables t "
    "ON t.table_schema = c.table_schema AND t.table_name = c.table_name "
    "WHERE c.table_schema = 'public' AND c.column_name = 'tenant_id' AND t.table_type = 'BASE TABLE' "
    "ORDER BY c.table_name"
)


def tenants_vencidos(con: Connection) -> list[str]:
    return [f[0] for f in con.execute(text(_SQL_VENCIDOS), {"plantilla": PLANTILLA_TENANT_ID})]


def tablas_con_tenant(con: Connection) -> list[str]:
    return [f[0] for f in con.execute(text(_SQL_TABLAS)) if f[0] not in TABLAS_EXENTAS]


def _q(con: Connection, nombre: str) -> str:
    return con.dialect.identifier_preparer.quote(nombre)


def _borrar_filas(con: Connection, tenant_id: str, tablas: list[str]) -> int:
    """Borra por pasadas: una tabla con FK a otra de la lista espera a que la hija se vacíe."""
    pendientes, total = list(tablas), 0
    while pendientes:
        siguientes = []
        for tabla in pendientes:
            try:
                with con.begin_nested():
                    total += con.execute(
                        text(f"DELETE FROM {_q(con, tabla)} WHERE tenant_id::text = :t"), {"t": tenant_id}).rowcount
            except IntegrityError:
                siguientes.append(tabla)
        if len(siguientes) == len(pendientes):
            raise ErrorPurga(f"no se pudo vaciar por claves foráneas: {', '.join(siguientes)}")
        pendientes = siguientes
    return total


def comprobar_cero_filas(con: Connection, tenant_id: str, tablas: list[str]) -> None:
    """Falla si queda alguna fila del tenant en una tabla con `tenant_id`, en `tenants` o en `demo_sesiones`."""
    restos = {}
    for tabla in tablas:
        n = con.execute(text(f"SELECT count(*) FROM {_q(con, tabla)} WHERE tenant_id::text = :t"),
                        {"t": tenant_id}).scalar_one()
        if n:
            restos[tabla] = n
    if con.execute(text("SELECT count(*) FROM tenants WHERE id = :t"), {"t": tenant_id}).scalar_one():
        restos["tenants"] = 1
    if con.execute(text("SELECT count(*) FROM demo_sesiones WHERE tenant_id = :t"), {"t": tenant_id}).scalar_one():
        restos["demo_sesiones"] = 1
    if restos:
        raise ErrorPurga(f"quedan filas del tenant tras la purga: {restos}")


def purgar_tenant(motor: Engine, almacen: Almacen, tenant_id: str) -> tuple[int, int]:
    """Objetos primero, filas después. Devuelve (objetos, filas). Si queda algo, revierte y falla."""
    if tenant_id == PLANTILLA_TENANT_ID:
        raise ErrorPurga("la plantilla nunca se purga.")
    prefijo = f"{tenant_id}/"
    claves = almacen.listar(prefijo)
    if claves:
        almacen.borrar(claves)
    if almacen.listar(prefijo):
        raise ErrorPurga(f"quedan objetos con el prefijo del tenant {tenant_id}.")
    with motor.begin() as con:
        tablas = tablas_con_tenant(con)
        # `users` no tiene `tenant_id`: la sesión del vendedor deja de apuntar a la persona (y al tenant).
        con.execute(text("UPDATE demo_sesiones SET persona_usuario_id = NULL, tenant_id = NULL "
                         "WHERE tenant_id = :t"), {"t": tenant_id})
        filas = _borrar_filas(con, tenant_id, tablas)
        filas += con.execute(text("DELETE FROM tenants WHERE id = :t AND es_demo"), {"t": tenant_id}).rowcount
        comprobar_cero_filas(con, tenant_id, tablas)
    return len(claves), filas


def caducar_sesiones(motor: Engine, ahora: datetime) -> int:
    """Borra las filas de `demo_sesiones` vencidas hace más de 90 días."""
    with motor.begin() as con:
        return con.execute(
            text("DELETE FROM demo_sesiones WHERE estado = 'vencida' AND terminada_en < :limite"),
            {"limite": ahora - timedelta(days=DIAS_DE_RETENCION)}).rowcount


def purgar(motor: Engine, almacen: Almacen, ahora: datetime) -> Informe:
    informe = Informe()
    with motor.connect() as con:
        vencidos = tenants_vencidos(con)
    for tenant_id in vencidos:
        objetos, filas = purgar_tenant(motor, almacen, tenant_id)
        informe.tenants.append(tenant_id)
        informe.objetos += objetos
        informe.filas += filas
    informe.sesiones_caducadas = caducar_sesiones(motor, ahora)
    return informe
