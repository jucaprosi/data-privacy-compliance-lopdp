# ¤domain ¤auditoria-capa
"""Entidades de dominio para la auditoría con grilla y actas por área (CAPA-04)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal
from uuid import UUID


@dataclass
class Auditoria:
    id: str
    tenant_id: str
    nombre: str
    alcance: list[str]  # Lista de area_ids
    equipo: list[str]   # Lista de user_ids con rol auditor
    estado: Literal["abierta", "cerrada"]
    creado_por: str
    creado_en: datetime | str
    cerrada_en: datetime | str | None = None
    filas: list[AuditoriaFila] = field(default_factory=list)


@dataclass
class AuditoriaFila:
    id: str
    tenant_id: str
    auditoria_id: str
    area_id: str
    control_ref: str
    declarado: int
    riesgo_inicial: int
    verificado: int | None = None
    evidencia_sha256: str | None = None
    riesgo_final: int | None = None
    revisado_por: str | None = None
    hallazgo_id: str | None = None


@dataclass
class AuditoriaActa:
    id: str
    tenant_id: str
    auditoria_id: str
    area_id: str
    evidencia_id: str
    acta_sha256: str
    firmada_por: str
    firmada_en: datetime | str


@dataclass
class AuditoriaVerificacionCierre:
    id: str
    tenant_id: str
    hallazgo_id: str
    accion_ref: str
    verificado_por: str
    resultado: Literal["conforme", "no_conforme"]
    motivo: str
    registrado_en: datetime | str
