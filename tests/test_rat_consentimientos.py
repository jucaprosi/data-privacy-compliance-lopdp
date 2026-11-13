"""Árbitro de RAT-07 contra PostgreSQL. ¤rat ¤evidencias ¤arbitro

Contrato: governance/especificaciones/RAT-07.md §5.

Mutación documentada: en features/rat/rat_service.py se quitó temporalmente la comparación de campos
(``campos_identificadores_presentes(cuerpo) or set(cuerpo) - propios``) y el modelo dejó de rechazar el campo
``email``; ``test_consentimiento_sin_identidad`` falló al recibir 201 en vez de 422 TITULAR_IDENTIFICADO.
Restaurada la comparación, este archivo vuelve a pasar.
"""
import os
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker

from app_core.db.session import fijar_contexto_rls
from app_core.errors import ErrorNegocio

pytestmark = pytest.mark.asyncio

ROLES = ("dpo", "coordinador", "implementador", "admin_organizacion", "responsable_area")


@pytest_asyncio.fixture
async def env(db_engine):
    assert os.environ.get("TEST_DATABASE_URL")
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    ta, tb = f"rat7-{uuid4().hex}", f"rat7-{uuid4().hex}"
    usuarios = {r: f"rat7-u-{uuid4().hex}" for r in ROLES}
    usuarios_b = {"coordinador": f"rat7-u-{uuid4().hex}"}
    try:
        async with factory() as s:
            for tenant in (ta, tb):
                await s.execute(text("INSERT INTO tenants (id,nombre_comercial,razon_social,ruc_identificacion) VALUES (:t,:t,:t,:t)"), {"t": tenant})
            for tenant, grupo in ((ta, usuarios), (tb, usuarios_b)):
                for rol, usuario in grupo.items():
                    await s.execute(text("INSERT INTO users (id,email,nombre) VALUES (:u,:e,'RAT-07')"),
                                    {"u": usuario, "e": f"{usuario}@example.test"})
                    await fijar_contexto_rls(s, tenant, usuario)
                    await s.execute(text("INSERT INTO user_tenant_roles (id,user_id,tenant_id,role) VALUES (:i,:u,:t,:r)"),
                                    {"i": str(uuid4()), "u": usuario, "t": tenant, "r": rol})
            await s.commit()
        yield {"factory": factory, "a": ta, "b": tb, "usuarios": usuarios, "usuarios_b": usuarios_b}
    finally:
        async with factory() as s:
            for tenant in (ta, tb):
                await fijar_contexto_rls(s, tenant)
                for sql in ("DELETE FROM audit_events WHERE tenant_id=:t", "DELETE FROM consentimientos_registro WHERE tenant_id=:t",
                            "DELETE FROM colectivos_titulares WHERE tenant_id=:t", "DELETE FROM rat_versiones WHERE tenant_id=:t",
                            "DELETE FROM rat_actividades WHERE tenant_id=:t",
                            "DELETE FROM user_tenant_roles WHERE tenant_id=:t", "DELETE FROM tenants WHERE id=:t"):
                    await s.execute(text(sql), {"t": tenant})
            for usuario in [*usuarios.values(), *usuarios_b.values()]:
                await s.execute(text("DELETE FROM users WHERE id=:u"), {"u": usuario})
            await s.commit()


@pytest_asyncio.fixture
async def cliente(env):
    from api.routers.rat import get_rat_session, router as rat
    from api.routers.rat_consentimientos import router as consentimientos

    app = FastAPI()
    app.include_router(rat, prefix="/api/v1")
    app.include_router(consentimientos, prefix="/api/v1")

    @app.exception_handler(ErrorNegocio)
    async def _negocio(_, exc: ErrorNegocio):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail, "code": exc.code})

    async def sesion(tenant: str = Header(..., alias="X-Tenant-ID"), usuario: str = Header(..., alias="X-User-ID")):
        async with env["factory"]() as s:
            await s.execute(text("SET LOCAL ROLE lopdp_app"))
            await fijar_contexto_rls(s, tenant, usuario)
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    app.dependency_overrides[get_rat_session] = sesion
    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://rat.test") as c:
        yield c


def _h(env, rol="coordinador", tenant="a"):
    grupo = env["usuarios"] if tenant == "a" else env["usuarios_b"]
    return {"X-Tenant-ID": env[tenant], "X-User-ID": grupo[rol], "X-Role": rol}


async def _tratamiento(cliente, env) -> str:
    r = await cliente.post("/api/v1/rat/actividades", headers=_h(env), json={
        "codigo": "RAT-C", "nombre": "Clientes", "area_responsable": "Ventas", "finalidad": "Venta",
        "plazo_conservacion": "5 años"})
    assert r.status_code == 200, r.text
    return r.json()["actividad"]["id"]


async def _colectivo(cliente, env, rat_id, **cambios) -> str:
    cuerpo = {"nombre": "Socios", "base_legitimacion": "CONSENTIMIENTO", "texto_version": "v1", **cambios}
    r = await cliente.post(f"/api/v1/rat/{rat_id}/colectivos", json=cuerpo, headers=_h(env))
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _registro(**cambios):
    return {"fecha": "2026-11-01", "canal": "web", "cantidad": 10, "texto_version": "v1", **cambios}


@pytest.mark.parametrize("campo", ["email", "cedula", "nombre_titular", "telefono", "campo_ajeno"])
async def test_consentimiento_sin_identidad(cliente, env, campo):
    rat_id = await _tratamiento(cliente, env)
    colectivo = await _colectivo(cliente, env, rat_id)
    r = await cliente.post(f"/api/v1/rat/colectivos/{colectivo}/consentimientos",
                           json=_registro(**{campo: "x"}), headers=_h(env))
    assert r.status_code == 422 and r.json()["code"] == "TITULAR_IDENTIFICADO", r.text
    r = await cliente.post(f"/api/v1/rat/{rat_id}/colectivos",
                           json={"nombre": "A", "base_legitimacion": "CONSENTIMIENTO", campo: "x"}, headers=_h(env))
    assert r.status_code == 422 and r.json()["code"] == "TITULAR_IDENTIFICADO", r.text
    total = (await cliente.get(f"/api/v1/rat/colectivos/{colectivo}/consentimientos", headers=_h(env))).json()
    assert total["registros"] == [] and total["total"] == 0


async def test_consentimiento_agrega(cliente, env):
    rat_id = await _tratamiento(cliente, env)
    colectivo = await _colectivo(cliente, env, rat_id)
    for fecha, canal, n in (("2026-11-01", "web", 10), ("2026-11-02", "presencial", 5), ("2026-12-01", "otro", 7)):
        r = await cliente.post(f"/api/v1/rat/colectivos/{colectivo}/consentimientos",
                               json=_registro(fecha=fecha, canal=canal, cantidad=n), headers=_h(env))
        assert r.status_code == 201, r.text
        assert "email" not in r.json() and "cedula" not in r.json()
    r = await cliente.get(f"/api/v1/rat/colectivos/{colectivo}/consentimientos?desde=2026-11-01&hasta=2026-11-30",
                          headers=_h(env, "dpo"))
    cuerpo = r.json()
    assert r.status_code == 200 and cuerpo["total"] == 15 and len(cuerpo["registros"]) == 2
    todo = (await cliente.get(f"/api/v1/rat/colectivos/{colectivo}/consentimientos", headers=_h(env))).json()
    assert todo["total"] == 22


@pytest.mark.parametrize("cantidad,canal", [(0, "web"), (-3, "web"), (5, "fax")])
async def test_registro_invalido_422(cliente, env, cantidad, canal):
    rat_id = await _tratamiento(cliente, env)
    colectivo = await _colectivo(cliente, env, rat_id)
    r = await cliente.post(f"/api/v1/rat/colectivos/{colectivo}/consentimientos",
                           json=_registro(cantidad=cantidad, canal=canal), headers=_h(env))
    assert r.status_code == 422 and r.json()["code"] == "VALIDACION_CONSENTIMIENTO"


async def test_roles_y_colectivo_ajeno(cliente, env):
    rat_id = await _tratamiento(cliente, env)
    colectivo = await _colectivo(cliente, env, rat_id)
    cuerpo = {"nombre": "Otros", "base_legitimacion": "OBLIGACION_LEGAL"}
    for rol in ("dpo", "responsable_area"):
        assert (await cliente.post(f"/api/v1/rat/{rat_id}/colectivos", json=cuerpo, headers=_h(env, rol))).status_code == 403
        assert (await cliente.get(f"/api/v1/rat/{rat_id}/colectivos", headers=_h(env, rol))).status_code == 200
    for rol in ("implementador", "admin_organizacion"):
        assert (await cliente.post(f"/api/v1/rat/{rat_id}/colectivos", json=cuerpo, headers=_h(env, rol))).status_code == 201
    r = await cliente.put(f"/api/v1/rat/colectivos/{colectivo}", headers=_h(env),
                          json={"nombre": "Socios 2", "base_legitimacion": "OBLIGACION_LEGAL"})
    assert r.status_code == 200 and r.json()["nombre"] == "Socios 2" and r.json()["texto_version"] is None
    # Otra organización: el colectivo no existe para ella.
    r = await cliente.get(f"/api/v1/rat/colectivos/{colectivo}/consentimientos", headers=_h(env, tenant="b"))
    assert r.status_code == 404 and r.json()["code"] == "COLECTIVO_NO_ENCONTRADO"


async def test_rls_consentimientos(cliente, env):
    rat_id = await _tratamiento(cliente, env)
    colectivo = await _colectivo(cliente, env, rat_id)
    await cliente.post(f"/api/v1/rat/colectivos/{colectivo}/consentimientos", json=_registro(), headers=_h(env))
    async with env["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, env["b"])
        for tabla in ("colectivos_titulares", "consentimientos_registro"):
            assert (await s.execute(text(f"SELECT count(*) FROM {tabla}"))).scalar_one() == 0
        with pytest.raises(DBAPIError):
            await s.execute(text("INSERT INTO colectivos_titulares (id,tenant_id,tratamiento_id,nombre,base_legitimacion) "
                                 "VALUES ('x',:t,'r','n','CONSENTIMIENTO')"), {"t": env["a"]})
    async with env["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, env["a"])
        assert (await s.execute(text("SELECT count(*) FROM consentimientos_registro"))).scalar_one() == 1
        # Append-only: lopdp_app no actualiza ni borra registros.
        for sql in ("UPDATE consentimientos_registro SET cantidad = 99", "DELETE FROM consentimientos_registro"):
            with pytest.raises(DBAPIError):
                async with s.begin_nested():
                    await s.execute(text(sql))
