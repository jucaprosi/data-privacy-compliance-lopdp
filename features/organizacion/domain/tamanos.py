"""Vocabulario cerrado de tamaños de organización (sala ADPA: Organización)."""
from enum import Enum


class TamanoOrganizacion(str, Enum):
    micro = "micro"
    pequena = "pequena"
    mediana = "mediana"
    corporativo = "corporativo"


TAMANOS_ORGANIZACION = tuple(t.value for t in TamanoOrganizacion)
