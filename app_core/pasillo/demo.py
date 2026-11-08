# ¤adpa
# ¤demo
"""Capacidades de la sala demo para otras salas (pasillo central, ADPA §3).

Es el único camino de otras salas hacia la demo. Cada función importa la compuerta en su cuerpo;
aquí no hay lógica de negocio.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


async def resolver_usuario(session: AsyncSession, vendedor_sub: str, ahora: datetime | None = None) -> Any:
    """Persona activa de la demo del vendedor (gancho de autenticación, DEMO-08)."""
    from features.demo import demo_service

    return await demo_service.resolver_usuario(session, vendedor_sub, ahora)


async def vencer_inactivas(session: AsyncSession, ahora: datetime | None = None) -> int:
    """Vence las demos inactivas (tarea programada de operaciones)."""
    from features.demo import demo_service

    return await demo_service.vencer_inactivas(session, ahora)
