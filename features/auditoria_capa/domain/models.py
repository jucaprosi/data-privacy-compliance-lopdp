"""Modelos de dominio del Módulo 3: Auditoría y Planes de Acción (CAPA)."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid

from sqlalchemy import Column, DateTime, MetaData, String, Table, Text


def gen_id() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SeveridadHallazgo(str, Enum):
    OBSERVACION = "OBSERVACION"
    NO_CONFORMIDAD_MENOR = "NO_CONFORMIDAD_MENOR"
    NO_CONFORMIDAD_MAYOR = "NO_CONFORMIDAD_MAYOR"
    VULNERABILIDAD_CRITICA = "VULNERABILIDAD_CRITICA"


class EstadoCAPA(str, Enum):
    ABIERTO = "ABIERTO"
    EN_REMEDIACION = "EN_REMEDIACION"
    PENDIENTE_VERIFICACION = "PENDIENTE_VERIFICACION"
    CERRADO_VERIFICADO = "CERRADO_VERIFICADO"


@dataclass
class TicketCAPA:
    id: str = field(default_factory=gen_id)
    tenant_id: str = ""
    control_id: str = ""
    severidad: SeveridadHallazgo = SeveridadHallazgo.NO_CONFORMIDAD_MENOR
    descripcion_hallazgo: str = ""
    causa_raiz: str = ""
    accion_correctiva: str = ""
    responsable_implementacion_id: str = ""
    creado_por: str = ""
    auditor_verificador_id: Optional[str] = None
    estado: EstadoCAPA = EstadoCAPA.ABIERTO
    evidencia_cierre_id: Optional[str] = None
    snapshot_normativo: str = "LOPDP-Ecuador-2021"
    fecha_creacion: datetime = field(default_factory=utc_now)
    fecha_cierre: Optional[datetime] = None


# Metadatos locales de la sala: no crean tablas ni abren conexiones.
capa_tickets = Table(
    "capa_tickets",
    MetaData(),
    Column("id", String, primary_key=True),
    Column("tenant_id", String, nullable=False),
    Column("control_id", String(128), nullable=False),
    Column("severidad", String(64), nullable=False),
    Column("descripcion_hallazgo", Text, nullable=False),
    Column("causa_raiz", Text, nullable=False),
    Column("accion_correctiva", Text, nullable=False),
    Column("responsable_implementacion_id", String, nullable=False),
    Column("creado_por", String, nullable=False),
    Column("auditor_verificador_id", String, nullable=True),
    Column("estado", String(64), nullable=False),
    Column("evidencia_cierre_id", String, nullable=True),
    Column("snapshot_normativo", String(128), nullable=False),
    Column("fecha_creacion", DateTime(timezone=True), nullable=False),
    Column("fecha_cierre", DateTime(timezone=True), nullable=True),
)
