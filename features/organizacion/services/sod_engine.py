"""Reglas puras de separación de funciones (sala ADPA: Organización).

- SoD del DPO (Art. 48 LOPDP): 'dpo' es incompatible con 'implementador' y
  'coordinador' activos en el mismo tenant. Se valida aquí y, como respaldo,
  en el trigger trg_utr_dpo_sod de la BD.
- Cuatro ojos: quien sube una evidencia no puede validarla.
"""
from typing import Iterable, Optional

from features.organizacion.domain.roles import DPO_INCOMPATIBLE_ROLES, Role


def check_dpo_sod(new_role: Role, active_roles: Iterable[Role]) -> Optional[str]:
    """Devuelve el motivo de violación de SoD del DPO, o None si es compatible."""
    active = set(active_roles)
    if new_role == Role.dpo and active & DPO_INCOMPATIBLE_ROLES:
        conflicto = sorted(r.value for r in active & DPO_INCOMPATIBLE_ROLES)
        return f"El DPO no puede tener roles operativos en el mismo tenant (tiene: {', '.join(conflicto)})"
    if new_role in DPO_INCOMPATIBLE_ROLES and Role.dpo in active:
        return f"El usuario es DPO en este tenant y no puede recibir el rol '{new_role.value}'"
    return None


def check_four_eyes(uploaded_by: Optional[str], validator_id: str) -> Optional[str]:
    """Devuelve el motivo si el validador es quien subió la evidencia."""
    if uploaded_by and uploaded_by == validator_id:
        return "Quien sube una evidencia no puede validarla"
    return None
