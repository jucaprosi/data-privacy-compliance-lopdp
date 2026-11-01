# ¤rat ¤rbac-tenant
"""Versiones inmutables de cada ficha RAT (RAT-05, R3); la transacción pertenece al llamador."""
from dataclasses import asdict
from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, func, insert, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from features.rat.domain.models import ActividadRAT

rat_versiones = Table(
    "rat_versiones", MetaData(),
    Column("id", String, primary_key=True),
    Column("tenant_id", String, nullable=False),
    Column("tratamiento_id", String, nullable=False),
    Column("numero", Integer, nullable=False),
    Column("contenido", JSONB, nullable=False),
    Column("creado_por", String),
    Column("creado_en", DateTime(timezone=True)),
)


async def registrar_version(session: AsyncSession, actividad: ActividadRAT, user_id: str | None) -> int:
    """Guarda la ficha completa como versión siguiente; el índice único rechaza dos números iguales."""
    ultima = (await session.execute(
        select(func.coalesce(func.max(rat_versiones.c.numero), 0)).where(
            rat_versiones.c.tenant_id == actividad.tenant_id,
            rat_versiones.c.tratamiento_id == actividad.id,
        )
    )).scalar_one()
    numero = ultima + 1
    await session.execute(insert(rat_versiones).values(
        id=str(uuid4()), tenant_id=actividad.tenant_id, tratamiento_id=actividad.id,
        numero=numero, contenido=asdict(actividad), creado_por=user_id,
    ))
    return numero


async def listar_versiones(session: AsyncSession, tenant_id: str, tratamiento_id: str) -> list[dict]:
    filas = (await session.execute(
        select(rat_versiones.c.numero, rat_versiones.c.creado_por, rat_versiones.c.creado_en).where(
            rat_versiones.c.tenant_id == tenant_id,
            rat_versiones.c.tratamiento_id == tratamiento_id,
        ).order_by(rat_versiones.c.numero)
    )).mappings().all()
    return [dict(f) for f in filas]


async def leer_version(session: AsyncSession, tenant_id: str, tratamiento_id: str, numero: int) -> dict | None:
    return (await session.execute(
        select(rat_versiones.c.contenido).where(
            rat_versiones.c.tenant_id == tenant_id,
            rat_versiones.c.tratamiento_id == tratamiento_id,
            rat_versiones.c.numero == numero,
        )
    )).scalar_one_or_none()
