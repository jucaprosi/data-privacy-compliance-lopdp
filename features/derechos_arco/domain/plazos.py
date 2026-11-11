"""Plazo de respuesta por tipo de solicitud de derechos (DER-05).
`¤regulation-code` `¤derechos`

Tabla única. Criterio validado por un abogado local y comunicado por el propietario el
2026-11-09 (el documento no consta en el repositorio): 15 días para acceso, rectificación,
eliminación y oposición (arts. 13 a 16); 10 días para portabilidad (art. 62).
La unidad (hábiles o corridos) sigue pendiente: regla provisional, la más estricta (corridos).
"""
from __future__ import annotations

from features.derechos_arco.domain.models import TipoSolicitud

PLAZO_POR_TIPO: dict[TipoSolicitud, int] = {
    TipoSolicitud.ACCESO: 15,
    TipoSolicitud.RECTIFICACION: 15,
    TipoSolicitud.CANCELACION: 15,
    TipoSolicitud.OPOSICION: 15,
    TipoSolicitud.PORTABILIDAD: 10,
    TipoSolicitud.SUSPENSION: 10,
    TipoSolicitud.DECISIONES_AUTOMATIZADAS: 10,
    TipoSolicitud.QUEJA: 10,
}

# DER-06a: único punto de activación. Los tipos nuevos se leen pero no se crean; DER-06b los suma aquí.
TIPOS_ACTIVOS: frozenset[TipoSolicitud] = frozenset(
    {
        TipoSolicitud.ACCESO,
        TipoSolicitud.RECTIFICACION,
        TipoSolicitud.CANCELACION,
        TipoSolicitud.OPOSICION,
        TipoSolicitud.PORTABILIDAD,
    }
)

UNIDAD = "corridos"
ESTIMADO = True


def plazo_dias(tipo: TipoSolicitud) -> int:
    """Días de plazo del tipo; KeyError si el tipo no tiene plazo definido."""
    return PLAZO_POR_TIPO[TipoSolicitud(tipo)]
