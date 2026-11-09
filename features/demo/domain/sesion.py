# -*- coding: utf-8 -*-
# ¤demo
"""Sesión de demo de un vendedor (DEMO-00, PRD EVYDENTIA §5.6, invariantes 60 a 63)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

#: Sesiones activas simultáneas como máximo en todo el entorno demo.
TOPE = 20
#: Minutos sin actividad tras los que una sesión vence.
MINUTOS_INACTIVIDAD = 60


class EstadoSesion(str, Enum):
    ACTIVA = "activa"
    VENCIDA = "vencida"


class MotivoFin(str, Enum):
    TERMINAR = "terminar"
    INACTIVIDAD = "inactividad"
    REEMPLAZADA = "reemplazada"


@dataclass(frozen=True)
class SesionDemo:
    """Solo lo imprescindible del vendedor: `sub`, correo, tenants, persona, estado, fechas y motivo.

    `tenant_ids` es una lista: hoy siempre uno; la cuenta profesional (§5.6.6) tendrá dos.
    """

    id: str
    vendedor_sub: str
    vendedor_email: str
    tenant_ids: tuple[str, ...] = field(default_factory=tuple)
    persona_usuario_id: str | None = None
    estado: EstadoSesion = EstadoSesion.ACTIVA
    iniciada_en: datetime | None = None
    ultima_actividad: datetime | None = None
    terminada_en: datetime | None = None
    motivo_fin: MotivoFin | None = None


def esta_vencida(ultima_actividad: datetime, ahora: datetime, minutos: int = MINUTOS_INACTIVIDAD) -> bool:
    """Vence al cumplir `minutos` sin actividad: 59 no, 60 sí."""
    return ahora - ultima_actividad >= timedelta(minutes=minutos)
