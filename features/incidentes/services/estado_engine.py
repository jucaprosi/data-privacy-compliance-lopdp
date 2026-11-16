# ¤incidentes ¤rbac-tenant ¤seguridad
"""Cambios de estado del incidente y contador de abiertos en PostgreSQL (INC-03).

Los eventos solo se agregan (lopdp_app tiene SELECT e INSERT). Dos cambios simultáneos del mismo
incidente no se serializan con candado: los separa UNIQUE (incidente_id, secuencia) y el segundo
recibe el conflicto. La huella de `incidentes` no cambia: el estado no entra en su contenido.
"""
from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.db.session import fijar_contexto_rls
from features.incidentes.domain.estado import (
    ABIERTO,
    CERRADO,
    CIERRE,
    DECISION_PENDIENTE,
    REAPERTURA,
    EstadoIncidente,
    IncidenteNoEncontrado,
    TransicionInvalida,
    estado_desde_evento,
)
from features.incidentes.services.asistente_engine import tiene_decision

_ULTIMO_EVENTO = (
    "SELECT secuencia, tipo, motivo, decision_notificacion, registrado_en "
    "FROM incidentes_eventos_estado WHERE incidente_id = :i AND tenant_id = :t "
    "ORDER BY secuencia DESC LIMIT 1"
)


async def estado_de(session: AsyncSession, tenant_id: str, incidente_id: str) -> EstadoIncidente:
    """Estado actual de un incidente de la organización (el contexto RLS ya está fijado)."""
    existe = (
        await session.execute(
            text("SELECT 1 FROM incidentes WHERE id = :i AND tenant_id = :t"),
            {"i": incidente_id, "t": tenant_id},
        )
    ).first()
    if existe is None:
        raise IncidenteNoEncontrado(incidente_id)
    evento = (await session.execute(text(_ULTIMO_EVENTO), {"i": incidente_id, "t": tenant_id})).mappings().first()
    return await _marca_veraz(session, tenant_id, estado_desde_evento(incidente_id, dict(evento) if evento else None))


async def _marca_veraz(session: AsyncSession, tenant_id: str, estado: EstadoIncidente) -> EstadoIncidente:
    """INC-04 R2: una marca 'pendiente' anterior se entrega solo si el incidente sigue sin sección 7.

    La fila guardada no se toca (historia inmutable, sin backfill).
    """
    if estado.decision_notificacion == DECISION_PENDIENTE and await tiene_decision(
        session, tenant_id, estado.incidente_id
    ):
        return replace(estado, decision_notificacion=None)
    return estado


async def estados_de(session: AsyncSession, tenant_id: str, user_id: str) -> dict[str, EstadoIncidente]:
    """Estado de todos los incidentes de la organización, por id."""
    await fijar_contexto_rls(session, tenant_id, user_id)
    filas = (
        await session.execute(
            text(
                "SELECT i.id AS incidente_id, e.secuencia, e.tipo, e.motivo, e.decision_notificacion, e.registrado_en "
                "FROM incidentes i LEFT JOIN LATERAL ("
                "  SELECT secuencia, tipo, motivo, decision_notificacion, registrado_en "
                "  FROM incidentes_eventos_estado x WHERE x.incidente_id = i.id AND x.tenant_id = i.tenant_id "
                "  ORDER BY x.secuencia DESC LIMIT 1"
                ") e ON TRUE WHERE i.tenant_id = :t"
            ),
            {"t": tenant_id},
        )
    ).mappings().all()
    return {
        f["incidente_id"]: await _marca_veraz(
            session, tenant_id, estado_desde_evento(f["incidente_id"], dict(f) if f["tipo"] is not None else None)
        )
        for f in filas
    }


async def _cambiar_estado(
    session: AsyncSession, tenant_id: str, user_id: str, incidente_id: str, *, tipo: str, motivo: str
) -> EstadoIncidente:
    await fijar_contexto_rls(session, tenant_id, user_id)
    incidente = (
        await session.execute(
            text("SELECT afecta_datos_personales FROM incidentes WHERE id = :i AND tenant_id = :t"),
            {"i": incidente_id, "t": tenant_id},
        )
    ).mappings().first()
    if incidente is None:
        raise IncidenteNoEncontrado(incidente_id)
    actual = await estado_de(session, tenant_id, incidente_id)
    if tipo == CIERRE and actual.estado == CERRADO:
        raise TransicionInvalida("El incidente ya está cerrado.", "INCIDENTE_YA_CERRADO")
    if tipo == REAPERTURA and actual.estado == ABIERTO:
        raise TransicionInvalida("El incidente ya está abierto.", "INCIDENTE_YA_ABIERTO")

    # INC-04 R1: ningún evento nuevo lleva marca. Un cierre con datos personales ya tiene la sección 7
    # (precondición de INC-02, R7), así que «pendiente» sería falso.
    decision = None
    secuencia = actual.ultima_secuencia + 1
    try:
        async with session.begin_nested():
            await session.execute(
                text(
                    "INSERT INTO incidentes_eventos_estado "
                    "(id, tenant_id, incidente_id, secuencia, tipo, motivo, decision_notificacion, "
                    "registrado_por, registrado_en) VALUES "
                    "(:id, :t, :i, :s, :tipo, :motivo, :decision, :u, :en)"
                ),
                {
                    "id": str(uuid.uuid4()), "t": tenant_id, "i": incidente_id, "s": secuencia, "tipo": tipo,
                    "motivo": motivo, "decision": decision, "u": user_id, "en": datetime.now(timezone.utc),
                },
            )
    except IntegrityError as exc:
        if "uq_incidentes_eventos_secuencia" in str(exc.orig):
            raise TransicionInvalida(
                "Otro cambio de estado del incidente se registró al mismo tiempo.", "INCIDENTE_CAMBIO_CONCURRENTE"
            ) from exc
        raise
    await registrar_evento(
        session, tenant_id, "incidente", incidente_id,
        "incidente_cerrado" if tipo == CIERRE else "incidente_reabierto", user_id,
        {"secuencia": secuencia},
    )
    return await estado_de(session, tenant_id, incidente_id)


async def cerrar_incidente(
    session: AsyncSession, tenant_id: str, user_id: str, incidente_id: str, motivo: str
) -> EstadoIncidente:
    return await _cambiar_estado(session, tenant_id, user_id, incidente_id, tipo=CIERRE, motivo=motivo)


async def reabrir_incidente(
    session: AsyncSession, tenant_id: str, user_id: str, incidente_id: str, motivo: str
) -> EstadoIncidente:
    return await _cambiar_estado(session, tenant_id, user_id, incidente_id, tipo=REAPERTURA, motivo=motivo)


async def contar_abiertos(session: AsyncSession, tenant_id: str) -> int:
    """Incidentes de la organización sin evento o cuyo último evento es una reapertura."""
    n = (
        await session.execute(
            text(
                "SELECT count(*) FROM incidentes i WHERE i.tenant_id = :t AND COALESCE(("
                "  SELECT e.tipo FROM incidentes_eventos_estado e "
                "  WHERE e.incidente_id = i.id AND e.tenant_id = i.tenant_id ORDER BY e.secuencia DESC LIMIT 1"
                "), 'reapertura') <> 'cierre'"
            ),
            {"t": tenant_id},
        )
    ).scalar_one()
    return int(n)
