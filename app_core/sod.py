# ¤adpa
"""Errores RBAC y regla de cuatro ojos, neutrales respecto de cualquier sala (ADR 0001)."""
from typing import Optional


class RbacError(Exception):
    """Error de negocio RBAC. `code` se traduce a HTTP en el router."""

    def __init__(self, code: int, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail


class SoDViolation(RbacError):
    def __init__(self, detail: str):
        super().__init__(409, detail)


def check_four_eyes(uploaded_by: Optional[str], validator_id: str) -> Optional[str]:
    """Devuelve el motivo si el validador es quien subió la evidencia."""
    if uploaded_by and uploaded_by == validator_id:
        return "Quien sube una evidencia no puede validarla"
    return None
