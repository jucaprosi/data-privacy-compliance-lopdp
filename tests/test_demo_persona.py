# -*- coding: utf-8 -*-
# ¤demo ¤seguridad ¤rbac-tenant
"""DEMO-01: persona activa y «Ver como» de la demo (resolutor, 403 si es ajena, auditoría con el vendedor real).

Corren contra PostgreSQL real (`db_engine`: el PG16 del arnés o evydentia-pruebas, nunca producción) con el rol
`lopdp_app` (sin BYPASSRLS). Solo valores simulados y correos `.invalid`; el token de Google se sustituye por un
doble y las rutas de la demo corren con `AUTH_MODE=oidc`.

Mutaciones ejecutadas y restauradas el 2026-11-15 contra PG16 local (cada una pone en rojo las pruebas indicadas):
  - quitar la consulta por `es_demo` de `personas_del_tenant`: test_persona_de_un_tenant_que_no_es_demo_es_403;
  - quitar el filtro por tenant en `cambiar_persona` (aceptar cualquier `persona_usuario_id`):
    test_persona_de_otra_organizacion_demo_es_403, test_persona_inexistente_es_403,
    test_persona_de_un_tenant_que_no_es_demo_es_403 y test_post_persona_ajena_es_403_con_el_cuerpo_congelado;
  - no comprobar `DEMO_VENDEDORES` en cada petición: test_vendedor_retirado_es_401_y_la_sesion_queda_vencida y
    test_sin_lista_de_vendedores_la_demo_esta_cerrada;
  - no confirmar (`commit`) antes de lanzar el 401: test_a_los_60_minutos_sin_actividad_vence_y_queda_vencida y
    test_vendedor_retirado_es_401_y_la_sesion_queda_vencida (la baja se pierde con el rollback de la API);
  - renovar la actividad en cada petición: test_la_actividad_se_renueva_como_mucho_cada_60_segundos;
  - no dejar el evento de auditoría con el vendedor: test_cambiar_persona_deja_auditoria_con_el_vendedor_real;
  - `AUTO_REGISTRO = True` en cualquier entorno: test_el_resolutor_solo_se_registra_con_app_env_demo.
"""
from __future__ import annotations

import importlib
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app_core import security
from app_core.db.session import fijar_contexto_rls, get_session
from app_core.pasillo import demo as pasillo
from app_core.security import IdentidadVerificada
from features.demo.domain.errores import ErrorDemo
from features.demo.repo import sesiones_repo

# La compuerta pública no recibe el reloj: la sesión nace «ahora» y las pruebas de tiempo lo adelantan.
T0 = datetime.now(timezone.utc).replace(microsecond=0)
SUB = "sub-vendedor-ficticio"
EMAIL = "vendedor@demo.invalid"
RUTA = "/api/v1/demo/persona"


def _fabrica(db_engine):
    return async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def sesion_app(db_engine):
    """Sesión con el rol de la aplicación: la RLS de verdad. El rol dura entre transacciones (SET ROLE confirmado)."""
    async with _fabrica(db_engine)() as s:
        await s.execute(text("SET ROLE lopdp_app"))
        await s.commit()
        try:
            yield s
        finally:
            await s.rollback()
            await s.execute(text("RESET ROLE"))
            await s.commit()


@pytest_asyncio.fixture
async def mundo(db_engine, monkeypatch):
    """Una organización demo (admin, DPO, responsable de área), otra organización demo y una que no es demo."""
    monkeypatch.setenv("DEMO_VENDEDORES", EMAIL)
    sufijo = uuid.uuid4().hex[:8]
    t = {k: f"dm1-{k}-{sufijo}" for k in ("demo", "otra", "real")}
    u = {k: f"dm1-u{k}-{sufijo}" for k in ("admin", "dpo", "area", "otra", "real")}
    area = f"dm1-area-{sufijo}"
    fabrica = _fabrica(db_engine)
    async with fabrica() as s:
        for clave, tid in t.items():
            await s.execute(
                text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, es_demo) "
                     "VALUES (:id, :n, :r, :ruc, :demo)"),
                {"id": tid, "n": f"Organización {clave}", "r": f"Org {tid} SA", "ruc": f"RUC{tid[:20]}", "demo": clave != "real"})
        for clave, uid in u.items():
            await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :n)"),
                            {"u": uid, "e": f"{uid}@correo.invalid", "n": f"Persona {clave}"})
        await fijar_contexto_rls(s, t["demo"])
        await s.execute(text("INSERT INTO areas (id, tenant_id, nombre, codigo, nivel) VALUES (:i, :t, 'Unidad ficticia', 'DEMO-U', 'unidad')"),
                        {"i": area, "t": t["demo"]})
        for tid, uid, rol, ar in ((t["demo"], u["admin"], "admin_organizacion", None), (t["demo"], u["dpo"], "dpo", None),
                                  (t["demo"], u["area"], "responsable_area", area), (t["otra"], u["otra"], "admin_organizacion", None),
                                  (t["real"], u["real"], "admin_organizacion", None)):
            await fijar_contexto_rls(s, tid)
            await s.execute(text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role, area_id) VALUES (:i, :u, :t, :r, :a)"),
                            {"i": str(uuid.uuid4()), "u": uid, "t": tid, "r": rol, "a": ar})
        await sesiones_repo.insertar(s, SUB, EMAIL, t["demo"], u["admin"], T0)
        await s.commit()
    yield {"t": t, "u": u, "area": area}
    async with fabrica() as s:
        await s.execute(text("DELETE FROM demo_sesiones WHERE vendedor_sub = :s"), {"s": SUB})
        for tid in t.values():
            await fijar_contexto_rls(s, tid)
            for sentencia in ("DELETE FROM audit_events WHERE tenant_id = :t", "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
                              "DELETE FROM areas WHERE tenant_id = :t", "DELETE FROM tenants WHERE id = :t"):
                await s.execute(text(sentencia), {"t": tid})
        await s.execute(text("DELETE FROM users WHERE id LIKE :p"), {"p": f"dm1-u%-{sufijo}"})
        await s.commit()


async def _sesion_en_bd(db_engine) -> dict:
    async with _fabrica(db_engine)() as s:
        fila = (await s.execute(text(
            "SELECT estado, motivo_fin, persona_usuario_id, ultima_actividad FROM demo_sesiones WHERE vendedor_sub = :s "
            "ORDER BY iniciada_en DESC LIMIT 1"), {"s": SUB})).mappings().one()
        return dict(fila)


async def _eventos(db_engine, tenant: str, accion: str) -> list[dict]:
    async with _fabrica(db_engine)() as s:
        await fijar_contexto_rls(s, tenant)
        filas = (await s.execute(text(
            "SELECT user_id, payload FROM audit_events WHERE tenant_id = :t AND action = :a"), {"t": tenant, "a": accion})).mappings().all()
        return [dict(f) for f in filas]


# --- Resolutor ----------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_el_resolutor_devuelve_la_persona_activa(db_engine, mundo):
    async with sesion_app(db_engine) as s:
        persona = await pasillo.resolver_usuario(s, SUB, T0 + timedelta(seconds=5))
    assert persona.usuario_id == mundo["u"]["admin"]
    assert persona.rol == "admin_organizacion" and persona.rol_etiqueta == "Administrador de la organización"


@pytest.mark.asyncio
async def test_sin_sesion_es_401(db_engine, mundo):
    async with sesion_app(db_engine) as s:
        with pytest.raises(ErrorDemo) as e:
            await pasillo.resolver_usuario(s, "sub-sin-demo", T0)
    assert (e.value.status_code, e.value.codigo.codigo) == (401, "DEMO_VENCIDA")


@pytest.mark.asyncio
async def test_sesion_vencida_es_401(db_engine, mundo):
    async with _fabrica(db_engine)() as s:
        await s.execute(text("UPDATE demo_sesiones SET estado = 'vencida', motivo_fin = 'terminar', terminada_en = now() "
                             "WHERE vendedor_sub = :s"), {"s": SUB})
        await s.commit()
    async with sesion_app(db_engine) as s:
        with pytest.raises(ErrorDemo) as e:
            await pasillo.resolver_usuario(s, SUB, T0)
    assert e.value.codigo.codigo == "DEMO_VENCIDA"


@pytest.mark.asyncio
async def test_a_los_60_minutos_sin_actividad_vence_y_queda_vencida(db_engine, mundo):
    async with sesion_app(db_engine) as s:
        persona = await pasillo.resolver_usuario(s, SUB, T0 + timedelta(minutes=59))
        assert persona.rol == "admin_organizacion"
    async with sesion_app(db_engine) as s:
        with pytest.raises(ErrorDemo):
            await pasillo.resolver_usuario(s, SUB, T0 + timedelta(minutes=60))
    bd = await _sesion_en_bd(db_engine)
    assert (bd["estado"], bd["motivo_fin"]) == ("vencida", "inactividad")


@pytest.mark.asyncio
async def test_vendedor_retirado_es_401_y_la_sesion_queda_vencida(db_engine, mundo, monkeypatch):
    monkeypatch.setenv("DEMO_VENDEDORES", "otro.vendedor@demo.invalid")
    async with sesion_app(db_engine) as s:
        with pytest.raises(ErrorDemo) as e:
            await pasillo.resolver_usuario(s, SUB, T0 + timedelta(seconds=1))
        await s.rollback()  # lo que hace el gestor de sesión de la API al fallar la petición
    assert e.value.codigo.codigo == "DEMO_VENCIDA"
    assert (await _sesion_en_bd(db_engine))["estado"] == "vencida"
    eventos = await _eventos(db_engine, mundo["t"]["demo"], "DEMO_VENCIDA")
    assert len(eventos) == 1 and eventos[0]["payload"]["causa"] == "vendedor_retirado"
    assert eventos[0]["payload"]["vendedor_email"] == EMAIL


@pytest.mark.asyncio
async def test_sin_lista_de_vendedores_la_demo_esta_cerrada(db_engine, mundo, monkeypatch):
    monkeypatch.delenv("DEMO_VENDEDORES")
    async with sesion_app(db_engine) as s:
        with pytest.raises(ErrorDemo):
            await pasillo.resolver_usuario(s, SUB, T0)


@pytest.mark.asyncio
async def test_la_actividad_se_renueva_como_mucho_cada_60_segundos(db_engine, mundo):
    async with sesion_app(db_engine) as s:
        await pasillo.resolver_usuario(s, SUB, T0 + timedelta(seconds=30))
        await s.commit()
    assert (await _sesion_en_bd(db_engine))["ultima_actividad"] == T0
    async with sesion_app(db_engine) as s:
        await pasillo.resolver_usuario(s, SUB, T0 + timedelta(seconds=61))
        await s.commit()
    assert (await _sesion_en_bd(db_engine))["ultima_actividad"] == T0 + timedelta(seconds=61)


@pytest.mark.asyncio
async def test_el_rol_de_la_persona_es_su_unico_rol_en_la_base(db_engine, mundo):
    async with sesion_app(db_engine) as s:
        persona = await pasillo.resolver_usuario(s, SUB, T0)
        roles = await security.roles_activos(s, mundo["t"]["demo"], persona.usuario_id)
    assert roles == {persona.rol}


# --- Cambiar de persona -------------------------------------------------------------------------

async def _cambiar(db_engine, persona_id: str, ahora=None):
    from features.demo import demo_service

    async with sesion_app(db_engine) as s:
        persona = await demo_service.cambiar_persona(s, SUB, persona_id)
        await s.commit()
    return persona


@pytest.mark.asyncio
async def test_cambiar_a_una_persona_de_la_organizacion_demo(db_engine, mundo):
    persona = await _cambiar(db_engine, mundo["u"]["area"])
    assert (persona.rol, persona.unidad) == ("responsable_area", "Unidad ficticia")
    assert (await _sesion_en_bd(db_engine))["persona_usuario_id"] == mundo["u"]["area"]
    async with sesion_app(db_engine) as s:
        assert (await pasillo.resolver_usuario(s, SUB, T0)).usuario_id == mundo["u"]["area"]


@pytest.mark.asyncio
async def test_persona_de_otra_organizacion_demo_es_403(db_engine, mundo):
    with pytest.raises(ErrorDemo) as e:
        await _cambiar(db_engine, mundo["u"]["otra"])
    assert (e.value.status_code, e.value.codigo.codigo) == (403, "DEMO_PERSONA_AJENA")
    assert (await _sesion_en_bd(db_engine))["persona_usuario_id"] == mundo["u"]["admin"]
    assert await _eventos(db_engine, mundo["t"]["demo"], "DEMO_CAMBIO_PERSONA") == []


@pytest.mark.asyncio
async def test_persona_inexistente_es_403(db_engine, mundo):
    with pytest.raises(ErrorDemo) as e:
        await _cambiar(db_engine, "persona-que-no-existe")
    assert e.value.codigo.codigo == "DEMO_PERSONA_AJENA"


@pytest.mark.asyncio
async def test_persona_de_un_tenant_que_no_es_demo_es_403(db_engine, mundo):
    """Invariante 61: si el tenant de la sesión no es `es_demo`, ninguna persona vale."""
    async with _fabrica(db_engine)() as s:
        await s.execute(text("UPDATE tenants SET es_demo = false WHERE id = :t"), {"t": mundo["t"]["demo"]})
        await s.commit()
    with pytest.raises(ErrorDemo) as e:
        await _cambiar(db_engine, mundo["u"]["dpo"])
    assert e.value.codigo.codigo == "DEMO_PERSONA_AJENA"
    async with sesion_app(db_engine) as s:
        with pytest.raises(ErrorDemo):
            await pasillo.resolver_usuario(s, SUB, T0)


@pytest.mark.asyncio
async def test_cambiar_persona_deja_auditoria_con_el_vendedor_real(db_engine, mundo):
    await _cambiar(db_engine, mundo["u"]["dpo"])
    eventos = await _eventos(db_engine, mundo["t"]["demo"], "DEMO_CAMBIO_PERSONA")
    assert len(eventos) == 1
    carga = eventos[0]["payload"]
    assert (carga["vendedor_sub"], carga["vendedor_email"]) == (SUB, EMAIL)
    assert (carga["persona_usuario_id"], carga["rol"]) == (mundo["u"]["dpo"], "dpo")
    assert carga["hora"] and eventos[0]["user_id"] is None


@pytest.mark.asyncio
async def test_el_estado_lleva_las_personas_en_orden_y_nunca_al_vendedor(db_engine, mundo):
    from features.demo import demo_service

    async with sesion_app(db_engine) as s:
        estado = await demo_service.estado(s, SUB)
    cuerpo = estado.a_dict()
    assert [p["rol"] for p in cuerpo["personas"]] == ["admin_organizacion", "dpo", "responsable_area"]
    assert cuerpo["persona_activa"]["usuario_id"] == mundo["u"]["admin"]
    assert cuerpo["organizacion"] == {"tenant_id": mundo["t"]["demo"], "nombre": "Organización demo"}
    assert EMAIL not in str(cuerpo) and SUB not in str(cuerpo)


# --- API ----------------------------------------------------------------------------------------

@pytest_asyncio.fixture
async def api(db_engine, mundo, monkeypatch):
    from api.routers import demo_persona

    async def token(_valor):
        return IdentidadVerificada(sub=SUB, email=EMAIL)

    monkeypatch.setattr(demo_persona, "verificar_token_google", token)

    async def sesion_de_aplicacion():
        async with sesion_app(db_engine) as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    app = FastAPI()
    app.include_router(demo_persona.router, prefix="/api/v1")
    app.dependency_overrides[get_session] = sesion_de_aplicacion
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://prueba") as cliente:
        yield cliente


@pytest.mark.asyncio
async def test_post_persona_devuelve_la_persona_con_su_rol_y_no_al_vendedor(api, mundo):
    r = await api.post(RUTA, json={"persona_usuario_id": mundo["u"]["dpo"]}, headers={"Authorization": "Bearer t"})
    assert r.status_code == 200
    assert r.json() == {"usuario_id": mundo["u"]["dpo"], "nombre": "Persona dpo", "rol": "dpo",
                        "rol_etiqueta": "DPO", "unidad": None}
    assert EMAIL not in r.text and SUB not in r.text


@pytest.mark.asyncio
async def test_post_persona_ajena_es_403_con_el_cuerpo_congelado(api, mundo):
    r = await api.post(RUTA, json={"persona_usuario_id": mundo["u"]["otra"]}, headers={"Authorization": "Bearer t"})
    assert r.status_code == 403
    assert r.json() == {"codigo": "DEMO_PERSONA_AJENA", "mensaje": "Esa persona no pertenece a tu demostración"}


@pytest.mark.asyncio
async def test_post_persona_sin_token_es_401_y_no_toca_nada(api, mundo, db_engine):
    from api.routers import demo_persona

    r = await api.post(RUTA, json={"persona_usuario_id": mundo["u"]["dpo"]})
    assert r.status_code == 401
    assert (await _sesion_en_bd(db_engine))["persona_usuario_id"] == mundo["u"]["admin"]
    assert demo_persona.AUTO_REGISTRO is False


@pytest.mark.asyncio
async def test_una_cabecera_de_usuario_no_decide_quien_es_el_vendedor(api, mundo, db_engine, monkeypatch):
    from api.routers import demo_persona

    async def otro(_valor):
        return IdentidadVerificada(sub="sub-de-otro-vendedor", email="otro@demo.invalid")

    monkeypatch.setattr(demo_persona, "verificar_token_google", otro)
    r = await api.post(RUTA, json={"persona_usuario_id": mundo["u"]["dpo"]},
                       headers={"Authorization": "Bearer t", "X-User-ID": mundo["u"]["admin"], "X-Tenant-ID": mundo["t"]["demo"]})
    assert r.status_code == 401 and r.json()["codigo"] == "DEMO_VENCIDA"
    assert (await _sesion_en_bd(db_engine))["persona_usuario_id"] == mundo["u"]["admin"]


@pytest.mark.asyncio
async def test_require_role_autoriza_el_x_role_devuelto_contra_la_base(api, mundo, db_engine, monkeypatch):
    """El `rol` devuelto es el `X-Role` que sirve; `require_role` lo sigue comprobando en `user_tenant_roles`."""
    from api.rbac import require_role

    r = await api.post(RUTA, json={"persona_usuario_id": mundo["u"]["dpo"]}, headers={"Authorization": "Bearer t"})
    x_role = r.json()["rol"]

    async def token(_valor):
        return IdentidadVerificada(sub=SUB, email=EMAIL)

    monkeypatch.setenv("APP_ENV", "demo")
    monkeypatch.setenv("AUTH_MODE", "oidc")  # la demo nunca corre con cabeceras
    monkeypatch.setattr(security, "verificar_token_google", token)
    monkeypatch.setattr(security, "_resolutor_identidad", pasillo.resolver_usuario)

    async def sesion_de_aplicacion():
        async with sesion_app(db_engine) as s:
            yield s
            await s.commit()

    protegida = FastAPI()

    @protegida.get("/protegida")
    async def _protegida(ctx: dict = Depends(require_role("dpo", "admin_organizacion"))):
        return ctx

    protegida.dependency_overrides[get_session] = sesion_de_aplicacion
    cabeceras = {"Authorization": "Bearer t", "X-Tenant-ID": mundo["t"]["demo"]}
    async with AsyncClient(transport=ASGITransport(app=protegida), base_url="http://prueba") as cliente:
        bien = await cliente.get("/protegida", headers={**cabeceras, "X-Role": x_role})
        declarado = await cliente.get("/protegida", headers={**cabeceras, "X-Role": "admin_organizacion"})
    assert bien.status_code == 200 and bien.json()["user_id"] == mundo["u"]["dpo"]
    # admin_organizacion lo admite la ruta, pero no es un rol de la persona activa en la base: 403.
    assert declarado.status_code == 403 and "membres" in declarado.json()["detail"]


# --- Registro y entorno -------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fuera_de_demo_la_ruta_no_existe(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    from main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://prueba") as cliente:
        r = await cliente.post(RUTA, json={"persona_usuario_id": "x"}, headers={"Authorization": "Bearer t"})
    assert r.status_code == 404
    assert not [x for x in app.routes if getattr(x, "path", "").startswith("/api/v1/demo/")]


def test_el_resolutor_solo_se_registra_con_app_env_demo(monkeypatch):
    from api.routers import demo_persona

    monkeypatch.setattr(security, "_resolutor_identidad", None)
    monkeypatch.setenv("APP_ENV", "development")
    importlib.reload(demo_persona)
    assert demo_persona.AUTO_REGISTRO is False and security._resolutor_identidad is None
    monkeypatch.setenv("APP_ENV", "demo")
    importlib.reload(demo_persona)
    assert demo_persona.AUTO_REGISTRO is True
    assert security._resolutor_identidad is pasillo.resolver_usuario
    monkeypatch.setattr(security, "_resolutor_identidad", None)
    monkeypatch.setenv("APP_ENV", "development")
    importlib.reload(demo_persona)  # deja el módulo como lo encuentran las demás pruebas
