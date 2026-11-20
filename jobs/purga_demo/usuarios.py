# -*- coding: utf-8 -*-
# ¤demo
"""Purga de personas ficticias de users huérfanas de demos vencidas (DEMO-05b, DEMO-05c).

Reglas en una sola transacción:
1. Antes de borrar filas de roles, el job lee los user_id con algún rol en user_tenant_roles
   de un tenant es_demo vencido que se está purgando.
2. Tras purgar las filas del tenant, borra de ese conjunto SOLO a quien cumpla las cuatro:
   - ningún rol restante en ningún tenant (plantilla, demo activa ni real);
   - ninguna sesión con organización lo apunta: la de una demo ya purgada (tenant_id nulo por
     `ON DELETE SET NULL`) no protege a nadie, y la purga no hace UPDATE de demo_sesiones;
   - `es_persona_ficticia(users.id)` es verdadera (segunda guarda, no la regla): la función de
     politicas_purga.sql mira el correo `.invalid` y el marcador `demo`; `purga_demo` solo lee `users.id`;
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
    "AND public.es_persona_ficticia(users.id) "
    "AND NOT EXISTS (SELECT 1 FROM user_tenant_roles utr WHERE utr.user_id = users.id) "
    "AND NOT EXISTS (SELECT 1 FROM demo_sesiones ds WHERE ds.persona_usuario_id = users.id "
    "AND ds.tenant_id IS NOT NULL)"
)


def leer_candidatos_usuarios(con: Connection, tenant_id: str) -> list[str]:
    """Lee los user_id con algún rol en user_tenant_roles del tenant es_demo antes de borrar roles."""
    filas = con.execute(text(_SQL_CANDIDATOS), {"t": tenant_id}).all()
    return [f[0] for f in filas]


def purgar_usuarios_ficticios(con: Connection, candidatos: Collection[str]) -> int:
    """Borra de los candidatos SOLO a personas ficticias sin roles restantes ni sesiones con organización."""
    lista = list(candidatos)
    if not lista:
        return 0
    stmt = text(_SQL_PURGAR_USUARIOS).bindparams(bindparam("candidatos", expanding=True))
    return con.execute(stmt, {"candidatos": lista}).rowcount
