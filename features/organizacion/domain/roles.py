"""Roles de la organización y sus reglas estructurales (sala ADPA: Organización)."""
from enum import Enum


class Role(str, Enum):
    responsable_area = "responsable_area"
    coordinador = "coordinador"
    dpo = "dpo"
    implementador = "implementador"
    admin_organizacion = "admin_organizacion"


# Roles que pueden acotarse a un área. El resto es transversal al tenant.
AREA_SCOPED_ROLES = {Role.responsable_area}

# Art. 48 LOPDP: el DPO supervisa, no ejecuta.
DPO_INCOMPATIBLE_ROLES = {Role.implementador, Role.coordinador}
