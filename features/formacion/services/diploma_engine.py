# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤engine ¤evidencias
"""Generación de constancias de formación (FOR-01).

Texto visible: «Constancia de formación», nunca «diploma» ni «certificado» (Doctrina 1).
"""
from __future__ import annotations


def generar_contenido_constancia(
    persona_id: str,
    accion_nombre: str,
    nota: float,
    fecha_iso: str,
) -> bytes:
    """Genera el contenido de la constancia de formación como texto UTF-8 válido."""
    lineas = [
        "Constancia de formación",
        "=======================",
        f"Participante: {persona_id}",
        f"Acción formativa: {accion_nombre}",
        f"Calificación obtenida: {nota:.1f} / 100",
        f"Fecha de finalización: {fecha_iso}",
        "",
        "Esta constancia acredita la realización de la acción formativa en la plataforma.",
    ]
    texto = "\n".join(lineas)
    return texto.encode("utf-8")
