# -*- coding: utf-8 -*-
# ¤adpa
# ¤roadmap
"""Motor de renderizado de plantillas de correo mínimo (sala ADPA: Notificaciones)."""
from __future__ import annotations

from typing import Sequence
from features.notificaciones.domain.models import Destinatario, TareaAsignadaItem


def renderizar_correo_lote_asignaciones(
    destinatario: Destinatario,
    tareas: Sequence[TareaAsignadaItem],
    app_base_url: str = "https://app.plataforma360.ec",
) -> tuple[str, str, str]:
    """Genera (asunto, cuerpo_texto, cuerpo_html) para un conjunto de tareas asignadas.

    Diseño del correo mínimo:
    - Agrupación por lote: Un solo correo con múltiples tareas, evitando saturación.
    - Enlace claro y directo a cada tarea.
    - Cero tokens estigmérgicos en la vista de usuario.
    """
    total = len(tareas)
    if total == 1:
        asunto = f"Nueva tarea asignada en Hoja de Ruta: {tareas[0].titulo}"
    else:
        asunto = f"Tienes {total} nuevas tareas asignadas en tu Hoja de Ruta"

    # Cuerpo en texto plano
    lineas_texto = [
        f"Hola, {destinatario.nombre}:",
        "",
        f"Se te han asignado {total} tarea(s) en la Hoja de Ruta de cumplimiento LOPDP.",
        "",
        "Detalle de tareas:",
    ]

    for idx, t in enumerate(tareas, 1):
        url = t.enlace_web or f"{app_base_url}/dashboard/roadmap/tasks/{t.task_id}"
        plazo = f" | Vence: {t.fecha_fin}" if t.fecha_fin else ""
        lineas_texto.append(
            f"  {idx}. [{t.control_ref}] {t.titulo} (Prioridad: {t.prioridad}{plazo})"
        )
        lineas_texto.append(f"     Enlace: {url}")

    lineas_texto.extend([
        "",
        "Por favor ingresa a la plataforma para revisar los entregables y gestionar las evidencias requeridas.",
        "",
        "Atentamente,",
        "Plataforma LOPDP 360",
    ])
    cuerpo_texto = "\n".join(lineas_texto)

    # Cuerpo HTML
    items_html = []
    for t in tareas:
        url = t.enlace_web or f"{app_base_url}/dashboard/roadmap/tasks/{t.task_id}"
        plazo_html = f" · <span style='color:#666;'>Vence: {t.fecha_fin}</span>" if t.fecha_fin else ""
        items_html.append(
            f"""
            <li style="margin-bottom: 12px; line-height: 1.4;">
                <strong>[{t.control_ref}] {t.titulo}</strong>
                <span style="font-size: 12px; background: #eee; padding: 2px 6px; border-radius: 4px; margin-left: 6px;">
                    {t.prioridad.upper()}
                </span>
                {plazo_html}
                <br />
                <a href="{url}" style="color: #0284c7; text-decoration: underline; font-size: 13px;">
                    Ver detalles y subir evidencia &rarr;
                </a>
            </li>
            """
        )

    cuerpo_html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="utf-8" /></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b; padding: 20px;">
        <h2 style="color: #0f172a;">Hola, {destinatario.nombre}</h2>
        <p>Se han asignado <strong>{total} tarea(s)</strong> a tu cargo dentro de la Hoja de Ruta de adecuación a la LOPDP.</p>
        <ul style="padding-left: 20px;">
            {"".join(items_html)}
        </ul>
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
        <p style="font-size: 12px; color: #64748b;">
            Este es un aviso automático generado por JUBYS Plataforma LOPDP 360 Ecuador.
        </p>
    </body>
    </html>
    """.strip()

    return asunto, cuerpo_texto, cuerpo_html
