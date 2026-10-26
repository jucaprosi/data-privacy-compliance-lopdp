"""Árbitro RAT-03 contra PostgreSQL.

Mutación documentada: en features/rat/services/eipd_engine.py se cambió temporalmente
``MAXIMO_BAJO = 4`` por ``MAXIMO_BAJO = 5``. El caso de borde P×I=5 falló al obtener
BAJO en vez de MEDIO. Restaurada la constante, este archivo vuelve a pasar.
"""
import os
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI, Header
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker

from features.rat.services.eipd_engine import nivel_riesgo

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def eipd_env(db_engine):
    from app_core.db.session import fijar_contexto_rls
    assert os.environ.get("TEST_DATABASE_URL")
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    ta, tb = f"eipd-{uuid4().hex}", f"eipd-{uuid4().hex}"
    usuarios = {r: f"eipd-u-{uuid4().hex}" for r in
                ("dpo", "coordinador", "implementador", "admin_organizacion", "responsable_area")}
    try:
        async with factory() as s:
            for tenant in (ta, tb):
                await s.execute(text("INSERT INTO tenants (id,nombre_comercial,razon_social,ruc_identificacion) VALUES (:t,:t,:t,:t)"), {"t": tenant})
            for rol, usuario in usuarios.items():
                await s.execute(text("INSERT INTO users (id,email,nombre) VALUES (:u,:e,'EIPD test')"),
                                {"u": usuario, "e": f"{usuario}@example.test"})
                await fijar_contexto_rls(s, ta, usuario)
                await s.execute(text("INSERT INTO user_tenant_roles (id,user_id,tenant_id,role) VALUES (:i,:u,:t,:r)"),
                                {"i": str(uuid4()), "u": usuario, "t": ta, "r": rol})
            await s.commit()
        yield {"factory": factory, "a": ta, "b": tb, "usuarios": usuarios}
    finally:
        async with factory() as s:
            for tenant in (ta, tb):
                await fijar_contexto_rls(s, tenant)
                for sql in ("DELETE FROM audit_events WHERE tenant_id=:t", "DELETE FROM rat_eipd_riesgos WHERE tenant_id=:t",
                            "DELETE FROM rat_eipd WHERE tenant_id=:t", "DELETE FROM rat_actividades WHERE tenant_id=:t",
                            "DELETE FROM user_tenant_roles WHERE tenant_id=:t", "DELETE FROM tenants WHERE id=:t"):
                    await s.execute(text(sql), {"t": tenant})
            for usuario in usuarios.values():
                await s.execute(text("DELETE FROM users WHERE id=:u"), {"u": usuario})
            await s.commit()


@pytest_asyncio.fixture
async def cliente(eipd_env):
    from api.routers.rat_eipd import router
    from api.routers.rat import get_rat_session
    from app_core.db.session import fijar_contexto_rls
    app = FastAPI(); app.include_router(router, prefix="/api/v1")

    async def sesion(tenant: str = Header(..., alias="X-Tenant-ID"), usuario: str = Header(..., alias="X-User-ID")):
        async with eipd_env["factory"]() as s:
            await s.execute(text("SET LOCAL ROLE lopdp_app"))
            await fijar_contexto_rls(s, tenant, usuario)
            try:
                yield s; await s.commit()
            except Exception:
                await s.rollback(); raise
    app.dependency_overrides[get_rat_session] = sesion
    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://eipd.test") as c:
        yield c


def _h(env, rol="dpo"):
    return {"X-Tenant-ID": env["a"], "X-User-ID": env["usuarios"][rol], "X-Role": rol}


@pytest_asyncio.fixture
async def actividad(eipd_env):
    from app_core.db.session import fijar_contexto_rls
    from features.rat.domain.models import ActividadRAT
    from features.rat.rat_service import registrar_actividad_rat
    async with eipd_env["factory"]() as s:
        await fijar_contexto_rls(s, eipd_env["a"])
        a = ActividadRAT(tenant_id=eipd_env["a"], codigo="RAT-EIPD", nombre="Perfilado",
                         area_responsable="Datos", finalidad="Evaluación", volumen_titulares_12_meses=100)
        await registrar_actividad_rat(s, a); await s.commit()
    return a


def _payload(rat_id):
    return {"rat_id": rat_id, "descripcion": "Evaluación inicial", "riesgos": [
        {"descripcion": "Discriminación", "probabilidad": 5, "impacto": 5, "medida": "Revisión humana"}]}


async def test_bordes_nivel_calculado_por_servidor():
    for probabilidad, impacto, esperado in (
        (1, 4, "BAJO"), (1, 5, "MEDIO"), (3, 3, "MEDIO"),
        (2, 5, "ALTO"), (4, 4, "ALTO"), (4, 5, "CRITICO"),
    ):
        assert nivel_riesgo(probabilidad, impacto) == (probabilidad * impacto, esperado)


async def test_crear_leer_aprobar_y_permisos(cliente, eipd_env, actividad):
    creado = await cliente.post("/api/v1/rat/eipd", json=_payload(actividad.id), headers=_h(eipd_env))
    assert creado.status_code == 200, creado.text
    eipd = creado.json()["eipd"]
    assert eipd["riesgos"][0]["puntuacion"] == 25 and eipd["riesgos"][0]["nivel"] == "CRITICO"
    for rol in ("coordinador", "implementador", "admin_organizacion", "responsable_area"):
        assert (await cliente.get(f"/api/v1/rat/eipd/{eipd['id']}", headers=_h(eipd_env, rol))).status_code == 200
        assert (await cliente.patch(f"/api/v1/rat/eipd/{eipd['id']}", json={"descripcion": "No"}, headers=_h(eipd_env, rol))).status_code == 403
        assert (await cliente.post(f"/api/v1/rat/eipd/{eipd['id']}/aprobar", headers=_h(eipd_env, rol))).status_code == 403
    aprobado = await cliente.post(f"/api/v1/rat/eipd/{eipd['id']}/aprobar", headers=_h(eipd_env))
    assert aprobado.status_code == 200 and aprobado.json()["eipd"]["estado"] == "APROBADA"


async def test_deriva_estrictamente_mayor_a_25_por_ciento(cliente, eipd_env, actividad):
    creado = (await cliente.post("/api/v1/rat/eipd", json=_payload(actividad.id), headers=_h(eipd_env))).json()["eipd"]
    await cliente.post(f"/api/v1/rat/eipd/{creado['id']}/aprobar", headers=_h(eipd_env))
    from app_core.db.session import fijar_contexto_rls
    async with eipd_env["factory"]() as s:
        await fijar_contexto_rls(s, eipd_env["a"])
        await s.execute(text("UPDATE rat_actividades SET volumen_titulares_12_meses=125 WHERE id=:i"), {"i": actividad.id}); await s.commit()
    borde = await cliente.post(f"/api/v1/rat/eipd/rat/{actividad.id}/evaluar-deriva", headers=_h(eipd_env))
    assert borde.json() == {"requiere_actualizacion": False}
    async with eipd_env["factory"]() as s:
        await fijar_contexto_rls(s, eipd_env["a"])
        await s.execute(text("UPDATE rat_actividades SET volumen_titulares_12_meses=126 WHERE id=:i"), {"i": actividad.id}); await s.commit()
    deriva = await cliente.post(f"/api/v1/rat/eipd/rat/{actividad.id}/evaluar-deriva", headers=_h(eipd_env))
    assert deriva.json() == {"requiere_actualizacion": True}
    assert (await cliente.get(f"/api/v1/rat/eipd/{creado['id']}", headers=_h(eipd_env))).json()["eipd"]["estado"] == "REQUIERE_ACTUALIZACION"


async def test_rls_real_con_set_local_role(cliente, eipd_env, actividad):
    creado = (await cliente.post("/api/v1/rat/eipd", json=_payload(actividad.id), headers=_h(eipd_env))).json()["eipd"]
    async with eipd_env["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        for tenant, total in ((eipd_env["a"], 1), (eipd_env["b"], 0), ("", 0)):
            await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant})
            assert (await s.execute(text("SELECT count(*) FROM rat_eipd WHERE id=:i"), {"i": creado["id"]})).scalar_one() == total
        await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": eipd_env["b"]})
        with pytest.raises(DBAPIError):
            await s.execute(text("INSERT INTO rat_eipd (id,tenant_id,rat_id,estado,descripcion,volumen_titulares_aprobacion,version,creada_en,actualizada_en) VALUES (:i,:ta,:r,'BORRADOR','x',0,1,now(),now())"),
                            {"i": str(uuid4()), "ta": eipd_env["a"], "r": actividad.id})


async def _aprobar_y_cambiar(cliente, eipd_env, actividad, sql, params):
    """Aprueba una EIPD de la actividad, aplica un cambio al RAT y evalúa la deriva."""
    from app_core.db.session import fijar_contexto_rls
    creado = (await cliente.post("/api/v1/rat/eipd", json=_payload(actividad.id), headers=_h(eipd_env))).json()["eipd"]
    await cliente.post(f"/api/v1/rat/eipd/{creado['id']}/aprobar", headers=_h(eipd_env))
    async with eipd_env["factory"]() as s:
        await fijar_contexto_rls(s, eipd_env["a"])
        await s.execute(text(sql), {"i": actividad.id, **params}); await s.commit()
    r = await cliente.post(f"/api/v1/rat/eipd/rat/{actividad.id}/evaluar-deriva", headers=_h(eipd_env))
    return r.json()["requiere_actualizacion"]


async def test_reducir_titulares_no_es_deriva(cliente, eipd_env, actividad):
    """La regla es un aumento de más del 25 %: menos titulares no aumenta el riesgo."""
    assert await _aprobar_y_cambiar(cliente, eipd_env, actividad,
        "UPDATE rat_actividades SET volumen_titulares_12_meses=10 WHERE id=:i", {}) is False


async def test_anadir_biometricos_es_deriva(cliente, eipd_env, actividad):
    """Segunda regla del sensor (Aporte 29): aparecen datos biométricos que no estaban al aprobar."""
    assert await _aprobar_y_cambiar(cliente, eipd_env, actividad,
        "UPDATE rat_actividades SET categorias_datos=CAST(:c AS JSONB) WHERE id=:i",
        {"c": '["FINANCIEROS", "BIOMETRICOS"]'}) is True


async def test_otra_categoria_sin_biometricos_no_es_deriva(cliente, eipd_env, actividad):
    assert await _aprobar_y_cambiar(cliente, eipd_env, actividad,
        "UPDATE rat_actividades SET categorias_datos=CAST(:c AS JSONB) WHERE id=:i",
        {"c": '["FINANCIEROS"]'}) is False
