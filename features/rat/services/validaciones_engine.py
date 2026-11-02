# ¤rat ¤hallazgos ¤rbac-tenant
"""Efectos de guardar una ficha RAT (RAT-05): versión y hallazgos, en la transacción del guardado.

Los hallazgos van a la sala `roadmap` por `app_core.pasillo.roadmap` (ADPA §3): `rat` no importa otra sala y
`roadmap` ya depende de `rat`. Contrato: governance/especificaciones/RAT-05.md §3.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.pasillo import roadmap as pasillo_roadmap
from features.rat.domain.models import ActividadRAT
from features.rat.domain.validaciones import (
    CONTROL_RAT,
    DIMENSION_RAT,
    ResultadoRegla,
    evaluar_reglas,
    origen_ref_regla,
)
from features.rat.services.versiones_engine import registrar_version

CERRADO = "cerrado"


def _claves(tratamiento_id: str, reglas: list[ResultadoRegla]) -> dict[str, ResultadoRegla]:
    return {origen_ref_regla(tratamiento_id, r.codigo): r for r in reglas}


async def _hallazgos_de_reglas(session: AsyncSession, tenant_id: str, user_id: str, claves) -> list:
    """Hallazgos de las reglas de la ficha, por severidad. El origen `rat` lo comparten otros productores."""
    hallazgos = await pasillo_roadmap.listar_hallazgos_rat(session, tenant_id, user_id)
    return [h for h in hallazgos if h.origen_ref in claves]


async def _sincronizar_hallazgos(session: AsyncSession, actividad: ActividadRAT, user_id: str) -> None:
    """R2: una regla incumplida tiene un hallazgo vigente; una regla cumplida, ninguno."""
    tenant_id = actividad.tenant_id
    reglas = _claves(actividad.id, evaluar_reglas(actividad))
    previos = {
        h.origen_ref: h for h in await _hallazgos_de_reglas(session, tenant_id, user_id, reglas)
    }
    for clave, regla in reglas.items():
        previo = previos.get(clave)
        if regla.cumple:
            if previo is not None and previo.estado != CERRADO:
                await pasillo_roadmap.cerrar_hallazgo(session, tenant_id, user_id, previo.id)
        elif previo is None:
            await pasillo_roadmap.registrar_hallazgo_rat(
                session, tenant_id, user_id, clave, regla.severidad,
                f"{actividad.codigo} · {regla.mensaje}", CONTROL_RAT, DIMENSION_RAT,
            )
        elif previo.estado == CERRADO:
            await pasillo_roadmap.reabrir_hallazgo(session, tenant_id, user_id, previo.id)


async def tras_guardar_ficha(session: AsyncSession, actividad: ActividadRAT, user_id: str | None) -> None:
    """El hallazgo y su auditoría exigen un usuario real; un guardado sin autor (fuera de la API) solo versiona."""
    await registrar_version(session, actividad, user_id)
    if user_id:
        await _sincronizar_hallazgos(session, actividad, user_id)


async def tras_baja_ficha(session: AsyncSession, actividad: ActividadRAT, user_id: str | None) -> None:
    """La ficha dada de baja ya no se puede corregir: sus hallazgos se cierran y sus versiones se conservan."""
    if not user_id:
        return
    claves = _claves(actividad.id, evaluar_reglas(actividad))
    for hallazgo in await _hallazgos_de_reglas(session, actividad.tenant_id, user_id, claves):
        if hallazgo.estado != CERRADO:
            await pasillo_roadmap.cerrar_hallazgo(session, actividad.tenant_id, user_id, hallazgo.id)


async def validar_ficha(session: AsyncSession, actividad: ActividadRAT, user_id: str) -> dict:
    """Estado actual de las reglas y el hallazgo vigente de mayor severidad de la ficha."""
    reglas = evaluar_reglas(actividad)
    hallazgos = await _hallazgos_de_reglas(
        session, actividad.tenant_id, user_id, _claves(actividad.id, reglas)
    )
    vigente = next((h for h in hallazgos if h.estado != CERRADO), None)
    return {
        "reglas": [{"codigo": r.codigo, "cumple": r.cumple, "mensaje": r.mensaje} for r in reglas],
        "hallazgo_id": vigente.id if vigente else None,
    }
