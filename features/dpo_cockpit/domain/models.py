"""Modelos de dominio del Módulo 4: Cockpit del DPD/DPO y Bitácora Inviolable."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid

from sqlalchemy import Boolean, Column, DateTime, MetaData, String, Table, Text


def gen_id() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TipoDictamenDPO(str, Enum):
    OPINION_CONSULTIVA = "OPINION_CONSULTIVA"
    ADVERTENCIA_RIESGO = "ADVERTENCIA_RIESGO"
    RECOMENDACION_EIPD = "RECOMENDACION_EIPD"
    DICTAMEN_TRANSFERENCIA = "DICTAMEN_TRANSFERENCIA"
    AUDITORIA_INFORME = "AUDITORIA_INFORME"
    ALERTA_RIESGO_GRAVE = "ALERTA_RIESGO_GRAVE"
    VALIDACION_EIPD = "VALIDACION_EIPD"


TipoDictamen = TipoDictamenDPO


@dataclass
class DictamenDPO:
    id: str = field(default_factory=gen_id)
    tenant_id: str = ""
    dpo_id: str = ""
    tipo: TipoDictamenDPO = TipoDictamenDPO.OPINION_CONSULTIVA
    asunto: str = ""
    referencia_normativa: str = ""
    cuerpo: str = ""
    fecha_emision: datetime = field(default_factory=utc_now)
    acuse_recibo_alta_direccion: bool = False
    fecha_acuse: Optional[datetime] = None
    es_vinculante: bool = False  # Doctrina: Siempre no vinculante por ley (Art. 50 LOPDP)
    prev_hash: str = ""
    sha256_hash: str = ""
    acuse_por: Optional[str] = None


# Metadatos locales de la sala: no crean tablas ni abren conexiones.
dpo_dictamenes = Table(
    "dpo_dictamenes",
    MetaData(),
    Column("id", String, primary_key=True),
    Column("tenant_id", String, nullable=False),
    Column("dpo_id", String, nullable=False),
    Column("tipo", String(64), nullable=False),
    Column("asunto", Text, nullable=False),
    Column("referencia_normativa", Text, nullable=False),
    Column("cuerpo", Text, nullable=False),
    Column("fecha_emision", DateTime(timezone=True), nullable=False),
    Column("es_vinculante", Boolean, nullable=False),
    Column("prev_hash", String(64), nullable=False),
    Column("sha256_hash", String(64), nullable=False),
    Column("acuse_recibo_alta_direccion", Boolean, nullable=False),
    Column("acuse_por", String, nullable=True),
    Column("fecha_acuse", DateTime(timezone=True), nullable=True),
)
