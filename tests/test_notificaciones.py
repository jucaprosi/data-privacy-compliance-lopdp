# -*- coding: utf-8 -*-
# ¤adpa
# ¤roadmap
"""Pruebas unitarias y de integración para la sala ADPA: Notificaciones (Task NOTIF-01).

Verifica:
1. Agrupación por usuario y por lote (batching: un solo correo para N tareas del mismo destinatario).
2. Regla de integridad: Un correo no sale sin destinatario o con correo vacío (descartado).
3. Interpretación fiel del evento 'task_assigned' de task_audit_log (RM-08).
4. Diseño de correo mínimo con enlaces y sin tokens estigmérgicos en la vista de usuario.
5. Funcionamiento del puerto Notificador con implementación falsa y boceto Resend.
"""
from __future__ import annotations

from datetime import datetime, timezone
import pytest

from features.notificaciones import (
    CanalNotificacion,
    Destinatario,
    EstadoEnvio,
    NotificadorFalso,
    NotificadorResendBoceto,
    TareaAsignadaItem,
    agrupar_tareas_por_destinatario,
    construir_correos_lote,
    despachar_lote_notificaciones,
    notificar_asignaciones_lote,
    procesar_evento_task_assigned_audit,
    renderizar_correo_lote_asignaciones,
)


def test_agrupacion_por_usuario_y_lote():
    """Un usuario con 3 tareas asignadas debe recibir UN SOLO correo consolidado en el lote."""
    u1 = Destinatario(
        user_id="user-01",
        email="responsable.ti@empresa.ec",
        nombre="Carlos TI",
        tenant_id="tenant-demo",
    )
    u2 = Destinatario(
        user_id="user-02",
        email="responsable.rrhh@empresa.ec",
        nombre="Ana RRHH",
        tenant_id="tenant-demo",
    )

    t1 = TareaAsignadaItem(task_id="tsk-1", titulo="Inventario RAT", control_ref="P2", prioridad="alta")
    t2 = TareaAsignadaItem(task_id="tsk-2", titulo="Cifrado backups", control_ref="P14", prioridad="critica")
    t3 = TareaAsignadaItem(task_id="tsk-3", titulo="Capacitación LOPDP", control_ref="P5", prioridad="media")
    t4 = TareaAsignadaItem(task_id="tsk-4", titulo="Cláusulas contratos laborales", control_ref="P8", prioridad="alta")

    asignaciones = [
        (u1, t1),
        (u1, t2),
        (u1, t3),
        (u2, t4),
    ]

    grupos = agrupar_tareas_por_destinatario(asignaciones)
    assert len(grupos) == 2
    assert len(grupos[u1]) == 3
    assert len(grupos[u2]) == 1

    correos = construir_correos_lote(grupos)
    assert len(correos) == 2

    # Verificar que el correo de u1 incluye las 3 tareas en un único mensaje
    correo_u1 = next(c for c in correos if c.destinatario.email == u1.email)
    assert len(correo_u1.tareas) == 3
    assert "3 nuevas tareas asignadas" in correo_u1.asunto
    assert "Inventario RAT" in correo_u1.cuerpo_texto
    assert "Cifrado backups" in correo_u1.cuerpo_texto
    assert "Capacitación LOPDP" in correo_u1.cuerpo_texto

    # Verificar que el correo de u2 incluye 1 sola tarea
    correo_u2 = next(c for c in correos if c.destinatario.email == u2.email)
    assert len(correo_u2.tareas) == 1
    assert "Cláusulas contratos laborales" in correo_u2.asunto


@pytest.mark.asyncio
async def test_correo_no_sale_sin_destinatario():
    """Un correo sin destinatario válido debe ser descartado sin intentar despacho."""
    u_invalido = Destinatario(
        user_id="user-anon",
        email="",  # Email vacío
        nombre="Sin Correo",
        tenant_id="tenant-demo",
    )
    t1 = TareaAsignadaItem(task_id="tsk-99", titulo="Tarea Huérfana", control_ref="P1", prioridad="alta")

    notificador = NotificadorFalso()
    resultados = await notificar_asignaciones_lote([(u_invalido, t1)], notificador=notificador)

    assert len(resultados) == 1
    assert resultados[0].estado == EstadoEnvio.DESCARTADO_SIN_DESTINATARIO
    assert len(notificador.correos_enviados) == 0


def test_interpretacion_evento_real_task_assigned_rm08():
    """Valida la lectura fiel de la estructura que RM-08 inserta en task_audit_log."""
    # Fila real producida por tarea_asignacion_engine.py
    audit_row_simulada = {
        "id": "audit-uuid-12345",
        "task_id": "task-uuid-67890",
        "tenant_id": "tenant-corp-01",
        "action": "task_assigned",
        "user_id": "admin-asignador-01",
        "timestamp": datetime.now(timezone.utc),
        "payload": {
            "responsable_id": "user-resp-888",
            "responsable_nombre": "Ing. María Solís",
            "area_id": "area-ciberseguridad-01",
        },
    }

    tarea_info = {
        "title": "Configurar control de accesos MFA",
        "control_ref": "P12",
        "priority": "critica",
        "end_date": "2026-11-30",
    }

    dest, item = procesar_evento_task_assigned_audit(
        audit_row=audit_row_simulada,
        destinatario_email="msolis@empresa.ec",
        tarea_info=tarea_info,
        app_base_url="https://app.plataforma360.ec",
    )

    assert dest.user_id == "user-resp-888"
    assert dest.email == "msolis@empresa.ec"
    assert dest.nombre == "Ing. María Solís"
    assert dest.tenant_id == "tenant-corp-01"

    assert item.task_id == "task-uuid-67890"
    assert item.titulo == "Configurar control de accesos MFA"
    assert item.control_ref == "P12"
    assert item.prioridad == "critica"
    assert item.fecha_fin == "2026-11-30"
    assert item.enlace_web == "https://app.plataforma360.ec/dashboard/roadmap/tasks/task-uuid-67890"


def test_diseno_correo_minimo_y_sin_tokens_en_interfaz():
    """El correo debe contener los enlaces a la tarea y no contener tokens estigmérgicos (¤)."""
    dest = Destinatario(
        user_id="user-01",
        email="test@empresa.ec",
        nombre="Juan Pérez",
        tenant_id="tenant-01",
    )
    t = TareaAsignadaItem(
        task_id="tsk-100",
        titulo="Auditoría de Transferencias Internacionales",
        control_ref="P33",
        prioridad="alta",
        fecha_fin="2026-12-15",
        enlace_web="https://app.plataforma360.ec/dashboard/roadmap/tasks/tsk-100",
    )

    asunto, texto, html = renderizar_correo_lote_asignaciones(dest, [t])

    # Verificación de enlaces presentes
    assert "https://app.plataforma360.ec/dashboard/roadmap/tasks/tsk-100" in texto
    assert "https://app.plataforma360.ec/dashboard/roadmap/tasks/tsk-100" in html

    # Verificación de ausencia total de tokens estigmérgicos en la vista de usuario
    assert "¤" not in asunto
    assert "¤" not in texto
    assert "¤" not in html


@pytest.mark.asyncio
async def test_adaptador_resend_boceto():
    """El adaptador de diseño Resend debe registrar el estado pendiente con documentación de requisitos."""
    dest = Destinatario(
        user_id="u-1",
        email="dev@empresa.ec",
        nombre="Dev User",
        tenant_id="t-1",
    )
    t = TareaAsignadaItem(task_id="t-1", titulo="Tarea Demo", control_ref="P1", prioridad="media")

    grupos = agrupar_tareas_por_destinatario([(dest, t)])
    correos = construir_correos_lote(grupos)

    adaptador = NotificadorResendBoceto(api_key="<PLACEHOLDER>")
    resultados = await despachar_lote_notificaciones(correos, adaptador)

    assert len(resultados) == 1
    assert resultados[0].estado == EstadoEnvio.PENDIENTE
    assert "RESEND_API_KEY" in (resultados[0].error_detalle or "")
