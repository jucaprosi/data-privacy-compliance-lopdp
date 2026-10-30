# ¤controles-periodicos ¤auditoria-capa
"""Control periódico (CAPA-02): qué se revisa, cada cuánto, quién responde y cuándo toca.

Contrato: governance/especificaciones/CAPA-02.md. Dominio puro: fechas y reglas, sin base de datos.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# Ecuador continental no tiene horario de verano; el desfase fijo evita depender de tzdata en Windows.
ZONA_GUAYAQUIL = timezone(timedelta(hours=-5), "America/Guayaquil")
NOMBRE_MAX = 200
MOTIVO_MAX = 500
NOTA_MAX = 2000


class FrecuenciaControl(str, Enum):
    mensual = "mensual"
    trimestral = "trimestral"
    semestral = "semestral"
    anual = "anual"


class EstadoControl(str, Enum):
    vigente = "vigente"
    vencido = "vencido"
    retirado = "retirado"


MESES_POR_FRECUENCIA = {
    FrecuenciaControl.mensual.value: 1,
    FrecuenciaControl.trimestral.value: 3,
    FrecuenciaControl.semestral.value: 6,
    FrecuenciaControl.anual.value: 12,
}


def ahora_guayaquil() -> datetime:
    return datetime.now(ZONA_GUAYAQUIL)


def hoy_guayaquil() -> date:
    return ahora_guayaquil().date()


def sumar_meses(fecha: date, meses: int) -> date:
    """Mismo día del mes; si ese mes no lo tiene, el último día (R1)."""
    indice = fecha.year * 12 + fecha.month - 1 + meses
    anio, mes = indice // 12, indice % 12 + 1
    return date(anio, mes, min(fecha.day, calendar.monthrange(anio, mes)[1]))


def siguiente_verificacion(verificado_en: date, frecuencia: str) -> date:
    return sumar_meses(verificado_en, MESES_POR_FRECUENCIA[frecuencia])


def clave_vencimiento(control_id: str, proxima_verificacion: date) -> str:
    """Clave de origen del hallazgo (R4): cada vencimiento de un control es un hecho distinto."""
    return f"{control_id}:{proxima_verificacion.isoformat()}"


class CrearControlEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nombre: str = Field(min_length=1, max_length=NOMBRE_MAX)
    control_ref: Optional[str] = Field(default=None, pattern=r"^P([1-9]|[1-7][0-9]|80)$")
    frecuencia: Literal["mensual", "trimestral", "semestral", "anual"]
    responsable_user_id: str = Field(min_length=1)
    proxima_verificacion: date


class VerificarControlEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    evidencia_sha256: Optional[str] = None
    nota: Optional[str] = Field(default=None, max_length=NOTA_MAX)


class RetirarControlEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    motivo: str = Field(min_length=1, max_length=MOTIVO_MAX)


@dataclass(frozen=True)
class ControlPeriodico:
    id: str
    nombre: str
    control_ref: Optional[str]
    frecuencia: str
    responsable_user_id: str
    proxima_verificacion: date
    estado: str
    hallazgo_vigente_id: Optional[str]
    ultima_verificacion_en: Optional[datetime]

    def a_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "control_ref": self.control_ref,
            "frecuencia": self.frecuencia,
            "responsable_user_id": self.responsable_user_id,
            "proxima_verificacion": self.proxima_verificacion.isoformat(),
            "estado": self.estado,
            "hallazgo_vigente_id": self.hallazgo_vigente_id,
            "ultima_verificacion_en": self.ultima_verificacion_en.isoformat() if self.ultima_verificacion_en else None,
        }


@dataclass(frozen=True)
class VerificacionControl:
    id: str
    control_id: str
    verificado_por: str
    verificado_en: datetime
    evidencia_sha256: Optional[str]
    nota: Optional[str]

    def a_dict(self) -> dict:
        return {
            "id": self.id,
            "control_id": self.control_id,
            "verificado_por": self.verificado_por,
            "verificado_en": self.verificado_en.isoformat(),
            "evidencia_sha256": self.evidencia_sha256,
            "nota": self.nota,
        }


@dataclass(frozen=True)
class ResultadoVencimiento:
    vencidos: int
    hallazgos_creados: int

    def a_dict(self) -> dict:
        return {"vencidos": self.vencidos, "hallazgos_creados": self.hallazgos_creados}
