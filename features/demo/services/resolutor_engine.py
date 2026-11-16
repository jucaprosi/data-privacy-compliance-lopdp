# -*- coding: utf-8 -*-
# ¤demo ¤seguridad ¤adpa
"""DEMO-01: el resolutor de identidad de la demo (invariante 61).

`resolver_usuario` traduce el `sub` ya verificado a la persona activa de la sesión demo del vendedor.
Es lo que el gancho de DEMO-08 llama en cada petición, así que falla cerrado: sesión inexistente,
vencida por inactividad, de un vendedor retirado de `DEMO_VENDEDORES` o con una persona que ya no es del
tenant `es_demo` de la sesión ⟹ `DEMO_VENCIDA` (401). La persona se busca solo dentro de ese tenant y el
filtro vive en la consulta, no en una comprobación posterior. La actividad se renueva como mucho cada 60 s.

Una sesión que se vence aquí se confirma (`commit`) antes de lanzar el error: el gestor de sesión de la API
revierte la transacción cuando una petición falla, y la baja no puede perderse con ella.
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.db.session import fijar_contexto_rls
from app_core.pasillo import organizacion as pasillo_organizacion
from features.demo.domain.errores import DEMO_VENCIDA, ErrorDemo
from features.demo.domain.eventos import EventoDemo
from features.demo.domain.personas import ETIQUETAS, ORDEN_DE_ROLES, PersonaDemo
from features.demo.domain.sesion import MotivoFin, SesionDemo, esta_vencida
from features.demo.repo import sesiones_repo

#: La actividad se renueva como mucho una vez por minuto, para no escribir en cada petición.
SEGUNDOS_ENTRE_RENOVACIONES = 60
ENTIDAD_SESION = "demo_sesion"


def vendedores_autorizados() -> frozenset[str]:
    """Correos de `DEMO_VENDEDORES` (secreto del proyecto demo), en minúsculas. Vacío cierra la demo."""
    crudo = os.environ.get("DEMO_VENDEDORES", "")
    return frozenset(c.lower() for c in re.split(r"[,;\s]+", crudo) if c)


async def _vencer(session: AsyncSession, sesion: SesionDemo, motivo: MotivoFin, causa: str, ahora: datetime) -> None:
    """Marca la sesión vencida, deja el evento con el vendedor real y confirma antes de que el error la revierta."""
    await sesiones_repo.marcar_vencida(session, sesion.id, motivo, ahora)
    if sesion.tenant_ids:
        tenant = sesion.tenant_ids[0]
        await fijar_contexto_rls(session, tenant)
        await registrar_evento(
            session, tenant, ENTIDAD_SESION, sesion.id, EventoDemo.DEMO_VENCIDA.value, None,
            {"vendedor_sub": sesion.vendedor_sub, "vendedor_email": sesion.vendedor_email, "causa": causa},
        )
    await session.commit()


async def sesion_vigente(session: AsyncSession, vendedor_sub: str, ahora: datetime | None = None) -> SesionDemo:
    """Sesión activa del vendedor, comprobada en esta petición; si no es válida, la vence y lanza 401."""
    ahora = ahora or datetime.now(timezone.utc)
    sesion = await sesiones_repo.obtener_activa(session, vendedor_sub)
    if sesion is None or not sesion.tenant_ids:
        raise ErrorDemo(DEMO_VENCIDA)
    if sesion.vendedor_email.lower() not in vendedores_autorizados():
        await _vencer(session, sesion, MotivoFin.TERMINAR, "vendedor_retirado", ahora)
        raise ErrorDemo(DEMO_VENCIDA)
    if sesion.ultima_actividad is not None and esta_vencida(sesion.ultima_actividad, ahora):
        await _vencer(session, sesion, MotivoFin.INACTIVIDAD, "inactividad", ahora)
        raise ErrorDemo(DEMO_VENCIDA)
    return sesion


async def es_tenant_demo(session: AsyncSession, tenant_id: str) -> bool:
    await fijar_contexto_rls(session, tenant_id)
    fila = (await session.execute(text("SELECT es_demo FROM tenants WHERE id = :t"), {"t": tenant_id})).first()
    return bool(fila and fila[0])


async def personas_del_tenant(session: AsyncSession, tenant_id: str) -> list[PersonaDemo]:
    """Personas con rol vigente en el tenant demo, una por usuario, en el orden fijo del ciclo.

    Un tenant que no es `es_demo` no tiene personas: el filtro se aplica aquí, en la consulta de la sesión.
    """
    if not await es_tenant_demo(session, tenant_id):
        return []
    unidades = {a["id"]: a["nombre"] for a in await pasillo_organizacion.listar_areas(session, tenant_id)}
    personas = []
    for u in await pasillo_organizacion.listar_usuarios(session, tenant_id):
        roles = [r for r in u["roles"] if r["role"] in ORDEN_DE_ROLES]
        if not roles:
            continue
        rol = min(roles, key=lambda r: ORDEN_DE_ROLES.index(r["role"]))
        personas.append(PersonaDemo(
            usuario_id=u["id"], nombre=u["nombre"], rol=rol["role"], rol_etiqueta=ETIQUETAS[rol["role"]],
            unidad=unidades.get(rol["area_id"]) if rol["role"] == "responsable_area" else None))
    return personas


async def resolver_usuario(session: AsyncSession, vendedor_sub: str, ahora: datetime | None = None) -> PersonaDemo:
    """`sub` verificado ⟹ persona activa; 401 `DEMO_VENCIDA` si la sesión no es válida."""
    ahora = ahora or datetime.now(timezone.utc)
    sesion = await sesion_vigente(session, vendedor_sub, ahora)
    tenant = sesion.tenant_ids[0]
    persona = next((p for p in await personas_del_tenant(session, tenant) if p.usuario_id == sesion.persona_usuario_id), None)
    if persona is None:
        raise ErrorDemo(DEMO_VENCIDA)
    if sesion.ultima_actividad is None or ahora - sesion.ultima_actividad >= timedelta(seconds=SEGUNDOS_ENTRE_RENOVACIONES):
        await sesiones_repo.renovar_actividad(session, sesion.id, ahora)
    return persona
