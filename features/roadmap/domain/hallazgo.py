# ¤roadmap ¤hallazgos ¤rbac-tenant
"""Hallazgo con origen (RM-21): lo que las salas productoras encuentran y solo `roadmap` convierte en tarea.

Contrato: governance/especificaciones/RM-21.md. Invariante: INV_LOPDP_SINGLE_ACTION_PLAN
(todo hallazgo que salió de `abierto` tiene exactamente una tarea con su origen en la hoja de ruta).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class OrigenHallazgo(str, Enum):
    diagnostico = "diagnostico"
    auditoria = "auditoria"
    eipd = "eipd"
    incidente = "incidente"
    tercero = "tercero"
    control_periodico = "control_periodico"
    # === RAT-05 ===
    rat = "rat"
    # === fin RAT-05 ===


class SeveridadHallazgo(str, Enum):
    critica = "critica"
    alta = "alta"
    media = "media"


class EstadoHallazgo(str, Enum):
    abierto = "abierto"
    en_tratamiento = "en_tratamiento"
    cerrado = "cerrado"


# Mismas expresiones que los CHECK de la migración 20261030_hallazgos (P1-P80, D01-D10).
PATRON_CONTROL = re.compile(r"^P([1-9]|[1-7][0-9]|80)$")
PATRON_DIMENSION = re.compile(r"^D(0[1-9]|10)$")
TITULO_MAX = 200
ORIGEN_REF_MAX = 120
DIMENSION_POR_DEFECTO = "D01"
MAX_IDS_CONVERSION = 100
MOTIVO_YA_CONVERTIDO = "YA_CONVERTIDO"

# Orden de presentación: crítica, alta, media.
ORDEN_SEVERIDAD = {"critica": 0, "alta": 1, "media": 2}


def validar_hallazgo(
    origen: str,
    origen_ref: str,
    severidad: str,
    titulo: str,
    control_ref: Optional[str],
    dimension: Optional[str],
) -> None:
    """Rechaza con ValueError lo que la base rechazaría con su CHECK (falla antes y con mensaje claro)."""
    OrigenHallazgo(origen)
    SeveridadHallazgo(severidad)
    if not origen_ref or len(origen_ref) > ORIGEN_REF_MAX:
        raise ValueError(f"origen_ref debe tener entre 1 y {ORIGEN_REF_MAX} caracteres")
    if not titulo or len(titulo) > TITULO_MAX:
        raise ValueError(f"titulo debe tener entre 1 y {TITULO_MAX} caracteres")
    if control_ref is not None and not PATRON_CONTROL.match(control_ref):
        raise ValueError("control_ref no pertenece al catálogo P1-P80")
    if dimension is not None and not PATRON_DIMENSION.match(dimension):
        raise ValueError("dimension no pertenece a D01-D10")


def origen_ref_diagnostico(resultado_id: str, pregunta_id: int) -> str:
    """Clave estable de una brecha del diagnóstico (regla R3): `<resultado_id>:P<pregunta_id>`."""
    return f"{resultado_id}:P{pregunta_id}"


@dataclass(frozen=True)
class Hallazgo:
    id: str
    origen: str
    origen_ref: str
    control_ref: Optional[str]
    dimension: Optional[str]
    severidad: str
    titulo: str
    descripcion: Optional[str]
    estado: str
    tarea_id: Optional[str]
    creado_en: datetime

    def a_dict(self) -> dict:
        return {
            "id": self.id,
            "origen": self.origen,
            "origen_ref": self.origen_ref,
            "control_ref": self.control_ref,
            "dimension": self.dimension,
            "severidad": self.severidad,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "estado": self.estado,
            "tarea_id": self.tarea_id,
            "creado_en": self.creado_en.isoformat(),
        }


@dataclass
class ResultadoRegistro:
    creados: int = 0
    existentes: int = 0


@dataclass
class ResultadoConversion:
    tareas: list[dict] = field(default_factory=list)
    omitidos: list[dict] = field(default_factory=list)


class ConvertirHallazgosEntrada(BaseModel):
    """Solo ids y ola: organización, autor, estado y fechas los pone el servidor."""

    model_config = ConfigDict(extra="forbid")

    hallazgo_ids: list[str] = Field(min_length=1, max_length=MAX_IDS_CONVERSION)
    wave_id: str = Field(min_length=1)
