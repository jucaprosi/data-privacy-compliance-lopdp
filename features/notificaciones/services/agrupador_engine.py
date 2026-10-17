# -*- coding: utf-8 -*-
# ¤adpa
# ¤roadmap
"""Motor de agrupación de eventos y procesamiento de lotes (sala ADPA: Notificaciones)."""
from __future__ import annotations

from collections import defaultdict
from typing import Sequence
from uuid import uuid4

from features.notificaciones.domain.models import (
    CanalNotificacion,
    CorreoLoteNotificacion,
    Destinatario,
    EventoAuditoriaAsignacion,
    ResultadoDespacho,
    TareaAsignadaItem,
)
from features.notificaciones.domain.puertos import Notificador
from features.notificaciones.services.plantillas_engine import (
    renderizar_correo_lote_asignaciones,
)


def agrupar_tareas_por_destinatario(
    asignaciones: Sequence[tuple[Destinatario, TareaAsignadaItem]],
) -> dict[Destinatario, list[TareaAsignadaItem]]:
    """Agrupa una lista de asignaciones individuales en lotes por destinatario.

    Garantiza que un usuario reciba un único correo consolidado por lote en lugar de N correos.
    """
    grupos: dict[Destinatario, list[TareaAsignadaItem]] = defaultdict(list)
    for dest, tarea in asignaciones:
        grupos[dest].append(tarea)
    return dict(grupos)


def construir_correos_lote(
    grupos: dict[Destinatario, list[TareaAsignadaItem]],
    app_base_url: str,
) -> list[CorreoLoteNotificacion]:
    """Convierte los grupos de asignaciones en mensajes listos para despacho."""
    correos: list[CorreoLoteNotificacion] = []

    for destinatario, tareas in grupos.items():
        if not tareas:
            continue
        asunto, cuerpo_texto, cuerpo_html = renderizar_correo_lote_asignaciones(
            destinatario=destinatario,
            tareas=tareas,
            app_base_url=app_base_url,
        )
        lote = CorreoLoteNotificacion(
            lote_id=str(uuid4()),
            destinatario=destinatario,
            canal=CanalNotificacion.CORREO,
            asunto=asunto,
            cuerpo_texto=cuerpo_texto,
            cuerpo_html=cuerpo_html,
            tareas=tuple(tareas),
        )
        correos.append(lote)

    return correos


async def despachar_lote_notificaciones(
    correos: Sequence[CorreoLoteNotificacion],
    notificador: Notificador,
) -> list[ResultadoDespacho]:
    """Despacha secuencialmente o en batch los correos preparados hacia el puerto."""
    resultados: list[ResultadoDespacho] = []
    for correo in correos:
        res = await notificador.enviar_correo(correo)
        resultados.append(res)
    return resultados
