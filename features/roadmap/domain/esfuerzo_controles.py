# ¤roadmap ¤arbitro
"""Prioridad y horas por nivel de control, y el plan cifrado (RM-26).

Las horas son ESTIMADO: un dato de negocio provisional que el propietario puede afinar por control.
La escala de niveles es la del diagnóstico (1 a 5); con nivel 4 o 5 el control no genera tarea.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

PRIORIDAD_POR_NIVEL: dict[int, str] = {1: "critica", 2: "alta", 3: "media"}
HORAS_POR_PRIORIDAD: dict[str, int] = {"critica": 40, "alta": 24, "media": 16}  # ESTIMADO
ORDEN_OLAS: tuple[str, ...] = ("critica", "alta", "media")
NIVEL_PROYECTADO = 4


def prioridad_de_nivel(nivel: int | None) -> str | None:
    """Prioridad del control según su nivel asignado; None si no genera tarea (nivel 4 o 5, o sin nivel)."""
    return PRIORIDAD_POR_NIVEL.get(nivel) if nivel is not None else None


@dataclass(frozen=True)
class ControlCifrado:
    control_ref: str
    nivel: int
    prioridad: str
    horas: int


@dataclass(frozen=True)
class OlaCifrada:
    prioridad: str
    controles: tuple[ControlCifrado, ...]
    horas: int
    inicio: date
    fin: date


@dataclass(frozen=True)
class PlanCifrado:
    olas: tuple[OlaCifrada, ...]
    score_objetivo: float
