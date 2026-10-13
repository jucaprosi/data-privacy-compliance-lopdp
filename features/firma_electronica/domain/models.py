# -*- coding: utf-8 -*-
# ¤adpa
# ¤firma-electronica
"""Boceto de modelos de dominio para la sala Firma Electrónica (Fase BBAP, paso 1)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class TransaccionFirmaBoceto:
    """Modelo conceptual para persistencia futura del flujo de firma con ANF."""
    id: str
    tenant_id: str
    documento_id: str
    firmante_id: str
    estado: str
    creado_en: datetime
