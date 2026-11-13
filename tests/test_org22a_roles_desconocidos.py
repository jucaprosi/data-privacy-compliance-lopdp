# -*- coding: utf-8 -*-
# ¤rbac-tenant
"""ORG-22a: el CHECK admite 'auditor' y las dos lecturas de roles toleran un valor que `Role` no conoce.

Durante el despliegue por escalones la revisión anterior lee filas `auditor` (aún sin `Role.auditor`, que
llega con ORG-22): no debe dar 500 y la SoD del DPO debe fallar cerrada. Corren contra PostgreSQL real
(`TEST_DATABASE_URL`: el PG16 del arnés o evydentia-pruebas, nunca producción) y terminan con rollback.

Mutaciones documentadas: si `grant_role` vuelve a `Role(valor)` estricto, fallan
test_conceder_rol_con_una_fila_desconocida_no_da_500 y test_conceder_dpo_..._falla_cerrada (ValueError); si lo
hace `_verificar_dpo`, falla test_invitar_dpo_..._falla_cerrada (ValueError en vez de ErrorNegocio); si la SoD
deja de fallar cerrada con un rol desconocido, fallan los dos test_*_falla_cerrada.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app_core.errors import ErrorNegocio
from features.organizacion import organizacion_service as org

ROL_FUTURO = "rol_de_una_version_futura"  # ORG-22 hizo conocido a 'auditor'

pytestmark = pytest.mark.asyncio


@pytest.fixture
def fabrica(db_engine):
    return async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)


async def _escenario(s, rol_extra: str = "auditor") -> dict:
    sufijo = uuid.uuid4().hex[:8]
    t, admin, otra = f"t-{sufijo}", f"u-adm-{sufijo}", f"u-otra-{sufijo}"
    correo = f"otra-{sufijo}@org22a.invalid"
    await s.execute(text(
        "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
        "VALUES (:id, 'Org 22a', 'Org 22a SA', :ruc, 'mediana')"), {"id": t, "ruc": f"RUC{sufijo}"})
    for uid, e in ((admin, f"adm-{sufijo}@org22a.invalid"), (otra, correo)):
        await s.execute(text("INSERT INTO users (id, email, nombre, activo) VALUES (:i, :e, 'Persona', TRUE)"),
                        {"i": uid, "e": e})
    if rol_extra == ROL_FUTURO:  # el CHECK solo admite roles conocidos: se suelta dentro de la transacción (rollback)
        await s.execute(text("ALTER TABLE user_tenant_roles DROP CONSTRAINT ck_utr_role"))
    await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": t})
    for uid, rol in ((admin, "admin_organizacion"), (otra, rol_extra)):
        await s.execute(text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, :r)"),
                        {"i": f"utr-{uuid.uuid4().hex[:8]}", "u": uid, "t": t, "r": rol})
    return {"t": t, "admin": admin, "otra": otra, "correo": correo}


async def test_el_check_acepta_auditor_y_rechaza_lo_inventado(fabrica):
    async with fabrica() as s:
        e = await _escenario(s)
        assert (await s.execute(text(
            "SELECT count(*) FROM user_tenant_roles WHERE tenant_id = :t AND role = 'auditor'"), {"t": e["t"]}
        )).scalar_one() == 1
        with pytest.raises(IntegrityError):
            async with s.begin_nested():
                await s.execute(text(
                    "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES ('utr-x', :u, :t, 'inventado')"),
                    {"u": e["admin"], "t": e["t"]})
        await s.rollback()


async def test_conceder_rol_con_una_fila_desconocida_no_da_500(fabrica):
    async with fabrica() as s:
        e = await _escenario(s, ROL_FUTURO)
        res = await org.grant_role(s, e["t"], e["admin"],
                                   org.RoleGrant(user_id=e["otra"], role=org.Role.implementador))
        assert res["role"] == "implementador"
        await s.rollback()


async def test_conceder_dpo_con_una_fila_desconocida_falla_cerrada(fabrica):
    async with fabrica() as s:
        e = await _escenario(s, ROL_FUTURO)
        with pytest.raises(org.SoDViolation):
            await org.grant_role(s, e["t"], e["admin"], org.RoleGrant(user_id=e["otra"], role=org.Role.dpo))
        await s.rollback()


async def test_la_sod_conocida_sigue_igual(fabrica):
    async with fabrica() as s:
        e = await _escenario(s, rol_extra="coordinador")
        with pytest.raises(org.SoDViolation):
            await org.grant_role(s, e["t"], e["admin"], org.RoleGrant(user_id=e["otra"], role=org.Role.dpo))
        await s.rollback()


def _persona(correo: str, rol: str) -> dict:
    return {"personas": [{"nombre": "Persona Ficticia", "cargo": "Cargo", "email": correo, "rol": rol}]}


async def test_invitar_dpo_con_una_fila_desconocida_falla_cerrada(fabrica):
    async with fabrica() as s:
        e = await _escenario(s, ROL_FUTURO)
        with pytest.raises(ErrorNegocio):
            await org.guardar_paso_alta(s, e["t"], e["admin"], "personas", _persona(e["correo"], "dpo"), None)
        await s.rollback()
