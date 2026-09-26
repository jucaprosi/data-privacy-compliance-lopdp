"""Modelos de dominio del Módulo 4: Cockpit del DPD/DPO."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid

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

@dataclass
class DictamenDPO:
    id: str = field(default_factory=gen_id)
    tenant_id: str = ""
    dpo_id: str = ""
    tipo: TipoDictamenDPO = TipoDictamenDPO.OPINION_CONSULTIVA
    asunto: str = ""
    referencia_normativa: str = "" # ej. Art. 48 LOPDP, Res. 2025-0028
    cuerpo: str = ""
    fecha_emision: datetime = field(default_factory=utc_now)
    acuse_recibo_alta_direccion: bool = False
    fecha_acuse: datetime = None
    es_vinculante: bool = False # Doctrina: Siempre no vinculante por ley
