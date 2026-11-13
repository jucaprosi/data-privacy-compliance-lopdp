# ¤regulation-code
# ¤paquete-normativo
"""Impacto de publicar una versión del paquete normativo (REG-01, R3).

No edita diff_engine.py. Las plantillas de la Biblioteca aún no declaran su paquete normativo y el
conteo de organizaciones cruza la RLS por tenant de los resultados del diagnóstico: los dos se
devuelven marcados como pendientes, nunca como un impacto nulo (Seguridad y Arquitecto, 2026-11-13).
"""
from __future__ import annotations

from typing import Optional

from features.regulacion_rag.domain.paquete import Impacto, Paquete


def impacto_de_publicar(paquete: Paquete, version_anterior: Optional[str]) -> Impacto:
    """Qué plantillas y cuántas organizaciones afecta pasar de la versión anterior a la nueva."""
    return Impacto(
        plantillas=[],
        plantillas_pendiente=True,
        organizaciones=None,
        organizaciones_pendiente=True,
    )
