# -*- coding: utf-8 -*-
# ¤demo
"""Protocolo de copia desde la plantilla «Cooperativa Demo» (DEMO-03a…03f, FLUJOS §1.1).

Cada sala con datos en la plantilla implementa `clonar_desde_plantilla` en su pasillo. El
orquestador (DEMO-02) las llama en `ORDEN_DE_SALAS`: organización primero, porque produce el mapa
de personas y unidades que necesitan las demás. Cada una devuelve el mapa ampliado con sus ids.
"""
from __future__ import annotations

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

#: Tenant plantilla «Cooperativa Demo» que siembra DEMO-03 y del que copian las salas.
PLANTILLA_TENANT_ID = "demo-plantilla-cooperativa"

#: id en la plantilla → id en el tenant nuevo, acumulado sala a sala.
MapaIds = dict[str, str]

ORDEN_DE_SALAS: tuple[str, ...] = (
    "organizacion",
    "diagnostico",
    "roadmap",
    "biblioteca",
    "evidencias",
    "videovigilancia",
)


class ClonadorDePlantilla(Protocol):
    async def __call__(
        self, session: AsyncSession, origen: str, destino: str, mapa_ids: MapaIds
    ) -> MapaIds:
        """Copia los datos de la sala del tenant `origen` al `destino`; nunca escribe en `origen`."""
        ...
