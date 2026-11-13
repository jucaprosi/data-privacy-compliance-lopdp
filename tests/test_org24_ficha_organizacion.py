# ¤rbac-tenant ¤arbitro
"""ORG-24: ficha de la organización activa (`GET /organizacion/ficha`), contrato en governance/tareas/ORG-24.md.

Corre contra PostgreSQL 16 local con el rol `lopdp_app` (sin BYPASSRLS): se siembra como dueño y la aplicación
consulta con `SET ROLE lopdp_app`. Sin TEST_DATABASE_URL se omiten; nunca producción. Solo valores simulados.

Pruebas de mutación (PostgreSQL 16 local, restauradas después):
- m1: en ficha_engine `nombres_visibles` devolvió siempre True -> test_nombres_solo_para_roles_de_la_lista falla
  (el responsable de área ve el nombre del DPO).
- m2: en ficha_engine `_SQL_TENANT` leyó sin `WHERE id = :t` -> test_la_ficha_es_del_tenant_activo falla.
- m3: la compuerta de derechos contó también las CONTESTADA -> test_contadores falla.
- m4: la compuerta de derechos quitó `fecha_vencimiento < now()` -> test_contadores falla (vencidas = abiertas).
- m5: `_aislado` dejó de capturar la excepción -> test_una_compuerta_caida_no_tumba_la_ficha da 500.
- m6: la ficha concatenó el correo al nombre del DPO -> test_la_ficha_no_expone_correo_ni_ids falla.
- m9 (ORG-24b): `contar_abiertos` de la compuerta contó todos como abiertos -> test_contadores falla (abiertas 2 en vez de 1).
- m10 (ORG-24b): `armar_ficha` fijó el contexto RLS de otro tenant -> 3 pruebas fallan (RLS oculta las filas). Quitar la
  llamada sin más no falla: la sesión ya trae el contexto del encabezado (get_session); la del motor es defensa en profundidad.
- m7: `armar_ficha` llamó a `_nombres` siempre -> test_sin_permiso_no_se_consultan_los_nombres falla.
- m8: `_SQL_NOMBRES` sin `valid_from <= now()` -> test_una_designacion_futura_no_aparece falla.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_TEST_URL = os.environ.get("TEST_DATABASE_URL", "")
if _TEST_URL:
    os.environ["DATABASE_URL"] = _TEST_URL
else:
    os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://sin-base:sin-base@localhost:1/sin-base")

from api.rbac import get_usuario_autenticado  # noqa: E402
from app_core.db.session import fijar_contexto_rls, get_session  # noqa: E402
from features.incidentes import incidentes_service  # noqa: E402
from main import app  # noqa: E402

RUTA = "/api/v1/organizacion/ficha"
requiere_base = pytest.mark.skipif(not _TEST_URL, reason="TEST_DATABASE_URL no configurada")


async def _rol(s, tenant, usuario, rol):
    await fijar_contexto_rls(s, tenant)
    await s.execute(text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, :r)"),
                    {"i": str(uuid.uuid4()), "u": usuario, "t": tenant, "r": rol})


@pytest_asyncio.fixture
async def ctx():
    assert "ep-late-hall" not in _TEST_URL, "Se requiere una base local o de pruebas (nunca producción)"
    engine = create_async_engine(_TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    t_a, t_b = f"org24-a-{sufijo}", f"org24-b-{sufijo}"
    ruc_a, ruc_b = f"A{sufijo}", f"B{sufijo}"
    u = {k: f"org24-{k}-{sufijo}" for k in ("dpo", "impl", "area", "coord", "admin", "otro")}
    nombres = {"dpo": "Dpo Simulado", "impl": "Implementador Simulado", "area": "Area Simulada", "coord": "Coord Simulado", "admin": "Admin Simulado", "otro": "Otro Simulado"}
    async with factory() as s:
        for t, nombre, ruc, nat in ((t_a, "Organización A", ruc_a, "privada"),
                                    (t_b, "Organización B", ruc_b, "publica")):
            await s.execute(text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, naturaleza, tamano) "
                "VALUES (:t, :n, :t, :r, :nat, 'mediana')"), {"t": t, "n": nombre, "r": ruc, "nat": nat})
        for k, uid in u.items():
            await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :n)"),
                            {"u": uid, "e": f"{uid}@correo.invalid", "n": nombres[k]})
        await _rol(s, t_a, u["dpo"], "dpo")
        await _rol(s, t_a, u["impl"], "implementador")
        await _rol(s, t_a, u["area"], "responsable_area")
        await _rol(s, t_a, u["coord"], "coordinador")
        await _rol(s, t_a, u["admin"], "admin_organizacion")
        await _rol(s, t_b, u["otro"], "dpo")
        await s.commit()

    actual = {"uid": u["dpo"]}

    async def sesion_de_aplicacion():
        async with factory() as sesion:
            await sesion.execute(text("SET ROLE lopdp_app"))
            try:
                yield sesion
                await sesion.commit()
            except Exception:
                await sesion.rollback()
                raise
            finally:
                await sesion.execute(text("RESET ROLE"))
                await sesion.commit()

    app.dependency_overrides[get_session] = sesion_de_aplicacion
    app.dependency_overrides[get_usuario_autenticado] = lambda: actual["uid"]
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield {"client": client, "factory": factory, "a": t_a, "b": t_b, "ruc_a": ruc_a, "ruc_b": ruc_b, "u": u, "actual": actual,
                   "nombres": nombres}
    finally:
        app.dependency_overrides.clear()
        async with factory() as s:
            for t in (t_a, t_b):
                await fijar_contexto_rls(s, t)
                for sentencia in ("DELETE FROM derechos_arco_solicitudes WHERE tenant_id_texto = :t",
                                  "DELETE FROM incidentes_eventos_estado WHERE tenant_id = :t",
                                  "DELETE FROM incidentes WHERE tenant_id = :t",
                                  "DELETE FROM audit_events WHERE tenant_id = :t",
                                  "DELETE FROM user_tenant_roles WHERE tenant_id = :t"):
                    await s.execute(text(sentencia), {"t": t})
                await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t})
            await s.execute(text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": list(u.values())})
            await s.commit()
        await engine.dispose()


def _cab(ctx, tenant, rol, quien):
    ctx["actual"]["uid"] = ctx["u"][quien]
    return {"X-Tenant-ID": tenant, "X-Role": rol}


async def _solicitud(ctx, tenant, estado, vence_en_dias):
    async with ctx["factory"]() as s:
        await fijar_contexto_rls(s, tenant)
        await s.execute(text(
            "INSERT INTO derechos_arco_solicitudes (tenant_id_texto, tipo_solicitud, estado, cedula_solicitante, "
            "nombre_solicitante, fecha_recepcion, fecha_vencimiento) VALUES (:t, 'ACCESO', CAST(:e AS estadosolicitud), "
            "'0000000000', 'Titular Simulado', now(), now() + make_interval(days => :d))"),
            {"t": tenant, "e": estado, "d": vence_en_dias})
        await s.commit()


async def _cerrar(ctx, tenant, quien, incidente_id):
    async with ctx["factory"]() as s:
        await incidentes_service.cerrar_incidente(s, tenant, ctx["u"][quien], incidente_id, "Cierre simulado")
        await s.commit()


async def _incidente(ctx, tenant, quien):
    async with ctx["factory"]() as s:
        incidente = await incidentes_service.registrar_incidente(
            s, tenant, ctx["u"][quien], fecha_deteccion=datetime.now(timezone.utc) - timedelta(hours=1),
            titulo="Incidente simulado", descripcion="Descripción simulada", severidad="Media",
            afecta_datos_personales=False, categorias_datos=[], medidas_inmediatas="Ninguna")
        await s.commit()
        return incidente.id


@requiere_base
@pytest.mark.asyncio
async def test_la_ficha_es_del_tenant_activo(ctx):
    r = await ctx["client"].get(RUTA, headers=_cab(ctx, ctx["a"], "dpo", "dpo"))
    assert r.status_code == 200, r.text
    f = r.json()
    assert (f["tenant_id"], f["nombre"], f["ruc"], f["naturaleza"]) == (ctx["a"], "Organización A", ctx["ruc_a"], "privada")
    r = await ctx["client"].get(RUTA, headers=_cab(ctx, ctx["b"], "dpo", "otro"))
    assert r.json()["tenant_id"] == ctx["b"] and r.json()["ruc"] == ctx["ruc_b"]


@requiere_base
@pytest.mark.asyncio
async def test_nombres_solo_para_roles_de_la_lista(ctx):
    casos = (("dpo", "dpo", True), ("implementador", "impl", True), ("admin_organizacion", "admin", True),
             ("responsable_area", "area", False), ("coordinador", "coord", False))
    for rol, quien, ve in casos:
        f = (await ctx["client"].get(RUTA, headers=_cab(ctx, ctx["a"], rol, quien))).json()
        assert f["nombres_visibles"] is ve, rol
        if ve:
            assert f["dpo_nombre"] == ctx["nombres"]["dpo"], rol
            assert f["implementadores"] == [ctx["nombres"]["impl"]], rol
        else:
            assert f["dpo_nombre"] is None and f["implementadores"] == [], rol
        assert "No disponible" not in str(f), rol


@requiere_base
@pytest.mark.asyncio
async def test_contadores(ctx):
    await _solicitud(ctx, ctx["a"], "RECIBIDA", 5)
    await _solicitud(ctx, ctx["a"], "EN_ANALISIS", -2)
    await _solicitud(ctx, ctx["a"], "CONTESTADA", -9)
    await _solicitud(ctx, ctx["b"], "RECIBIDA", -1)
    cerrado = await _incidente(ctx, ctx["a"], "dpo")
    await _incidente(ctx, ctx["a"], "dpo")
    await _cerrar(ctx, ctx["a"], "dpo", cerrado)
    await _incidente(ctx, ctx["b"], "otro")  # de otra organización: no cuenta
    f = (await ctx["client"].get(RUTA, headers=_cab(ctx, ctx["a"], "dpo", "dpo"))).json()
    assert (f["solicitudes_abiertas"], f["solicitudes_vencidas"]) == (2, 1)
    assert f["plazo_estimado"] == "ESTIMADO"
    # ORG-24b: los dos campos conviven; registradas cuenta todos, abiertas solo los no cerrados.
    assert (f["vulneraciones_registradas"], f["vulneraciones_abiertas"]) == (2, 1)
    assert f["vulneraciones_con_plazo"] is None and f["vulneraciones_con_plazo_motivo"] == "plazo_no_definido"
    assert f["errores"] == {}


@requiere_base
@pytest.mark.asyncio
async def test_una_compuerta_caida_no_tumba_la_ficha(ctx, monkeypatch):
    from app_core.pasillo import derechos_arco as pasillo_derechos

    async def falla(*a, **k):
        raise RuntimeError("compuerta caída simulada")

    monkeypatch.setattr(pasillo_derechos, "contar_solicitudes_para_ficha", falla)
    await _incidente(ctx, ctx["a"], "dpo")
    r = await ctx["client"].get(RUTA, headers=_cab(ctx, ctx["a"], "dpo", "dpo"))
    assert r.status_code == 200, r.text
    f = r.json()
    assert f["solicitudes_abiertas"] is None and f["solicitudes_vencidas"] is None
    assert set(f["errores"]) == {"solicitudes_abiertas", "solicitudes_vencidas", "plazo_estimado"}
    assert f["vulneraciones_registradas"] == 1 and f["vulneraciones_abiertas"] == 1 and f["nombre"] == "Organización A"


@requiere_base
@pytest.mark.asyncio
async def test_la_ficha_no_expone_correo_ni_ids(ctx):
    crudo = (await ctx["client"].get(RUTA, headers=_cab(ctx, ctx["a"], "dpo", "dpo"))).text
    assert "correo.invalid" not in crudo and "@" not in crudo
    for uid in ctx["u"].values():
        assert uid not in crudo


@requiere_base
@pytest.mark.asyncio
async def test_sin_rol_vigente_en_el_tenant_no_hay_ficha(ctx):
    r = await ctx["client"].get(RUTA, headers=_cab(ctx, ctx["a"], "dpo", "otro"))
    assert r.status_code in (401, 403), r.text


@requiere_base
@pytest.mark.asyncio
async def test_sin_permiso_no_se_consultan_los_nombres(ctx, monkeypatch):
    import sys

    motor = sys.modules["features.organizacion.services.ficha_engine"]
    llamadas = []
    original = motor._nombres

    async def espia(*a, **k):
        llamadas.append(a[1])
        return await original(*a, **k)

    monkeypatch.setattr(motor, "_nombres", espia)
    await ctx["client"].get(RUTA, headers=_cab(ctx, ctx["a"], "responsable_area", "area"))
    assert llamadas == []
    await ctx["client"].get(RUTA, headers=_cab(ctx, ctx["a"], "dpo", "dpo"))
    assert llamadas == [ctx["a"]]


@requiere_base
@pytest.mark.asyncio
async def test_una_designacion_futura_no_aparece(ctx):
    async with ctx["factory"]() as s:
        await fijar_contexto_rls(s, ctx["a"])
        await s.execute(text("UPDATE user_tenant_roles SET valid_from = now() + interval '1 day' "
                             "WHERE tenant_id = :t AND user_id = :u"), {"t": ctx["a"], "u": ctx["u"]["impl"]})
        await s.commit()
    f = (await ctx["client"].get(RUTA, headers=_cab(ctx, ctx["a"], "dpo", "dpo"))).json()
    assert f["implementadores"] == []
