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

# Base legal de la independencia del DPO / DPD:
# Arts. 49 y 50 de la LOPDP; Arts. 48, 49 y 56 del Reglamento General (Decreto Ejecutivo 904);
# Arts. 3, 15, 16, 17 y 18 del Reglamento del Delegado de Protección de Datos
# (Resolución SPDP-SPD-2025-0028-R, Registro Oficial 105, 19-ago-2025).

# Matriz única de incompatibilidades canónica.
# Estructura: (rol_a, rol_b, motivo, base_legal)
INCOMPATIBILIDADES_ROLES: tuple[tuple[Role, Role, str, str], ...] = (
    (
        Role.dpo,
        Role.coordinador,
        "El DPO no puede ejercer funciones directivas, de coordinación o de implementación del responsable del tratamiento",
        "Reglamento del Delegado Arts. 15.1 y 15.5",
    ),
    (
        Role.dpo,
        Role.implementador,
        "El DPO no puede implementar directamente la LOPDP ni ejecutar la gestión de riesgos",
        "Reglamento del Delegado Art. 15.5",
    ),
    (
        Role.dpo,
        Role.responsable_area,
        "El DPO no puede ejecutar o participar en actividades de tratamiento de datos en áreas operativas",
        "Reglamento del Delegado Art. 18.1",
    ),
    (
        Role.dpo,
        Role.admin_organizacion,
        "El DPO no puede tomar decisiones sobre la organización y su gestión interna (conflicto de intereses)",
        "Reglamento del Delegado Arts. 18.3 y 15.6",
    ),
)

# El DPO no puede tener ningún otro rol en la plataforma en el mismo tenant.
DPO_INCOMPATIBLE_ROLES = {
    r_b if r_a == Role.dpo else r_a
    for r_a, r_b, _, _ in INCOMPATIBILIDADES_ROLES
    if Role.dpo in (r_a, r_b)
}

