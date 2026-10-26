# ¤rat ¤diagnostico ¤arbitro
"""RAT-02: plantilla sectorial de salud.

La plantilla se valida contra el modelo del RAT sin base; la carga se prueba contra PostgreSQL
(rama Neon de revisión): crea exactamente lo elegido, no duplica, respeta el sector y la SoD.
"""
import os
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI, Header
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from features.rat.domain.models import BaseLegitimacion, CategoriaTitular
from features.rat.services.plantilla_engine import cargar_plantilla, sector_de_la_organizacion

RUTA = "/api/v1/rat/plantillas"


# --- Plantilla (sin base) ---------------------------------------------------------------------

def test_la_plantilla_de_salud_es_valida_contra_el_modelo():
    plantilla = cargar_plantilla("salud")
    actividades = plantilla["actividades"]
    assert len(actividades) == 25
    codigos = [e["actividad"]["codigo"] for e in actividades]
    assert len(set(codigos)) == 25
    for e in actividades:
        a = e["actividad"]
        BaseLegitimacion(a["base_legal"])
        [CategoriaTitular(c) for c in a["categorias_titulares"]]
        assert a["origen"] == "plantilla:salud"
        assert e["actor_sugerido"]
        for sugerido in (e["base_legal_sugerida"], e["conservacion_sugerida"]):
            assert sugerido["estado"] == "sugerido, validar" and sugerido["texto"]


@pytest.mark.parametrize("sector, esperado", [
    ("Salud", "salud"), ("Clínica de salud privada", "salud"), ("Telecomunicaciones", None), ("", None), (None, None),
])
def test_sector_de_la_organizacion(sector, esperado):
    assert sector_de_la_organizacion(sector) == esperado


# --- Carga contra PostgreSQL ------------------------------------------------------------------



@pytest_asyncio.fixture
async def env(db_engine):
    from app_core.db.session import fijar_contexto_rls
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    salud, otra = f"pl-s-{uuid4().hex}", f"pl-o-{uuid4().hex}"
    roles = ("coordinador", "dpo", "implementador")
    usuarios = {(t, r): f"pl-u-{uuid4().hex}" for t in (salud, otra) for r in roles}
    try:
        async with factory() as s:
            for tenant, sector in ((salud, "Salud"), (otra, "Telecomunicaciones")):
                await s.execute(text(
                    "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, sector) "
                    "VALUES (:t, :t, :t, :t, :s)"
                ), {"t": tenant, "s": sector})
            for (tenant, rol), usuario in usuarios.items():
                await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, 'Plantilla')"),
                                {"u": usuario, "e": f"{usuario}@plantilla.test"})
                await fijar_contexto_rls(s, tenant, usuario)
                await s.execute(text(
                    "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, :r)"
                ), {"i": str(uuid4()), "u": usuario, "t": tenant, "r": rol})
            await s.commit()
        yield {"factory": factory, "salud": salud, "otra": otra, "usuarios": usuarios}
    finally:
        async with factory() as s:
            for tenant in (salud, otra):
                await fijar_contexto_rls(s, tenant)
                for sql in ("DELETE FROM audit_events WHERE tenant_id = :t",
                            "DELETE FROM rat_actividades WHERE tenant_id = :t",
                            "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
                            "DELETE FROM tenants WHERE id = :t"):
                    await s.execute(text(sql), {"t": tenant})
            for usuario in usuarios.values():
                await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": usuario})
            await s.commit()


@pytest_asyncio.fixture
async def cliente(env):
    from api.routers.rat import get_rat_session, router as router_rat
    from api.routers.rat_plantillas import router
    from app_core.db.session import fijar_contexto_rls
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.include_router(router_rat, prefix="/api/v1")

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
    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://pl.test") as c:
        yield c


def _h(env, rol="coordinador", tenant="salud"):
    return {"X-Tenant-ID": env[tenant], "X-User-ID": env["usuarios"][(env[tenant], rol)], "X-Role": rol}


@pytest.mark.asyncio
async def test_la_organizacion_de_salud_ve_la_plantilla_y_otra_no(cliente, env):
    salud = (await cliente.get(RUTA, headers=_h(env, "implementador"))).json()["plantillas"]
    assert [p["sector"] for p in salud] == ["salud"] and len(salud[0]["actividades"]) == 25
    assert (await cliente.get(RUTA, headers=_h(env, "coordinador", "otra"))).json()["plantillas"] == []


@pytest.mark.asyncio
async def test_cargar_crea_exactamente_lo_elegido_y_no_duplica(cliente, env):
    url = f"{RUTA}/salud/aplicar"
    primera = await cliente.post(url, json={"codigos": ["SALUD-001", "SALUD-003"]}, headers=_h(env))
    assert primera.status_code == 200, primera.text
    assert primera.json()["creadas"] == ["SALUD-001", "SALUD-003"] and primera.json()["omitidas"] == []

    segunda = await cliente.post(url, json={"codigos": ["SALUD-003", "SALUD-009"]}, headers=_h(env))
    assert segunda.json()["creadas"] == ["SALUD-009"] and segunda.json()["omitidas"] == ["SALUD-003"]

    rat = (await cliente.get("/api/v1/rat/actividades", headers=_h(env))).json()["actividades"]
    assert sorted(a["codigo"] for a in rat) == ["SALUD-001", "SALUD-003", "SALUD-009"]
    assert all(a["origen"] == "plantilla:salud" and "validarlas" in a["observaciones_dpo"] for a in rat)


@pytest.mark.asyncio
async def test_otra_organizacion_no_puede_cargar_la_plantilla_de_salud(cliente, env):
    r = await cliente.post(f"{RUTA}/salud/aplicar", json={"codigos": ["SALUD-001"]}, headers=_h(env, "coordinador", "otra"))
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_codigo_ajeno_a_la_plantilla_es_422_y_no_carga_nada(cliente, env):
    r = await cliente.post(f"{RUTA}/salud/aplicar", json={"codigos": ["SALUD-001", "SALUD-999"]}, headers=_h(env))
    assert r.status_code == 422
    assert (await cliente.get("/api/v1/rat/actividades", headers=_h(env))).json()["actividades"] == []


@pytest.mark.asyncio
@pytest.mark.parametrize("rol", ["dpo", "implementador"])
async def test_solo_el_coordinador_carga_la_plantilla(cliente, env, rol):
    r = await cliente.post(f"{RUTA}/salud/aplicar", json={"codigos": ["SALUD-001"]}, headers=_h(env, rol))
    assert r.status_code == 403
    if rol == "dpo":
        assert "Violación SoD" in r.json()["detail"]
