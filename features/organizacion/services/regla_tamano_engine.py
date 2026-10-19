"""Regla INV_LOPDP_ENCARGADO_RESPONSABLE_SIZE (sala ADPA: Organización).

Una misma persona solo puede ser `encargado` y `responsable_area` en el mismo tenant
si la organización es `micro` o `pequena`. Falla cerrado: sin tamaño válido no se
puede saber si se rompe la separación de funciones. El trigger
`trg_utr_encargado_responsable` de la BD aplica la misma regla como respaldo.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from app_core.errors import SOD_VIOLATION, TENANT_SIZE_NOT_CONFIGURED
from features.organizacion.domain.roles import Role
from features.organizacion.domain.tamanos import TamanoOrganizacion

TAMANOS_PERMITIDOS = frozenset({TamanoOrganizacion.micro.value, TamanoOrganizacion.pequena.value})
PAR_ROLES = {
    Role.coordinador.value: Role.responsable_area.value,
    Role.responsable_area.value: Role.coordinador.value,
}
MARCA_TAMANO = "TENANT_SIZE_NOT_CONFIGURED"
MARCA_SOD = "SOD_VIOLATION"


def evaluar_tamano(tamano: Optional[str]) -> None:
    """Lanza ErrorNegocio si el tamaño no permite acumular coordinador y responsable_area."""
    if tamano not in {t.value for t in TamanoOrganizacion}:
        raise ErrorNegocio(
            TENANT_SIZE_NOT_CONFIGURED,
            "Configure el tamaño de la organización antes de asignar coordinador y responsable de área a la misma persona.",
            action_required="configure_tenant_size",
        )
    if tamano not in TAMANOS_PERMITIDOS:
        raise ErrorNegocio(
            SOD_VIOLATION,
            f"En una organización '{tamano}' el coordinador no puede ser también responsable de área.",
        )


async def verificar_encargado_responsable(
    session: AsyncSession, tenant_id: str, user_id: str, role: str
) -> None:
    """Valida la asignación de `role` al usuario frente a su otro rol activo del par."""
    contraparte = PAR_ROLES.get(role)
    if contraparte is None:
        return
    acumula = (await session.execute(
        text(
            "SELECT 1 FROM user_tenant_roles WHERE user_id=:u AND tenant_id=:t AND role=:r "
            "AND (valid_to IS NULL OR valid_to > now()) LIMIT 1"
        ),
        {"u": user_id, "t": tenant_id, "r": contraparte},
    )).first()
    if not acumula:
        return
    tamano = (await session.execute(
        text("SELECT tamano FROM tenants WHERE id=:t"), {"t": tenant_id}
    )).scalar_one_or_none()
    evaluar_tamano(tamano)


def traducir_error_trigger(exc: BaseException) -> Optional[ErrorNegocio]:
    """Convierte la excepción del trigger de BD en ErrorNegocio (409); None si no es suya."""
    actual: Optional[BaseException] = exc
    while actual is not None:
        mensaje = str(getattr(actual, "orig", actual))
        if MARCA_TAMANO in mensaje:
            return ErrorNegocio(TENANT_SIZE_NOT_CONFIGURED, action_required="configure_tenant_size")
        if MARCA_SOD in mensaje:
            return ErrorNegocio(SOD_VIOLATION, "Coordinador y responsable de área no pueden recaer en la misma persona en esta organización.")
        actual = actual.__cause__ or actual.__context__
    return None


__all__ = [
    "evaluar_tamano",
    "traducir_error_trigger",
    "verificar_encargado_responsable",
]
