# -*- coding: utf-8 -*-
# ¤adpa
# ¤demo
"""Compuerta pública de la sala demo (DEMO-00). Sus firmas son definitivas: nadie la edita después.

Cada función delega en el motor de su ficha con importación diferida; si el motor aún no existe,
lanza `NotImplementedError` con el id de la ficha. Otras salas entran por `app_core/pasillo/demo.py`.
"""
from __future__ import annotations

import importlib
from datetime import datetime
from types import ModuleType

from sqlalchemy.ext.asyncio import AsyncSession

from features.demo.domain import errores as _errores  # noqa: F401  (registra los códigos al importarse)
from features.demo.domain.contrato import EstadoDemo
from features.demo.domain.personas import PersonaDemo

__all__ = ["entrar", "terminar", "estado", "cambiar_persona", "resolver_usuario", "vencer_inactivas"]


def _motor(modulo: str, ficha: str) -> ModuleType:
    nombre = f"features.demo.services.{modulo}"
    try:
        return importlib.import_module(nombre)
    except ModuleNotFoundError as exc:
        if exc.name in (nombre, "features.demo.services"):
            raise NotImplementedError(f"Pendiente de {ficha}: features/demo/services/{modulo}.py") from exc
        raise


async def entrar(session: AsyncSession, vendedor_sub: str, vendedor_email: str) -> EstadoDemo:
    """Abre la demo del vendedor: copia la plantilla y arranca como administrador (DEMO-02)."""
    return await _motor("entrada_engine", "DEMO-02").entrar(session, vendedor_sub, vendedor_email)


async def terminar(session: AsyncSession, vendedor_sub: str) -> None:
    """Marca la sesión como vencida con motivo `terminar` (DEMO-02). Nunca borra (invariante 63)."""
    await _motor("cierre_engine", "DEMO-02").terminar(session, vendedor_sub)


async def estado(session: AsyncSession, vendedor_sub: str) -> EstadoDemo:
    """Estado de la demo activa del vendedor (DEMO-01)."""
    return await _motor("persona_engine", "DEMO-01").estado(session, vendedor_sub)


async def cambiar_persona(session: AsyncSession, vendedor_sub: str, persona_usuario_id: str) -> PersonaDemo:
    """Cambia la persona activa; 403 DEMO_PERSONA_AJENA si no es del tenant de la sesión (DEMO-01)."""
    return await _motor("persona_engine", "DEMO-01").cambiar_persona(session, vendedor_sub, persona_usuario_id)


async def resolver_usuario(session: AsyncSession, vendedor_sub: str, ahora: datetime | None = None) -> PersonaDemo:
    """Traduce el `sub` verificado a la persona activa; 401 DEMO_VENCIDA si venció (DEMO-01)."""
    return await _motor("resolutor_engine", "DEMO-01").resolver_usuario(session, vendedor_sub, ahora)


async def vencer_inactivas(session: AsyncSession, ahora: datetime | None = None) -> int:
    """Vence las sesiones sin actividad en 60 minutos; devuelve cuántas (DEMO-02)."""
    return await _motor("cierre_engine", "DEMO-02").vencer_inactivas(session, ahora)
