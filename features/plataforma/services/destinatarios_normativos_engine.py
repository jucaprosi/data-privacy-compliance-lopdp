# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤inteligencia-normativa ¤seguridad-tenant ¤adpa
"""NORM-02b: destinatarios del aviso de novedades normativas, por organización (R1, R2).

Única lectura entre organizaciones de la ficha. Los destinatarios salen solo de la función
`fn_destinatarios_normativos()` (SECURITY DEFINER, solo `lopdp_app` la ejecuta): el operador sigue sin fijar
organización (ORG-09) y no consulta `user_tenant_roles` directamente. Cada elemento lleva solo el identificador
de la organización y los dos grupos de correos; nada de nombres, RUC ni datos de tratamiento.
"""
from __future__ import annotations

from sqlalchemy import text

CAMPOS = ("tenant_id", "correos_admin", "correos_dpo")


async def destinatarios_normativos(session) -> list[dict]:
    """[{tenant_id, correos_admin, correos_dpo}] de las organizaciones activas con algún destinatario."""
    filas = (await session.execute(
        text("SELECT tenant_id, correos_admin, correos_dpo FROM fn_destinatarios_normativos()")
    )).all()
    return [
        {"tenant_id": f.tenant_id, "correos_admin": list(f.correos_admin or []), "correos_dpo": list(f.correos_dpo or [])}
        for f in filas
    ]


async def contar_organizaciones_activas(session) -> int:
    """Solo un número: cuántas organizaciones activas hay, para contar las que quedan sin destinatarios (R7)."""
    return int((await session.execute(text("SELECT count(*) FROM tenants WHERE activo IS TRUE"))).scalar_one())
