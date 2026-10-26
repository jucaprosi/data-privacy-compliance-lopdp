# -*- coding: utf-8 -*-
"""Sensor persistente de deriva de la EIPD; la transacción pertenece al llamador."""
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from features.rat.services.eipd_engine import rat_eipd

# Reglas de deriva de la EIPD aprobada (Aporte 29), las mismas del sensor en memoria anterior:
# 1. el volumen de titulares crece más de un 25 % respecto al de la aprobación;
# 2. aparece la categoría BIOMETRICOS, que no estaba al aprobarla.
UMBRAL_DERIVA_VOLUMEN = 0.25
CATEGORIA_BIOMETRICOS = "BIOMETRICOS"


async def evaluar_deriva_riesgo_eipd(
    session: AsyncSession, tenant_id: str, rat_id: str, volumen_actual: int, categorias_actuales: list[str],
) -> bool:
    """Marca la EIPD aprobada como «requiere actualización» si el tratamiento derivó."""
    fila = (await session.execute(
        select(rat_eipd.c.id, rat_eipd.c.volumen_titulares_aprobacion, rat_eipd.c.categorias_datos_aprobacion).where(
            rat_eipd.c.tenant_id == tenant_id,
            rat_eipd.c.rat_id == rat_id,
            rat_eipd.c.estado == "APROBADA",
        ).with_for_update()
    )).first()
    if not fila:
        return False
    crece = volumen_actual > fila.volumen_titulares_aprobacion * (1 + UMBRAL_DERIVA_VOLUMEN)
    biometricos_nuevos = (
        CATEGORIA_BIOMETRICOS in categorias_actuales
        and CATEGORIA_BIOMETRICOS not in (fila.categorias_datos_aprobacion or [])
    )
    deriva = crece or biometricos_nuevos
    if deriva:
        await session.execute(update(rat_eipd).where(
            rat_eipd.c.id == fila.id, rat_eipd.c.tenant_id == tenant_id,
        ).values(estado="REQUIERE_ACTUALIZACION"))
    return deriva
