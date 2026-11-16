# ¤evidencias
"""Retención por objeto de los documentos de evidencia: un solo lugar para decidirla."""
from __future__ import annotations


def retencion_dias(tenant_id: str) -> int:
    """Días que el almacén conserva el objeto, sin poder borrarlo, desde que se sube.

    Mientras no exista BOV-01 vale lo mismo para todas las organizaciones (cinco años). BOV-01 la
    sustituirá por la del paquete contratado (PRD §2.2: hasta 5, 7 o 10 años; el pool admite de 3 a
    10). Ningún otro archivo escribe este número: lo lee de aquí.
    """
    return 1825
