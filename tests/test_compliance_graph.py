"""Grafo RAT/EIPD sobre persistencia real, sin dobles de riesgos."""
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app_core.db.session import fijar_contexto_rls
from features.rat.domain.models import ActividadRAT
from features.rat.rat_service import (
    RiesgoEIPD, aprobar_eipd_rat, comprobar_deriva_eipd_rat, crear_eipd_rat,
    editar_actividad_rat, leer_eipd_rat, registrar_actividad_rat,
)

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def grafo(db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    tenant = f"cg-{uuid4().hex}"
    async with factory() as s:
        await s.execute(text("INSERT INTO tenants (id,nombre_comercial,razon_social,ruc_identificacion) VALUES (:t,:t,:t,:t)"), {"t": tenant})
        await s.commit()
    try:
        async with factory() as s:
            await fijar_contexto_rls(s, tenant)
            actividad = ActividadRAT(tenant_id=tenant, codigo="CG-01", nombre="Grafo",
                area_responsable="TI", finalidad="Prueba", volumen_titulares_12_meses=100)
            await registrar_actividad_rat(s, actividad)
            eipd = await crear_eipd_rat(s, tenant, actividad.id, "Inicial",
                [RiesgoEIPD("Pérdida de control", 3, 4, "Minimización")])
            await aprobar_eipd_rat(s, tenant, eipd["id"], "dpo-test")
            await s.commit()
        yield factory, tenant, actividad.id, eipd["id"]
    finally:
        async with factory() as s:
            await fijar_contexto_rls(s, tenant)
            for sql in ("DELETE FROM rat_eipd_riesgos WHERE tenant_id=:t", "DELETE FROM rat_eipd WHERE tenant_id=:t",
                        "DELETE FROM rat_actividades WHERE tenant_id=:t", "DELETE FROM tenants WHERE id=:t"):
                await s.execute(text(sql), {"t": tenant})
            await s.commit()


async def test_modificacion_rat_propaga_deriva_persistida(grafo):
    factory, tenant, rat_id, eipd_id = grafo
    async with factory() as s:
        await fijar_contexto_rls(s, tenant)
        await editar_actividad_rat(s, tenant, rat_id, {"volumen_titulares_12_meses": 126})
        assert await comprobar_deriva_eipd_rat(s, tenant, rat_id) is True
        assert (await leer_eipd_rat(s, tenant, eipd_id))["estado"] == "REQUIERE_ACTUALIZACION"
        await s.commit()


async def test_grafo_sobrevive_sesion_nueva(grafo):
    factory, tenant, _, eipd_id = grafo
    async with factory() as s:
        await fijar_contexto_rls(s, tenant)
        eipd = await leer_eipd_rat(s, tenant, eipd_id)
        assert eipd["riesgos"][0]["nivel"] == "ALTO"
