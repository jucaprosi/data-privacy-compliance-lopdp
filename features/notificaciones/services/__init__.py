# -*- coding: utf-8 -*-
# ¤adpa
# ¤roadmap
"""Motores y servicios de la sala ADPA: Notificaciones."""
from features.notificaciones.services.adaptadores import (
    NotificadorFalso,
    NotificadorResendBoceto,
)
from features.notificaciones.services.agrupador_engine import (
    agrupar_tareas_por_destinatario,
    construir_correos_lote,
    despachar_lote_notificaciones,
)
from features.notificaciones.services.plantillas_engine import (
    renderizar_correo_lote_asignaciones,
)

__all__ = [
    "NotificadorFalso",
    "NotificadorResendBoceto",
    "agrupar_tareas_por_destinatario",
    "construir_correos_lote",
    "despachar_lote_notificaciones",
    "renderizar_correo_lote_asignaciones",
]
