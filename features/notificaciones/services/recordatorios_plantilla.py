# -*- coding: utf-8 -*-
# ¤adpa
# ¤roadmap
"""Plantilla del correo de recordatorios de vencimiento (RM-23): un correo con todas las tareas del usuario."""
from __future__ import annotations

from html import escape
from typing import Sequence

from features.notificaciones.domain.models import Destinatario, TareaAsignadaItem, enlace_tarea

ETIQUETAS = {"7dias": "Vence en 7 días", "hoy": "Vence hoy", "vencida": "Vencida"}


def renderizar_correo_recordatorios(
    destinatario: Destinatario,
    items: Sequence[tuple[TareaAsignadaItem, str]],
    app_base_url: str,
) -> tuple[str, str, str]:
    """Genera (asunto, cuerpo_texto, cuerpo_html). Solo datos de la tarea, nunca evidencias (PRD §5.8)."""
    total = len(items)
    asunto = (
        f"Recordatorio de tarea en tu Hoja de Ruta: {items[0][0].titulo}"
        if total == 1
        else f"Tienes {total} tareas por atender en tu Hoja de Ruta"
    )

    lineas = [f"Hola, {destinatario.nombre}:", "", f"Tienes {total} tarea(s) con vencimiento por atender:", ""]
    filas_html = []
    for tarea, tipo in items:
        url = enlace_tarea(app_base_url, tarea.task_id)
        etiqueta = ETIQUETAS[tipo]
        lineas.append(f"  - [{tarea.control_ref}] {tarea.titulo} ({etiqueta}: {tarea.fecha_fin})")
        lineas.append(f"    Enlace: {url}")
        filas_html.append(
            f"<li>[{escape(tarea.control_ref)}] {escape(tarea.titulo)} · {etiqueta}: {escape(tarea.fecha_fin or '')} "
            f"· <a href=\"{escape(url, quote=True)}\">Abrir la Hoja de Ruta</a></li>"
        )
    lineas.extend(["", "Atentamente,", "Plataforma LOPDP 360"])

    cuerpo_html = (
        "<!DOCTYPE html><html lang=\"es\"><head><meta charset=\"utf-8\" /></head><body>"
        f"<p>Hola, {escape(destinatario.nombre)}:</p>"
        f"<p>Tienes {total} tarea(s) con vencimiento por atender:</p>"
        f"<ul>{''.join(filas_html)}</ul>"
        "<p>Atentamente,<br />Plataforma LOPDP 360</p></body></html>"
    )
    return asunto, "\n".join(lineas), cuerpo_html
