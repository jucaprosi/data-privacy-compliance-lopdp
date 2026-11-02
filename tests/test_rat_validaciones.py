"""Árbitro de RAT-05 contra PostgreSQL. ¤rat ¤hallazgos ¤arbitro

Contrato: governance/especificaciones/RAT-05.md §5.

Mutación documentada: en features/rat/services/validaciones_engine.py se sustituyó temporalmente la llamada a
``pasillo_roadmap.registrar_hallazgo_rat(...)`` por ``pass`` (validar sin generar hallazgo).
``test_rat_sens_genera_hallazgo``, ``test_rat_correccion_cierra_y_versiona`` y ``test_rat_hallazgo_idempotente``
fallaron al no encontrar el hallazgo.
Restaurada la llamada, este archivo vuelve a pasar.
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

from api.errores import ErrorNegocio
from app_core.db.session import fijar_contexto_rls
from features.rat.domain.models import ActividadRAT, CategoriaTitular, CondicionHabilitante
from features.rat.domain.validaciones import evaluar_reglas

pytestmark = pytest.mark.asyncio

ROLES = ("dpo", "coordinador", "implementador", "admin_organizacion", "responsable_area")


@pytest_asyncio.fixture
async def env(db_engine):
    assert os.environ.get("TEST_DATABASE_URL")
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    ta, tb = f"ratv-{uuid4().hex}", f"ratv-{uuid4().hex}"
    usuarios = {r: f"ratv-u-{uuid4().hex}" for r in ROLES}
    usuarios_b = {"coordinador": f"ratv-u-{uuid4().hex}"}
    try:
        async with factory() as s:
            for tenant in (ta, tb):
                await s.execute(text("INSERT INTO tenants (id,nombre_comercial,razon_social,ruc_identificacion) VALUES (:t,:t,:t,:t)"), {"t": tenant})
            for tenant, grupo in ((ta, usuarios), (tb, usuarios_b)):
                for rol, usuario in grupo.items():
                    await s.execute(text("INSERT INTO users (id,email,nombre) VALUES (:u,:e,'RAT-05')"),
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
                for sql in ("DELETE FROM audit_events WHERE tenant_id=:t", "DELETE FROM rat_versiones WHERE tenant_id=:t",
                            "UPDATE roadmap_tasks SET hallazgo_id=NULL WHERE tenant_id=:t",
                            "DELETE FROM hallazgos WHERE tenant_id=:t", "DELETE FROM rat_actividades WHERE tenant_id=:t",
                            "DELETE FROM user_tenant_roles WHERE tenant_id=:t", "DELETE FROM tenants WHERE id=:t"):
                    await s.execute(text(sql), {"t": tenant})
            for usuario in [*usuarios.values(), *usuarios_b.values()]:
                await s.execute(text("DELETE FROM users WHERE id=:u"), {"u": usuario})
            await s.commit()


@pytest_asyncio.fixture
async def cliente(env):
    from api.routers.rat import get_rat_session, router as rat
    from api.routers.rat_validaciones import router as validaciones

    app = FastAPI()
    app.include_router(rat, prefix="/api/v1")
    app.include_router(validaciones, prefix="/api/v1")

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


def _h(env, rol="coordinador"):
    return {"X-Tenant-ID": env["a"], "X-User-ID": env["usuarios"][rol], "X-Role": rol}


def _ficha(**cambios):
    return {
        "codigo": "RAT-V", "nombre": "Historia clínica", "area_responsable": "Salud", "finalidad": "Atención",
        "plazo_conservacion": "15 años", **cambios,
    }


async def _crear(cliente, env, **cambios) -> str:
    r = await cliente.post("/api/v1/rat/actividades", json=_ficha(**cambios), headers=_h(env))
    assert r.status_code == 200, r.text
    return r.json()["actividad"]["id"]


async def _hallazgos(env, rat_id):
    async with env["factory"]() as s:
        await fijar_contexto_rls(s, env["a"])
        filas = await s.execute(
            text("SELECT id, origen_ref, severidad, estado, control_ref, dimension FROM hallazgos "
                 "WHERE tenant_id=:t AND origen='rat' AND origen_ref LIKE :r ORDER BY origen_ref"),
            {"t": env["a"], "r": f"{rat_id}:%"},
        )
        return [dict(f) for f in filas.mappings().all()]


def _regla(cuerpo, codigo):
    return next(r for r in cuerpo["reglas"] if r["codigo"] == codigo)


# --- Reglas puras -------------------------------------------------------------------------------


async def test_reglas_puras():
    def cumple(ficha, codigo):
        return next(r for r in evaluar_reglas(ficha) if r.codigo == codigo).cumple

    completa = dict(plazo_conservacion="5 años")
    assert all(r.cumple for r in evaluar_reglas(ActividadRAT(**completa)))
    assert not cumple(ActividadRAT(datos_sensibles=True, **completa), "RAT-SENS")
    assert cumple(ActividadRAT(datos_sensibles=True, condicion_habilitante=CondicionHabilitante.ORDEN_JUDICIAL, **completa), "RAT-SENS")
    for disparador in (
        {"categorias_titulares": [CategoriaTitular.MENORES_EDAD]},
        {"decisiones_automatizadas": True},
        {"categorias_datos": ["Datos biométricos"]},
    ):
        assert not cumple(ActividadRAT(**disparador, **completa), "RAT-EIPD")
        assert cumple(ActividadRAT(requiere_eipd=True, **disparador, **completa), "RAT-EIPD")
    assert not cumple(ActividadRAT(), "RAT-PLAZO")


async def test_rat_base_con_valor_nulo():
    """Por la API hoy no falla: `base_legal` tiene valor por defecto (especificación, R1)."""
    regla = next(r for r in evaluar_reglas(ActividadRAT(base_legal=None)) if r.codigo == "RAT-BASE")
    assert regla.cumple is False and regla.severidad == "media"


# --- Aceptación ----------------------------------------------------------------------------------


async def test_rat_sens_genera_hallazgo(cliente, env):
    rid = await _crear(cliente, env, datos_sensibles=True)
    cuerpo = (await cliente.get(f"/api/v1/rat/{rid}/validaciones", headers=_h(env))).json()
    assert _regla(cuerpo, "RAT-SENS")["cumple"] is False
    hallazgos = await _hallazgos(env, rid)
    assert [h["origen_ref"] for h in hallazgos] == [f"{rid}:RAT-SENS"]
    assert hallazgos[0]["severidad"] == "alta" and hallazgos[0]["estado"] == "abierto"
    assert (hallazgos[0]["control_ref"], hallazgos[0]["dimension"]) == ("P10", "D02")
    assert cuerpo["hallazgo_id"] == hallazgos[0]["id"]


async def test_rat_correccion_cierra_y_versiona(cliente, env):
    rid = await _crear(cliente, env, datos_sensibles=True)
    r = await cliente.patch(f"/api/v1/rat/actividades/{rid}", headers=_h(env),
                            json={"condicion_habilitante": "CONSENTIMIENTO_EXPLICITO"})
    assert r.status_code == 200, r.text
    assert [h["estado"] for h in await _hallazgos(env, rid)] == ["cerrado"]
    cuerpo = (await cliente.get(f"/api/v1/rat/{rid}/validaciones", headers=_h(env))).json()
    assert _regla(cuerpo, "RAT-SENS")["cumple"] is True and cuerpo["hallazgo_id"] is None
    versiones = (await cliente.get(f"/api/v1/rat/{rid}/versiones", headers=_h(env))).json()["versiones"]
    assert [v["numero"] for v in versiones] == [1, 2]
    assert versiones[0]["creado_por"] == env["usuarios"]["coordinador"]
    primera = (await cliente.get(f"/api/v1/rat/{rid}/versiones/1", headers=_h(env))).json()
    segunda = (await cliente.get(f"/api/v1/rat/{rid}/versiones/2", headers=_h(env))).json()
    assert primera["condicion_habilitante"] is None
    assert segunda["condicion_habilitante"] == "CONSENTIMIENTO_EXPLICITO" and segunda["id"] == rid


async def test_rat_hallazgo_idempotente(cliente, env):
    rid = await _crear(cliente, env, datos_sensibles=True)
    r = await cliente.patch(f"/api/v1/rat/actividades/{rid}", json={"nombre": "Otro nombre"}, headers=_h(env))
    assert r.status_code == 200, r.text
    assert len(await _hallazgos(env, rid)) == 1


async def test_rat_reincidencia_reabre(cliente, env):
    rid = await _crear(cliente, env, plazo_conservacion="")
    assert (await _hallazgos(env, rid))[0]["severidad"] == "media"
    url = f"/api/v1/rat/actividades/{rid}"
    await cliente.patch(url, json={"plazo_conservacion": "5 años"}, headers=_h(env))
    assert [h["estado"] for h in await _hallazgos(env, rid)] == ["cerrado"]
    await cliente.patch(url, json={"plazo_conservacion": " "}, headers=_h(env))
    hallazgos = await _hallazgos(env, rid)
    assert [h["estado"] for h in hallazgos] == ["abierto"]
    async with env["factory"]() as s:
        await fijar_contexto_rls(s, env["a"])
        acciones = await s.execute(
            text("SELECT action, payload FROM audit_events WHERE tenant_id=:t AND entity_id=:h ORDER BY timestamp"),
            {"t": env["a"], "h": hallazgos[0]["id"]},
        )
        filas = acciones.all()
    assert [f[0] for f in filas] == ["registrado", "cerrado", "reabierto"]
    assert "origen_resuelto" in str(filas[1][1]) and "origen_reincidente" in str(filas[2][1])


async def test_baja_cierra_hallazgos_y_conserva_versiones(cliente, env):
    rid = await _crear(cliente, env, datos_sensibles=True)
    assert (await cliente.delete(f"/api/v1/rat/actividades/{rid}", headers=_h(env))).status_code == 200
    assert [h["estado"] for h in await _hallazgos(env, rid)] == ["cerrado"]
    assert len((await cliente.get(f"/api/v1/rat/{rid}/versiones", headers=_h(env))).json()["versiones"]) == 1


async def test_rls_rat_versiones(cliente, env):
    await _crear(cliente, env)
    async with env["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, env["b"])
        assert (await s.execute(text("SELECT count(*) FROM rat_versiones WHERE tenant_id=:t"), {"t": env["a"]})).scalar_one() == 0
        assert (await s.execute(text("SELECT count(*) FROM rat_versiones"))).scalar_one() == 0
        with pytest.raises(DBAPIError):
            await s.execute(
                text("INSERT INTO rat_versiones (id,tenant_id,tratamiento_id,numero,contenido) "
                     "VALUES (:i,:t,'x',1,'{}')"),
                {"i": str(uuid4()), "t": env["a"]},
            )
        await s.rollback()


@pytest.mark.parametrize("sql", ["UPDATE rat_versiones SET numero=9", "DELETE FROM rat_versiones"])
async def test_versiones_append_only(cliente, env, sql):
    await _crear(cliente, env)
    async with env["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, env["a"])
        with pytest.raises(DBAPIError):
            await s.execute(text(sql))
        await s.rollback()


async def test_tablas_rls_forzada(env):
    async with env["factory"]() as s:
        fila = (await s.execute(text(
            "SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE relname='rat_versiones'"
        ))).one()
    assert fila == (True, True)


async def test_ficha_ajena_no_encontrada_y_permisos(cliente, env):
    rid = await _crear(cliente, env)
    ajeno = {"X-Tenant-ID": env["b"], "X-User-ID": env["usuarios_b"]["coordinador"], "X-Role": "coordinador"}
    for ruta in ("validaciones", "versiones", "versiones/1"):
        r = await cliente.get(f"/api/v1/rat/{rid}/{ruta}", headers=ajeno)
        assert r.status_code == 404 and r.json()["code"] == "RAT_NO_ENCONTRADO"
        for rol in ROLES:
            assert (await cliente.get(f"/api/v1/rat/{rid}/{ruta}", headers=_h(env, rol))).status_code == 200
    faltante = await cliente.get(f"/api/v1/rat/{rid}/versiones/99", headers=_h(env))
    assert faltante.status_code == 404 and faltante.json()["code"] == "RAT_NO_ENCONTRADO"


async def test_condicion_fuera_del_catalogo_se_rechaza(cliente, env):
    r = await cliente.post("/api/v1/rat/actividades", json=_ficha(condicion_habilitante="INVENTADA"), headers=_h(env))
    assert r.status_code == 422
