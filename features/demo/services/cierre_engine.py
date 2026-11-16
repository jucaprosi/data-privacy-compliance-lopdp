# -*- coding: utf-8 -*-
# ¤demo
"""Cierre lógico de las demos (DEMO-02): terminar y vencer por inactividad. Nunca borra (invariante 63).

La purga física la hace el Cloud Run Job `purga-demo` (DEMO-05). No hace commit: lo hace quien abrió la
transacción.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.db.session import fijar_contexto_rls
from features.demo.domain.eventos import EventoDemo
from features.demo.domain.sesion import MINUTOS_INACTIVIDAD, MotivoFin, SesionDemo
from features.demo.repo import sesiones_repo

ENTIDAD = "demo_sesion"

_SQL_INACTIVAS = (
    "SELECT id FROM demo_sesiones WHERE estado = 'activa' AND ultima_actividad <= :limite "
    "ORDER BY ultima_actividad"
)


async def vencer(session: AsyncSession, sesion: SesionDemo, motivo: MotivoFin, ahora: datetime) -> None:
    """Marca la sesión vencida con su motivo y deja el evento de auditoría con el vendedor real."""
    await sesiones_repo.marcar_vencida(session, sesion.id, motivo, ahora)
    for tenant_id in sesion.tenant_ids:
        await fijar_contexto_rls(session, tenant_id, sesion.persona_usuario_id)
        evento = EventoDemo.DEMO_TERMINADA if motivo is MotivoFin.TERMINAR else EventoDemo.DEMO_VENCIDA
        await registrar_evento(
            session, tenant_id, ENTIDAD, sesion.id, evento.value, sesion.persona_usuario_id,
            {"motivo": motivo.value, "vendedor_email": sesion.vendedor_email},
        )


async def terminar(session: AsyncSession, vendedor_sub: str, ahora: datetime | None = None) -> None:
    """Vencimiento lógico con motivo `terminar`. Sin demo activa no hace nada (idempotente)."""
    ahora = ahora or datetime.now(timezone.utc)
    sesion = await sesiones_repo.obtener_activa(session, vendedor_sub)
    if sesion is not None:
        await vencer(session, sesion, MotivoFin.TERMINAR, ahora)


async def vencer_inactivas(session: AsyncSession, ahora: datetime | None = None) -> int:
    """Vence las activas con 60 minutos o más sin actividad (59 no, 60 sí); devuelve cuántas."""
    ahora = ahora or datetime.now(timezone.utc)
    limite = ahora - timedelta(minutes=MINUTOS_INACTIVIDAD)
    ids = [f[0] for f in (await session.execute(text(_SQL_INACTIVAS), {"limite": limite})).all()]
    for sesion_id in ids:
        fila = (await session.execute(
            text("SELECT vendedor_sub FROM demo_sesiones WHERE id = :i"), {"i": sesion_id})).one()
        sesion = await sesiones_repo.obtener_activa(session, fila[0])
        if sesion is not None:
            await vencer(session, sesion, MotivoFin.INACTIVIDAD, ahora)
    return len(ids)
