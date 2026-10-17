# -*- coding: utf-8 -*-
# ¤adpa
# ¤roadmap
"""Compuerta pública de la sala ADPA: Notificaciones (Fase BBAP, paso 1).

Decisión de diseño:
- Notificaciones por correo para eventos operativos clave de la plataforma (PRD §5.8).
- Proveedor propuesto: Resend (3 000 correos/mes, 100/día en Free Tier).
- Primer disparador: Evento 'task_assigned' emitido por RM-08 en task_audit_log.
- Diseño de correo mínimo: enlace a la tarea, agrupado por usuario y por lote.
- Puerto desacoplado 'Notificador' con implementación falsa para pruebas y boceto para Resend.

Invariantes ADPA:
- Aislamiento hermético: única compuerta pública para interactuar con notificaciones.
- Cero dependencias de red en pruebas locales.
- Modelos inmutables y reglas de no salida de correos sin destinatario.
"""
from __future__ import annotations

from typing import Sequence
from features.notificaciones.domain.models import (
    CanalNotificacion,
    CorreoLoteNotificacion,
    Destinatario,
    EstadoEnvio,
    EventoAuditoriaAsignacion,
    ResultadoDespacho,
    TareaAsignadaItem,
    TipoEventoNotificacion,
    enlace_tarea,
)
from features.notificaciones.domain.puertos import Notificador
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
    # Modelos y Enums
    "CanalNotificacion",
    "CorreoLoteNotificacion",
    "Destinatario",
    "EstadoEnvio",
    "EventoAuditoriaAsignacion",
    "Notificador",
    "ResultadoDespacho",
    "TareaAsignadaItem",
    "TipoEventoNotificacion",
    # Adaptadores
    "NotificadorFalso",
    "NotificadorResendBoceto",
    # Funciones de compuerta
    "agrupar_tareas_por_destinatario",
    "construir_correos_lote",
    "despachar_lote_notificaciones",
    "notificar_asignaciones_lote",
    "procesar_evento_task_assigned_audit",
    "renderizar_correo_lote_asignaciones",
]


def procesar_evento_task_assigned_audit(
    audit_row: dict,
    destinatario_email: str,
    tarea_info: dict,
    app_base_url: str,
) -> tuple[Destinatario, TareaAsignadaItem]:
    """Interpreta la fila real de task_audit_log generada por RM-08 (tarea_asignacion_engine.py).

    Estructura real en task_audit_log:
    - id: str (UUID)
    - task_id: str
    - tenant_id: str
    - action: "task_assigned"
    - user_id: str | None (quien asignó)
    - timestamp: datetime
    - payload: {"responsable_id": str, "responsable_nombre": str, "area_id": str | None}
    """
    payload = audit_row.get("payload") or {}
    responsable_id = payload.get("responsable_id") or "desconocido"
    responsable_nombre = payload.get("responsable_nombre") or "Responsable"
    tenant_id = audit_row.get("tenant_id") or ""
    task_id = audit_row.get("task_id") or ""

    destinatario = Destinatario(
        user_id=responsable_id,
        email=destinatario_email,
        nombre=responsable_nombre,
        tenant_id=tenant_id,
    )

    tarea_item = TareaAsignadaItem(
        task_id=task_id,
        titulo=tarea_info.get("title", f"Tarea {task_id}"),
        control_ref=tarea_info.get("control_ref", "P0"),
        prioridad=tarea_info.get("priority", "media"),
        fecha_fin=tarea_info.get("end_date"),
        enlace_web=enlace_tarea(app_base_url, task_id),
    )

    return destinatario, tarea_item


async def notificar_asignaciones_lote(
    asignaciones: Sequence[tuple[Destinatario, TareaAsignadaItem]],
    app_base_url: str,
    notificador: Notificador | None = None,
) -> list[ResultadoDespacho]:
    """Punto de entrada de alto nivel de la compuerta para notificar tareas agrupadas por usuario."""
    notificador_activo = notificador or NotificadorFalso()
    grupos = agrupar_tareas_por_destinatario(asignaciones)
    correos = construir_correos_lote(grupos, app_base_url=app_base_url)
    return await despachar_lote_notificaciones(correos, notificador_activo)
