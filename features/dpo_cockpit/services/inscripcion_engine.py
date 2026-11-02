"""Inscripción del delegado ante la SPDP: registro por organización con historial solo de alta. ¤dpo-informe-anual

El tenant y quien registra llegan del contexto de la sesión (lo resuelve el router), nunca del
cuerpo. Una entrada nunca se edita ni se borra: corregir es registrar otra, y la vigente es la
última. Si la organización no figura inscrita, la fecha y el trámite no se guardan.
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from app_core.errors import CodigoErrorNegocio
from features.dpo_cockpit.domain.inscripcion import (
    InscripcionSPDP,
    dpo_inscripciones,
    gen_id,
)

DPO_INSCRIPCION_INVALIDA = CodigoErrorNegocio(
    codigo="DPO_INSCRIPCION_INVALIDA",
    status_code=422,
    mensaje_defecto="Los datos de la inscripción ante la SPDP no son válidos.",
    action_required=None,
)

LONGITUD_MAX_TRAMITE = 60


def normalizar_inscripcion(
    inscrito: bool,
    fecha_inscripcion: Optional[date],
    numero_tramite: Optional[str],
    hoy: Optional[date] = None,
) -> tuple[Optional[date], Optional[str]]:
    """Devuelve (fecha, trámite) coherentes con `inscrito` o lanza ErrorNegocio."""
    if not inscrito:
        return None, None
    tramite = (numero_tramite or "").strip()
    if fecha_inscripcion is None:
        raise ErrorNegocio(DPO_INSCRIPCION_INVALIDA, detail="Indica la fecha de inscripción.")
    if not tramite:
        raise ErrorNegocio(DPO_INSCRIPCION_INVALIDA, detail="Indica el número de trámite.")
    if len(tramite) > LONGITUD_MAX_TRAMITE:
        raise ErrorNegocio(
            DPO_INSCRIPCION_INVALIDA,
            detail=f"El número de trámite admite hasta {LONGITUD_MAX_TRAMITE} caracteres.",
        )
    if fecha_inscripcion > (hoy or date.today()):
        raise ErrorNegocio(
            DPO_INSCRIPCION_INVALIDA, detail="La fecha de inscripción no puede ser futura."
        )
    return fecha_inscripcion, tramite


def _fila_a_inscripcion(fila) -> InscripcionSPDP:
    return InscripcionSPDP(
        id=fila["id"],
        tenant_id=fila["tenant_id"],
        inscrito=bool(fila["inscrito"]),
        fecha_inscripcion=fila["fecha_inscripcion"],
        numero_tramite=fila["numero_tramite"],
        registrado_por=fila["registrado_por"],
        registrado_at=fila["registrado_at"],
        orden=fila["orden"],
    )


async def registrar_inscripcion(
    session: AsyncSession,
    tenant_id: str,
    registrado_por: str,
    inscrito: bool,
    fecha_inscripcion: Optional[date],
    numero_tramite: Optional[str],
) -> InscripcionSPDP:
    """Agrega una entrada al historial de la organización y la devuelve tal como quedó."""
    fecha, tramite = normalizar_inscripcion(inscrito, fecha_inscripcion, numero_tramite)
    nueva_id = gen_id()
    await session.execute(
        insert(dpo_inscripciones).values(
            id=nueva_id,
            tenant_id=tenant_id,
            inscrito=inscrito,
            fecha_inscripcion=fecha,
            numero_tramite=tramite,
            registrado_por=registrado_por,
        )
    )
    fila = (
        await session.execute(
            select(dpo_inscripciones).where(
                dpo_inscripciones.c.id == nueva_id,
                dpo_inscripciones.c.tenant_id == tenant_id,
            )
        )
    ).mappings().one()
    return _fila_a_inscripcion(fila)


async def historial_inscripcion(session: AsyncSession, tenant_id: str) -> List[InscripcionSPDP]:
    """Entradas de la organización, de la más reciente a la más antigua."""
    filas = (
        await session.execute(
            select(dpo_inscripciones)
            .where(dpo_inscripciones.c.tenant_id == tenant_id)
            .order_by(dpo_inscripciones.c.orden.desc())
        )
    ).mappings().all()
    return [_fila_a_inscripcion(f) for f in filas]


async def inscripcion_vigente(session: AsyncSession, tenant_id: str) -> Optional[InscripcionSPDP]:
    """La última entrada registrada, o None si la organización nunca declaró nada."""
    historial = await historial_inscripcion(session, tenant_id)
    return historial[0] if historial else None
