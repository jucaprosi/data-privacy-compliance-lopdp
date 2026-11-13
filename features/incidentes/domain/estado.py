# ¤incidentes ¤rbac-tenant
"""Estado del incidente (INC-03): abierto o cerrado, como eventos que solo se agregan.

La bitácora `incidentes` es inmutable (huella encadenada): el estado no vive en ella. El estado actual
es el del último evento de `incidentes_eventos_estado`; sin eventos, el incidente está abierto.
Esta sala no calcula ni exige plazos para cerrar (REG-01).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

CIERRE = "cierre"
REAPERTURA = "reapertura"
ABIERTO = "abierto"
CERRADO = "cerrado"
MOTIVO_MINIMO = 10

# ESTIMADO: el cierre de un incidente con datos personales puede ir antes de que INC-02 registre la
# decisión de notificar; queda marcado mientras el plazo del art. 43 siga aplazado.
DECISION_PENDIENTE = "pendiente"


@dataclass(frozen=True)
class EstadoIncidente:
    incidente_id: str
    estado: str
    ultima_secuencia: int = 0
    decision_notificacion: str | None = None
    ultimo_motivo: str | None = None
    ultimo_cambio_en: datetime | None = None

    def a_salida(self) -> dict:
        return {
            "estado": self.estado,
            "decision_notificacion": self.decision_notificacion,
            "ultimo_motivo": self.ultimo_motivo,
            "ultimo_cambio_en": self.ultimo_cambio_en.isoformat() if self.ultimo_cambio_en else None,
        }


def estado_desde_evento(incidente_id: str, evento: dict | None) -> EstadoIncidente:
    """Estado según el último evento (el de mayor secuencia); sin evento, abierto."""
    if evento is None:
        return EstadoIncidente(incidente_id=incidente_id, estado=ABIERTO)
    cerrado = evento["tipo"] == CIERRE
    return EstadoIncidente(
        incidente_id=incidente_id,
        estado=CERRADO if cerrado else ABIERTO,
        ultima_secuencia=int(evento["secuencia"]),
        decision_notificacion=evento["decision_notificacion"] if cerrado else None,
        ultimo_motivo=evento["motivo"],
        ultimo_cambio_en=evento["registrado_en"],
    )


class IncidenteNoEncontrado(LookupError):
    """El incidente no existe en la organización (o es de otra: RLS lo oculta)."""


class TransicionInvalida(ValueError):
    """Cerrar algo cerrado, reabrir algo abierto, o perder la carrera contra otro cambio."""

    def __init__(self, mensaje: str, codigo: str):
        super().__init__(mensaje)
        self.codigo = codigo
