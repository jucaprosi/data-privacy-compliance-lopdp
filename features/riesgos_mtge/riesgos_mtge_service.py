"""Compuerta pública de la sala ADPA: Riesgos y MTGE Gran Escala."""
from features.riesgos_mtge.domain.models import (
    AlcanceGeografico,
    CategoriasDatos,
    EntradaCalculoMTGE,
    Frecuencia,
    Permanencia,
    ResultadoMTGE,
    SupuestoDirecto,
)
from features.riesgos_mtge.services.mtge_calculator import UMBRAL_GRAN_ESCALA_PUNTOS, calcular_mtge_actividad


def evaluar_gran_escala_mtge(entrada: EntradaCalculoMTGE) -> ResultadoMTGE:
    """Califica un tratamiento como de gran escala (Res. SPDP-SPD-2026-0005-R, arts. 8-10 y 14)."""
    return calcular_mtge_actividad(entrada)


__all__ = [
    "AlcanceGeografico",
    "CategoriasDatos",
    "EntradaCalculoMTGE",
    "Frecuencia",
    "Permanencia",
    "ResultadoMTGE",
    "SupuestoDirecto",
    "UMBRAL_GRAN_ESCALA_PUNTOS",
    "evaluar_gran_escala_mtge",
]
