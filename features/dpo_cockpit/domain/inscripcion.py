"""Dominio de la inscripción del delegado ante la SPDP (DPO-02). ¤dpo-informe-anual"""
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional
import uuid

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, MetaData, String, Table


def gen_id() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class InscripcionSPDP:
    """Una entrada del historial: lo declarado en un momento. La vigente es la última."""

    id: str = field(default_factory=gen_id)
    tenant_id: str = ""
    inscrito: bool = False
    fecha_inscripcion: Optional[date] = None
    numero_tramite: Optional[str] = None
    registrado_por: str = ""
    registrado_at: Optional[datetime] = None
    orden: Optional[int] = None


# Metadatos locales de la sala: no crean tablas ni abren conexiones.
dpo_inscripciones = Table(
    "dpo_inscripciones",
    MetaData(),
    Column("orden", BigInteger, nullable=False),
    Column("id", String, primary_key=True),
    Column("tenant_id", String, nullable=False),
    Column("inscrito", Boolean, nullable=False),
    Column("fecha_inscripcion", Date, nullable=True),
    Column("numero_tramite", String(60), nullable=True),
    Column("registrado_por", String, nullable=False),
    Column("registrado_at", DateTime(timezone=True), nullable=False),
)
