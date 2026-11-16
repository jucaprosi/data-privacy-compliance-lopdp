# -*- coding: utf-8 -*-
# ¤demo ¤seguridad ¤rbac-tenant ¤adpa
"""DEMO-01: personas de la demo y «Ver como» (FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md §1.2, invariante 61).

El servidor decide quién es la persona activa; el navegador solo la pide. `cambiar_persona` acepta únicamente
personas del tenant `es_demo` de la sesión del vendedor (si no, 403 `DEMO_PERSONA_AJENA`) y deja un evento
`DEMO_CAMBIO_PERSONA` con el vendedor real, la persona y la hora. El correo y el `sub` del vendedor van en la
auditoría y nunca en una respuesta.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.db.session import fijar_contexto_rls
from features.demo.domain.contrato import EstadoDemo
from features.demo.domain.errores import DEMO_PERSONA_AJENA, DEMO_VENCIDA, ErrorDemo
from features.demo.domain.eventos import EventoDemo
from features.demo.domain.personas import PersonaDemo, ordenar
from features.demo.domain.sesion import MINUTOS_INACTIVIDAD
from features.demo.repo import sesiones_repo
from features.demo.services.resolutor_engine import ENTIDAD_SESION, personas_del_tenant, sesion_vigente


async def listar_personas(session: AsyncSession, vendedor_sub: str, ahora: datetime | None = None) -> list[PersonaDemo]:
    """Las personas del tenant de la sesión vigente del vendedor, en el orden fijo del ciclo."""
    sesion = await sesion_vigente(session, vendedor_sub, ahora)
    return ordenar(await personas_del_tenant(session, sesion.tenant_ids[0]))


async def estado(session: AsyncSession, vendedor_sub: str, ahora: datetime | None = None) -> EstadoDemo:
    """Estado de la demo activa: organización ficticia, persona activa, personas y vencimiento."""
    sesion = await sesion_vigente(session, vendedor_sub, ahora)
    tenant = sesion.tenant_ids[0]
    personas = ordenar(await personas_del_tenant(session, tenant))
    activa = next((p for p in personas if p.usuario_id == sesion.persona_usuario_id), None)
    if activa is None:
        raise ErrorDemo(DEMO_VENCIDA)
    nombre = (await session.execute(text("SELECT nombre_comercial FROM tenants WHERE id = :t"), {"t": tenant})).scalar_one()
    vence = sesion.ultima_actividad + timedelta(minutes=MINUTOS_INACTIVIDAD) if sesion.ultima_actividad else None
    return EstadoDemo(tenant_id=tenant, nombre_organizacion=nombre, persona_activa=activa,
                      personas=tuple(personas), vence_en=vence)


async def cambiar_persona(
    session: AsyncSession, vendedor_sub: str, persona_usuario_id: str, ahora: datetime | None = None
) -> PersonaDemo:
    """Cambia la persona activa; 403 `DEMO_PERSONA_AJENA` si no es del tenant `es_demo` de la sesión."""
    ahora = ahora or datetime.now(timezone.utc)
    sesion = await sesion_vigente(session, vendedor_sub, ahora)
    tenant = sesion.tenant_ids[0]
    persona = next((p for p in await personas_del_tenant(session, tenant) if p.usuario_id == persona_usuario_id), None)
    if persona is None:
        raise ErrorDemo(DEMO_PERSONA_AJENA)
    await sesiones_repo.renovar_actividad(session, sesion.id, ahora, persona.usuario_id)
    await fijar_contexto_rls(session, tenant)
    await registrar_evento(
        session, tenant, ENTIDAD_SESION, sesion.id, EventoDemo.DEMO_CAMBIO_PERSONA.value, None,
        {"vendedor_sub": sesion.vendedor_sub, "vendedor_email": sesion.vendedor_email,
         "persona_usuario_id": persona.usuario_id, "rol": persona.rol, "hora": ahora.isoformat()},
    )
    return persona
