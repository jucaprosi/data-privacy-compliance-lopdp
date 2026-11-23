# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa
# ¤roadmap
"""Re-exportador del dominio de la sala ADPA: Notificaciones."""
from features.notificaciones.domain.models import (
    CanalNotificacion,
    CorreoLoteNotificacion,
    Destinatario,
    EstadoEnvio,
    EventoAuditoriaAsignacion,
    ResultadoDespacho,
    TareaAsignadaItem,
    TipoEventoNotificacion,
)
from features.notificaciones.domain.puertos import Notificador

__all__ = [
    "CanalNotificacion",
    "CorreoLoteNotificacion",
    "Destinatario",
    "EstadoEnvio",
    "EventoAuditoriaAsignacion",
    "Notificador",
    "ResultadoDespacho",
    "TareaAsignadaItem",
    "TipoEventoNotificacion",
]
