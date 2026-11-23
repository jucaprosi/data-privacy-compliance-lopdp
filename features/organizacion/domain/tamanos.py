# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"""Vocabulario cerrado de tamaños de organización (sala ADPA: Organización)."""
from enum import Enum


class TamanoOrganizacion(str, Enum):
    micro = "micro"
    pequena = "pequena"
    mediana = "mediana"
    corporativo = "corporativo"


TAMANOS_ORGANIZACION = tuple(t.value for t in TamanoOrganizacion)
