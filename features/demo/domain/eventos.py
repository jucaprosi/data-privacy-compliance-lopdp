# -*- coding: utf-8 -*-
# ¤demo
"""Eventos de auditoría de la demo (invariante 61): vendedor real, persona y hora."""
from __future__ import annotations

from enum import Enum


class EventoDemo(str, Enum):
    DEMO_INICIADA = "DEMO_INICIADA"
    DEMO_CAMBIO_PERSONA = "DEMO_CAMBIO_PERSONA"
    DEMO_TERMINADA = "DEMO_TERMINADA"
    DEMO_VENCIDA = "DEMO_VENCIDA"
