"""Reglas puras de separación de funciones (sala ADPA: Organización).

- SoD del DPO (Arts. 49-50 LOPDP; Arts. 15-18 Reglamento del Delegado): 'dpo' es incompatible
  con cualquier otro rol en el mismo tenant ('coordinador', 'implementador',
  'responsable_area', 'admin_organizacion'). Se valida aquí y, como respaldo,
  en el trigger trg_utr_dpo_sod de la BD.
- SoD del auditor (ORG-22, regla de negocio INV_LOPDP_FOUR_EYES_CLOSURE): 'auditor' y 'dpo' son
  exclusivos: quien tiene uno no tiene ningún otro rol en el tenant.
- Cuatro ojos: quien sube una evidencia no puede validarla.
"""
from typing import Iterable, Optional

from app_core.sod import check_four_eyes  # noqa: F401
from features.organizacion.domain.roles import INCOMPATIBILIDADES_ROLES, Role

_EXCLUSIVOS = (Role.dpo, Role.auditor)


def _incompatibles_de(rol: Role) -> set[Role]:
    return {b if a == rol else a for a, b, _, _ in INCOMPATIBILIDADES_ROLES if rol in (a, b)}


def check_dpo_sod(new_role: Role, active_roles: Iterable[Role]) -> Optional[str]:
    """Devuelve el motivo de violación de SoD (DPO o auditor), o None si es compatible.

    Conserva el nombre para que los llamadores no cambien; aplica cualquier par de
    `INCOMPATIBILIDADES_ROLES` en las dos direcciones.
    """
    active = set(active_roles)
    for exclusivo in _EXCLUSIVOS:
        if new_role == exclusivo:
            conflicto = sorted(r.value for r in active & _incompatibles_de(exclusivo))
            if conflicto:
                return _motivo_propio(exclusivo, conflicto)
        elif exclusivo in active and new_role in _incompatibles_de(exclusivo):
            return (f"El usuario es {_nombre(exclusivo)} en este tenant y no puede recibir el rol "
                    f"'{new_role.value}'")
    return None


def _nombre(rol: Role) -> str:
    return "auditor" if rol == Role.auditor else "DPO"


def _motivo_propio(rol: Role, conflicto: list[str]) -> str:
    if rol == Role.auditor:
        return f"El auditor no puede tener ningún otro rol en el mismo tenant (tiene: {', '.join(conflicto)})"
    return f"El DPO no puede tener roles operativos en el mismo tenant (tiene: {', '.join(conflicto)})"
