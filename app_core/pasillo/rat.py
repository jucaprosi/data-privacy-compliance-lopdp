# ¤adpa
"""Capacidades de la sala RAT para otras salas."""
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class ActividadResumen:
    id: str
    codigo: str
    nombre: str
    datos_sensibles: bool
    es_gran_escala: bool
    requiere_eipd: bool


async def listar_actividades_resumen(session: AsyncSession, tenant_id: str) -> list[ActividadResumen]:
    from features.rat import rat_service

    return [
        ActividadResumen(
            id=a.id,
            codigo=a.codigo,
            nombre=a.nombre,
            datos_sensibles=a.datos_sensibles,
            es_gran_escala=a.es_gran_escala,
            requiere_eipd=a.requiere_eipd,
        )
        for a in await rat_service.listar_actividades_rat(session, tenant_id)
    ]
