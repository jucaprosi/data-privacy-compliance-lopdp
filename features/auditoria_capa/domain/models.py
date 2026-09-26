"""Modelos de dominio del Módulo 3: Auditorías y Acciones Correctivas (CAPA)."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid

def gen_id() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class SeveridadHallazgo(str, Enum):
    NO_CONFORMIDAD_MAYOR = "NO_CONFORMIDAD_MAYOR"
    NO_CONFORMIDAD_MENOR = "NO_CONFORMIDAD_MENOR"
    OBSERVACION = "OBSERVACION"
    OPORTUNIDAD_MEJORA = "OPORTUNIDAD_MEJORA"

class EstadoCAPA(str, Enum):
    ABIERTO = "ABIERTO"
    EN_IMPLEMENTACION = "EN_IMPLEMENTACION"
    PENDIENTE_VERIFICACION = "PENDIENTE_VERIFICACION"
    CERRADO_VERIFICADO = "CERRADO_VERIFICADO"
    RECHAZADO = "RECHAZADO"

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
    auditor_verificador_id: str = ""
    estado: EstadoCAPA = EstadoCAPA.ABIERTO
    evidencia_cierre_id: str = ""
    snapshot_normativo: str = ""
    fecha_creacion: datetime = field(default_factory=utc_now)
    fecha_cierre: datetime = None
