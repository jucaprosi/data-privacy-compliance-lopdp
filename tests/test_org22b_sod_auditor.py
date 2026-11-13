# -*- coding: utf-8 -*-
# ¤rbac-tenant ¤arbitro
"""ORG-22: `dpo` y `auditor` son exclusivos (INV_LOPDP_AUDITOR_SOLE_ROLE, PRD EVYDENTIA §3; razón: INV_LOPDP_FOUR_EYES_CLOSURE; decisión del CTO, 2026-11-12).

Quien tiene uno no tiene ningún otro rol activo en el tenant. Dos capas: la compuerta (`grant_role`) y el trigger
`fn_utr_dpo_sod`. Corren contra PostgreSQL real (`TEST_DATABASE_URL`: el PG16 del arnés o evydentia-pruebas, nunca
producción) y terminan con rollback.

Mutaciones documentadas (cada una hace fallar su caso):
  1. quitar la tupla (auditor, dpo) de INCOMPATIBILIDADES_ROLES → test_auditor_y_dpo_se_excluyen_en_las_dos_direcciones;
  2. quitar una tupla (auditor, X) → el caso de ese rol en test_auditor_frente_a_los_otros_cuatro_roles;
  3. quitar 'auditor' de fn_utr_dpo_sod → test_el_trigger_rechaza_la_insercion_directa;
  4. volver a `nuevo == Role.dpo` en motivo_sod_tolerante → test_auditor_con_un_rol_desconocido_se_rechaza;
  5. reemplazar el recuento de la migración por un DELETE → test_la_migracion_aborta_con_el_recuento (borra la fila);
  6. añadir el par del auditor a `roles_validos` de la excepción → test_una_excepcion_temporal_no_habilita_al_auditor;
  7. quitar el pg_advisory_xact_lock de fn_utr_dpo_sod → test_dos_inserciones_simultaneas_no_burlan_la_exclusividad
     (la segunda no espera y las dos pasan).
"""
from __future__ import annotations

import asyncio
import importlib.util
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from features.organizacion import organizacion_service as org

RAIZ = Path(__file__).resolve().parents[1]
CUATRO_ROLES = ("coordinador", "responsable_area", "implementador", "admin_organizacion")


@pytest.fixture
def fabrica(db_engine):
    return async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)


async def _dar(s, t: str, uid: str, rol: str) -> None:
    await s.execute(text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, :r)"),
                    {"i": f"utr-{uuid.uuid4().hex[:8]}", "u": uid, "t": t, "r": rol})


async def _escenario(s, rol_de_x: str | None = None, con_trigger: bool = False) -> dict:
    """Por omisión apaga el trigger (se revierte con el rollback) para que la prueba mida solo la compuerta."""
    sufijo = uuid.uuid4().hex[:8]
    t, admin, x = f"t-{sufijo}", f"u-adm-{sufijo}", f"u-x-{sufijo}"
    await s.execute(text(
        "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
        "VALUES (:id, 'Org 22', 'Org 22 SA', :ruc, 'mediana')"), {"id": t, "ruc": f"RUC{sufijo}"})
    for uid in (admin, x):
        await s.execute(text("INSERT INTO users (id, email, nombre, activo) VALUES (:i, :e, 'Persona', TRUE)"),
                        {"i": uid, "e": f"{uid}@org22.invalid"})
    if not con_trigger:
        await s.execute(text("ALTER TABLE user_tenant_roles DISABLE TRIGGER trg_utr_dpo_sod"))
    await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": t})
    await _dar(s, t, admin, "admin_organizacion")
    if rol_de_x:
        await _dar(s, t, x, rol_de_x)
    return {"t": t, "admin": admin, "x": x}


async def _conceder(s, e: dict, rol: str):
    return await org.grant_role(s, e["t"], e["admin"], org.RoleGrant(user_id=e["x"], role=org.Role(rol)))


@pytest.mark.asyncio
@pytest.mark.parametrize("tiene,pide", [("auditor", "dpo"), ("dpo", "auditor")])
async def test_auditor_y_dpo_se_excluyen_en_las_dos_direcciones(fabrica, tiene, pide):
    async with fabrica() as s:
        e = await _escenario(s, tiene)
        with pytest.raises(org.SoDViolation):
            await _conceder(s, e, pide)
        await s.rollback()


@pytest.mark.asyncio
@pytest.mark.parametrize("otro", CUATRO_ROLES)
async def test_auditor_frente_a_los_otros_cuatro_roles(fabrica, otro):
    async with fabrica() as s:
        e = await _escenario(s, "auditor")
        with pytest.raises(org.SoDViolation):
            await _conceder(s, e, otro)  # el auditor no recibe otro rol
        await s.rollback()
    async with fabrica() as s:
        e = await _escenario(s, otro)
        with pytest.raises(org.SoDViolation):
            await _conceder(s, e, "auditor")  # quien tiene otro rol no recibe auditor
        await s.rollback()


@pytest.mark.asyncio
@pytest.mark.parametrize("primero,segundo", [("auditor", "dpo"), ("dpo", "auditor"),
                                             ("auditor", "implementador"), ("implementador", "auditor")])
async def test_el_trigger_rechaza_la_insercion_directa(fabrica, primero, segundo):
    async with fabrica() as s:
        e = await _escenario(s, primero, con_trigger=True)
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": e["t"]})
        with pytest.raises(DBAPIError) as err:
            async with s.begin_nested():
                await _dar(s, e["t"], e["x"], segundo)
        assert "SoD" in str(err.value.orig)
        await s.rollback()


@pytest.mark.asyncio
async def test_auditor_con_un_rol_desconocido_se_rechaza(fabrica):
    async with fabrica() as s:
        e = await _escenario(s)
        await s.execute(text("ALTER TABLE user_tenant_roles DROP CONSTRAINT ck_utr_role"))  # se revierte con el rollback
        await _dar(s, e["t"], e["x"], "rol_de_una_version_futura")
        with pytest.raises(org.SoDViolation):
            await _conceder(s, e, "auditor")
        await s.rollback()


def _migracion():
    ruta = RAIZ / "alembic" / "versions" / "org22b_auditor_sod_trigger.py"
    spec = importlib.util.spec_from_file_location("org22b_auditor_sod_trigger", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.mark.asyncio
async def test_la_migracion_aborta_con_el_recuento(fabrica):
    modulo = _migracion()
    async with fabrica() as s:
        e = await _escenario(s)
        await _dar(s, e["t"], e["x"], "dpo")
        await _dar(s, e["t"], e["x"], "auditor")

        def correr(conexion):
            with Operations.context(MigrationContext.configure(conexion)):
                modulo.upgrade()

        conexion = await s.connection()
        with pytest.raises(Exception) as err:
            await conexion.run_sync(correr)
        assert "1 par(es)" in str(err.value)
        filas = (await s.execute(text(
            "SELECT count(*) FROM user_tenant_roles WHERE tenant_id = :t AND user_id = :u"),
            {"t": e["t"], "u": e["x"]})).scalar_one()
        assert filas == 2, "la migración no modifica ni borra filas"
        await s.rollback()


@pytest.mark.asyncio
async def test_una_excepcion_temporal_no_habilita_al_auditor(fabrica):
    async with fabrica() as s:
        e = await _escenario(s, "coordinador")
        for existente, solicitado in (("coordinador", "auditor"), ("auditor", "coordinador"),
                                      ("auditor", "responsable_area")):
            with pytest.raises(org.RbacError) as err:
                await org.solicitar_excepcion_sod(s, e["t"], e["admin"], org.ExcepcionSoDCreate(
                    user_id=e["x"], rol_existente=existente, rol_solicitado=solicitado,
                    motivo="motivo de prueba",
                    control_compensatorio_tipo=next(iter(org.ControlCompensatorioTipo)),
                    control_compensatorio_detalle="detalle de prueba",
                    valid_to=datetime.now(timezone.utc) + timedelta(days=5)))
            assert err.value.code == 400
        with pytest.raises(org.SoDViolation):
            await _conceder(s, e, "auditor")
        await s.rollback()


@pytest.mark.asyncio
async def test_dos_inserciones_simultaneas_no_burlan_la_exclusividad(fabrica):
    """Seguridad (#675): 'auditor' y 'coordinador' del mismo par en dos transacciones concurrentes.

    El candado por (tenant, usuario) hace esperar a la segunda; al confirmar la primera, la segunda ve su fila y el
    trigger la rechaza. Sin el candado, la segunda no espera y las dos pasan (mutación 7).
    """
    sufijo = uuid.uuid4().hex[:8]
    t, x = f"t-conc-{sufijo}", f"u-conc-{sufijo}"
    async with fabrica() as s:
        await s.execute(text(
            "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
            "VALUES (:id, 'Org conc', 'Org conc SA', :ruc, 'mediana')"), {"id": t, "ruc": f"RUC{sufijo}"})
        await s.execute(text("INSERT INTO users (id, email, nombre, activo) VALUES (:i, :e, 'Persona', TRUE)"),
                        {"i": x, "e": f"{x}@org22.invalid"})
        await s.commit()
    a, b = fabrica(), fabrica()
    try:
        for ses in (a, b):
            await ses.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": t})
        await _dar(a, t, x, "auditor")  # transacción A abierta, con el candado tomado

        async def segunda():
            await _dar(b, t, x, "coordinador")
            await b.commit()

        tarea = asyncio.create_task(segunda())
        await asyncio.sleep(1.5)
        assert not tarea.done(), "la segunda inserción no esperó el candado: las dos pasarían"
        await a.commit()
        with pytest.raises(DBAPIError) as exc:
            await asyncio.wait_for(tarea, timeout=10)
        assert "SoD auditor" in str(exc.value)
    finally:
        await a.rollback()
        await b.rollback()
        await a.close()
        await b.close()
        async with fabrica() as s:
            await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": t})
            await s.execute(text("ALTER TABLE user_tenant_roles DISABLE TRIGGER trg_utr_dpo_sod"))
            await s.execute(text("DELETE FROM user_tenant_roles WHERE tenant_id = :t"), {"t": t})
            await s.execute(text("ALTER TABLE user_tenant_roles ENABLE TRIGGER trg_utr_dpo_sod"))
            await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": x})
            await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t})
            await s.commit()
