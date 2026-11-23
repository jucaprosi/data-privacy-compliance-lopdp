# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤domain ¤evidencias ¤rbac-tenant
"""Entidades de dominio para la sala Formación (FOR-01)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal


@dataclass
class ContenidoFormativo:
    id: str
    tenant_id: str
    titulo: str
    tipo: Literal["pdf", "video"]
    referencia: str
    creado_por: str
    creado_en: datetime | str
    preguntas: list[PreguntaFormativa] = field(default_factory=list)


@dataclass
class PreguntaFormativa:
    id: str
    tenant_id: str
    contenido_id: str
    orden: int
    enunciado: str
    opciones: list[str]
    correcta: int


@dataclass
class AccionFormativa:
    id: str
    tenant_id: str
    contenido_id: str
    nombre: str
    inicio: date | str
    fin: date | str
    nota_minima: float
    creado_por: str
    participaciones: list[ParticipacionFormativa] = field(default_factory=list)


@dataclass
class ParticipacionFormativa:
    id: str
    tenant_id: str
    accion_id: str
    persona_id: str
    enviado_en: datetime | str
    iniciado_en: datetime | str | None = None
    terminado_en: datetime | str | None = None
    nota: float | None = None
    diploma_sha256: str | None = None
