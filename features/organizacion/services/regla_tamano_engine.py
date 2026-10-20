"""Regla INV_LOPDP_COORDINADOR_RESPONSABLE_EXCEPCION (sala ADPA: Organización).

Una misma persona solo puede ser `coordinador` y `responsable_area` en el mismo tenant
si cuenta con una excepción SoD activa (`sod_exceptions`).
Falla cerrado: sin tamaño configurado en la organización no se permite ninguna excepción
ni acumulación (`TENANT_SIZE_NOT_CONFIGURED`). Si no hay excepción activa, se rechaza
como `SOD_VIOLATION`. El trigger `trg_utr_coordinador_responsable` de la BD aplica la
misma regla como respaldo.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from app_core.errors import SOD_VIOLATION, TENANT_SIZE_NOT_CONFIGURED
from features.organizacion.domain.roles import Role
from features.organizacion.domain.tamanos import TamanoOrganizacion

PAR_ROLES = {
    Role.coordinador.value: Role.responsable_area.value,
    Role.responsable_area.value: Role.coordinador.value,
}
MARCA_TAMANO = "TENANT_SIZE_NOT_CONFIGURED"
MARCA_SOD = "SOD_VIOLATION"


def evaluar_tamano(tamano: Optional[str]) -> None:
    """Valida que la organización tenga un tamaño válido configurado.

    Falla cerrado si no está configurado (TENANT_SIZE_NOT_CONFIGURED).
    """
    if tamano not in {t.value for t in TamanoOrganizacion}:
        raise ErrorNegocio(
            TENANT_SIZE_NOT_CONFIGURED,
            "Configure el tamaño de la organización antes de asignar coordinador y responsable de área a la misma persona.",
            action_required="configure_tenant_size",
        )


async def verificar_excepcion_coordinador_responsable(
    session: AsyncSession, tenant_id: str, user_id: str, role: str
) -> None:
    """Valida la asignación de `role` al usuario frente a su otro rol activo del par.

    Requiere una excepción SoD activa y vigente en sod_exceptions.
    """
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

    # Verificar si existe excepción activa y vigente
    tiene_excepcion = (await session.execute(
        text(
            "SELECT 1 FROM sod_exceptions "
            "WHERE tenant_id=:t AND user_id=:u AND estado='activa' "
            "AND valid_from <= now() AND valid_to > now() LIMIT 1"
        ),
        {"t": tenant_id, "u": user_id},
    )).first()

    if not tiene_excepcion:
        raise ErrorNegocio(
            SOD_VIOLATION,
            "Coordinador y responsable de área no pueden recaer en la misma persona sin una excepción SoD activa.",
        )


def traducir_error_trigger(exc: BaseException) -> Optional[ErrorNegocio]:
    """Convierte la excepción del trigger de BD en ErrorNegocio (409); None si no es suya."""
    actual: Optional[BaseException] = exc
    while actual is not None:
        mensaje = str(getattr(actual, "orig", actual))
        if MARCA_TAMANO in mensaje:
            return ErrorNegocio(TENANT_SIZE_NOT_CONFIGURED, action_required="configure_tenant_size")
        if MARCA_SOD in mensaje:
            return ErrorNegocio(
                SOD_VIOLATION,
                "Coordinador y responsable de área no pueden recaer en la misma persona en esta organización sin una excepción SoD activa.",
            )
        actual = actual.__cause__ or actual.__context__
    return None


__all__ = [
    "evaluar_tamano",
    "traducir_error_trigger",
    "verificar_excepcion_coordinador_responsable",
]
