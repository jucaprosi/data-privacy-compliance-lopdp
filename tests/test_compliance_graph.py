"""Grafo de cumplimiento: interacciones entre el RAT y los riesgos/EIPD.

Desde RAT-01 el RAT vive en PostgreSQL y su compuerta es asíncrona: las pruebas usan una
organización de prueba en la rama de la base (se omiten sin TEST_DATABASE_URL). Los riesgos siguen
simulados en memoria hasta que la EIPD se guarde en la base (RAT-03).
"""
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app_core.db.session import fijar_contexto_rls
from features.rat.domain.models import ActividadRAT
from features.rat.rat_service import editar_actividad_rat, eliminar_actividad_rat, registrar_actividad_rat

pytestmark = pytest.mark.asyncio


class RiesgosStoreMock:
    """Riesgos vinculados a una actividad del RAT (simulado hasta RAT-03)."""
    _riesgos: dict = {}

    @classmethod
    def asociar_riesgo(cls, rat_id, eipd_requerido):
        cls._riesgos[rat_id] = {"eipd_requerido": eipd_requerido}

    @classmethod
    def obtener_riesgo(cls, rat_id):
        return cls._riesgos.get(rat_id)

    @classmethod
    def eliminar_riesgos_rat(cls, rat_id):
        cls._riesgos.pop(rat_id, None)


@pytest_asyncio.fixture
async def sesion_tenant(db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    tenant = f"cg-{uuid4().hex}"
    async with factory() as s:
        await s.execute(text(
            "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:t, :t, :t, :t)"
        ), {"t": tenant})
        await s.commit()
    try:
        async with factory() as s:
            await fijar_contexto_rls(s, tenant)
            yield s, tenant
            await s.commit()
    finally:
        async with factory() as s:
            await fijar_contexto_rls(s, tenant)
            await s.execute(text("DELETE FROM audit_events WHERE tenant_id = :t"), {"t": tenant})
            await s.execute(text("DELETE FROM rat_actividades WHERE tenant_id = :t"), {"t": tenant})
            await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": tenant})
            await s.commit()


async def modificar_tratamiento_rat(session, tenant, actividad: ActividadRAT, es_gran_escala: bool):
    """Orquesta la modificación del RAT y el recálculo de riesgos."""
    guardada = await editar_actividad_rat(
        session, tenant, actividad.id, {"es_gran_escala": es_gran_escala, "requiere_eipd": es_gran_escala}
    )
    RiesgosStoreMock.asociar_riesgo(guardada.id, guardada.requiere_eipd)
    return guardada


async def orquestar_eliminacion_rat(session, tenant, rat_id: str):
    """Da de baja la actividad y elimina sus riesgos vinculados en el mismo paso."""
    assert await eliminar_actividad_rat(session, tenant, rat_id)
    RiesgosStoreMock.eliminar_riesgos_rat(rat_id)


async def test_compliance_graph_recalculo_modificacion(sesion_tenant):
    """Al modificar un tratamiento a gran escala, las obligaciones de EIPD se recalculan."""
    session, tenant = sesion_tenant
    guardada = await registrar_actividad_rat(session, ActividadRAT(
        tenant_id=tenant, codigo="RAT-TEST-01", nombre="Tratamiento Test", area_responsable="IT", finalidad="Prueba",
    ))
    RiesgosStoreMock.asociar_riesgo(guardada.id, False)
    assert RiesgosStoreMock.obtener_riesgo(guardada.id)["eipd_requerido"] is False

    modificada = await modificar_tratamiento_rat(session, tenant, guardada, es_gran_escala=True)

    assert modificada.requiere_eipd is True
    assert RiesgosStoreMock.obtener_riesgo(modificada.id)["eipd_requerido"] is True


async def test_compliance_graph_eliminacion_atomica(sesion_tenant):
    """Al dar de baja un tratamiento del RAT, sus riesgos vinculados se eliminan."""
    session, tenant = sesion_tenant
    guardada = await registrar_actividad_rat(session, ActividadRAT(
        tenant_id=tenant, codigo="RAT-TEST-02", nombre="Tratamiento a eliminar", area_responsable="IT", finalidad="Prueba",
    ))
    RiesgosStoreMock.asociar_riesgo(guardada.id, True)
    assert RiesgosStoreMock.obtener_riesgo(guardada.id) is not None

    await orquestar_eliminacion_rat(session, tenant, guardada.id)

    assert RiesgosStoreMock.obtener_riesgo(guardada.id) is None
    assert await editar_actividad_rat(session, tenant, guardada.id, {"nombre": "x"}) is None
