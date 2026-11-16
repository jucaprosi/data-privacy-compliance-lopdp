# -*- coding: utf-8 -*-
# ¤demo
"""Purga de personas ficticias de users huérfanas de demos vencidas (DEMO-05b).

Reglas en una sola transacción:
1. Antes de borrar filas de roles, el job lee los user_id con algún rol en user_tenant_roles
   de un tenant es_demo vencido que se está purgando.
2. Tras purgar las filas del tenant, borra de ese conjunto SOLO a quien cumpla las cuatro:
   - ningún rol restante en ningún tenant (plantilla, demo activa ni real);
   - ninguna fila de demo_sesiones lo apunta (la purga deja persona_usuario_id en nulo);
   - el correo termina en .invalid (segunda guarda, no la regla);
   - y su única pertenencia fue a esos tenants vencidos.
3. Un .invalid sin ningún rol en el conjunto del paso 1 no se toca.
"""
from __future__ import annotations

from typing import Collection

from sqlalchemy import bindparam, text
from sqlalchemy.engine import Connection

_SQL_CANDIDATOS = (
    "SELECT DISTINCT utr.user_id "
    "FROM user_tenant_roles utr "
    "JOIN tenants t ON t.id = utr.tenant_id "
    "WHERE utr.tenant_id = :t AND t.es_demo"
)

_SQL_PURGAR_USUARIOS = (
    "DELETE FROM users "
    "WHERE id IN :candidatos "
    "AND email LIKE '%.invalid' "
    "AND NOT EXISTS (SELECT 1 FROM user_tenant_roles utr WHERE utr.user_id = users.id) "
    "AND NOT EXISTS (SELECT 1 FROM demo_sesiones ds WHERE ds.persona_usuario_id = users.id)"
)


def leer_candidatos_usuarios(con: Connection, tenant_id: str) -> list[str]:
    """Lee los user_id con algún rol en user_tenant_roles del tenant es_demo antes de borrar roles."""
    filas = con.execute(text(_SQL_CANDIDATOS), {"t": tenant_id}).all()
    return [f[0] for f in filas]


def purgar_usuarios_ficticios(con: Connection, candidatos: Collection[str]) -> int:
    """Borra de los candidatos SOLO a quienes no tengan roles restantes, ni sesiones, y correo .invalid."""
    lista = list(candidatos)
    if not lista:
        return 0
    stmt = text(_SQL_PURGAR_USUARIOS).bindparams(bindparam("candidatos", expanding=True))
    return con.execute(stmt, {"candidatos": lista}).rowcount
