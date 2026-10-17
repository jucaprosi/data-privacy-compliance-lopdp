# -*- coding: utf-8 -*-
# ¤adpa
# ¤roadmap
"""Modelos de dominio tipados para la sala ADPA: Notificaciones (Fase BBAP, paso 1).

Invariantes:
- Modelos inmutables / tipados para eventos, destinatarios, mensajes y lotes.
- Agrupación determinista por usuario y por lote (batching).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Sequence
from uuid import UUID, uuid4


class CanalNotificacion(str, Enum):
    """Canales de notificación admitidos (PRD §5.8 restringe inicialmente a correo)."""
    CORREO = "correo"


class EstadoEnvio(str, Enum):
    """Estado del despacho de una notificación."""
    PENDIENTE = "pendiente"
    ENVIADO = "enviado"
    FALLIDO = "fallido"
    DESCARTADO_SIN_DESTINATARIO = "descartado_sin_destinatario"


class TipoEventoNotificacion(str, Enum):
    """Tipos de eventos disparadores en la plataforma."""
    TASK_ASSIGNED = "task_assigned"
    # Eventos adicionales identificados para consulta/decisión con el propietario:
    # TASK_STATUS_CHANGED = "task_status_changed"
    # EVIDENCE_VALIDATED = "evidence_validated"
    # DEADLINE_APPROACHING = "deadline_approaching"


@dataclass(frozen=True)
class Destinatario:
    """Información del destinatario de una notificación."""
    user_id: str
    email: str
    nombre: str
    tenant_id: str


@dataclass(frozen=True)
class TareaAsignadaItem:
    """Detalle de una tarea asignada incluida en un lote de notificación."""
    task_id: str
    titulo: str
    control_ref: str
    prioridad: str
    fecha_fin: str | None = None
    enlace_web: str = ""


@dataclass(frozen=True)
class EventoAuditoriaAsignacion:
    """Evento capturado desde task_audit_log generado por RM-08."""
    evento_id: str
    task_id: str
    tenant_id: str
    user_id_asignador: str | None
    responsable_id: str
    responsable_nombre: str
    area_id: str | None
    timestamp: datetime
    metadata_extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CorreoLoteNotificacion:
    """Mensaje consolidado agrupado por usuario para despacho único por lote."""
    lote_id: str
    destinatario: Destinatario
    canal: CanalNotificacion
    asunto: str
    cuerpo_texto: str
    cuerpo_html: str
    tareas: tuple[TareaAsignadaItem, ...]
    creado_en: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class ResultadoDespacho:
    """Resultado auditable del intento de despacho."""
    despacho_id: str
    lote_id: str
    destinatario_email: str
    estado: EstadoEnvio
    id_externo_proveedor: str | None = None
    error_detalle: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# Destino de los enlaces de los correos. PROVISIONAL: el panel es una sola página (/dashboard) con
# pestañas y no tiene una URL por tarea, así que el enlace lleva al panel y no a la tarea concreta.
# Cuando el frontend exponga un enlace profundo (por ejemplo ?tarea=<id>), se cambia aquí y solo aquí.
RUTA_PANEL = "/dashboard"


def enlace_tarea(app_base_url: str, task_id: str) -> str:
    """Enlace que se incluye en el correo para una tarea. `task_id` se reserva para el enlace profundo."""
    return f"{app_base_url.rstrip('/')}{RUTA_PANEL}"
