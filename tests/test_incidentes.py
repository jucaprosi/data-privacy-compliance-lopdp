# ¤incidentes ¤rbac-tenant ¤arbitro
"""INC-01: la bitácora de incidentes se guarda en la base por organización y no se edita ni borra.

Recorrido real contra PostgreSQL (rama Neon de desarrollo o la rama test del CI, nunca producción);
sin TEST_DATABASE_URL las pruebas se omiten.

Prueba de mutación ejecutada en la rama Neon rama-inc-01:
- En features/incidentes/domain/models.py se añadió "dpo" a ROLES_REGISTRO.
- pytest tests/test_incidentes.py::test_el_dpo_consulta_pero_no_registra devolvió 1
  (FAILED: assert 201 == 403).
- Se restauró ROLES_REGISTRO; sin la mutación la prueba pasa.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_TEST_URL = os.environ.get("TEST_DATABASE_URL", "")
if not _TEST_URL:
    pytest.skip("TEST_DATABASE_URL no configurada", allow_module_level=True)
os.environ["DATABASE_URL"] = _TEST_URL

from app_core.db.session import fijar_contexto_rls, get_session  # noqa: E402
from main import app  # noqa: E402

RUTA = "/api/v1/incidentes"
ROLES_QUE_REGISTRAN = ("admin_organizacion", "coordinador", "responsable_area", "implementador")


def _h(user: str, tenant: str, role: str) -> dict[str, str]:
    return {"X-User-ID": user, "X-Tenant-ID": tenant, "X-Role": role}


def _incidente(**cambios) -> dict:
    base = {
        "fecha_deteccion": (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(),
        "titulo": "Acceso no autorizado a la base de clientes",
        "descripcion": "Se detectaron consultas masivas desde una cuenta de servicio.",
        "severidad": "Alta",
        "afecta_datos_personales": True,
        "categorias_datos": ["Contacto (Email / Teléfono)"],
        "medidas_inmediatas": "Se revocó la credencial de la cuenta de servicio.",
    }
    return {**base, **cambios}


@pytest_asyncio.fixture
async def ctx(monkeypatch):
    # Rama de desarrollo o la rama test del CI, nunca producción.
    assert "ep-late-hall" not in _TEST_URL, "Se requiere una rama de desarrollo o test (nunca producción)"
    monkeypatch.setenv("AUTH_MODE", "headers")
    engine = create_async_engine(_TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    a, b = f"inc-a-{sufijo}", f"inc-b-{sufijo}"
    usuarios = {rol: (f"inc-{rol[:5]}-{sufijo}", a, rol) for rol in (*ROLES_QUE_REGISTRAN, "dpo")}
    usuarios["coord_b"] = (f"inc-coordb-{sufijo}", b, "coordinador")
    async with factory() as s:
        for t in (a, b):
            await s.execute(text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:t, :t, :t, :t)"
            ), {"t": t})
        for uid, tenant, rol in usuarios.values():
            await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :u)"),
                            {"u": uid, "e": f"{uid}@example.test"})
            await fijar_contexto_rls(s, tenant, uid)
            await s.execute(text(
                "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, :r)"
            ), {"i": str(uuid.uuid4()), "u": uid, "t": tenant, "r": rol})
        await s.commit()

    async def session_override():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = session_override
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield {"client": client, "factory": factory, "a": a, "b": b, "u": usuarios}
    finally:
        app.dependency_overrides.clear()
        async with factory() as s:
            for t in (a, b):
                await fijar_contexto_rls(s, t)
                for sentencia in (
                    "DELETE FROM incidentes WHERE tenant_id = :t",
                    "DELETE FROM audit_events WHERE tenant_id = :t",
                    "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
                ):
                    await s.execute(text(sentencia), {"t": t})
                await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t})
            await s.execute(text("DELETE FROM users WHERE id LIKE :p"), {"p": f"inc-%-{sufijo}"})
            await s.commit()
        await engine.dispose()


def _como(ctx, clave):
    uid, tenant, rol = ctx["u"][clave]
    return _h(uid, tenant, rol)


@pytest.mark.asyncio
@pytest.mark.parametrize("rol", ROLES_QUE_REGISTRAN)
async def test_registran_los_roles_de_la_organizacion(ctx, rol):
    r = await ctx["client"].post(RUTA, headers=_como(ctx, rol), json=_incidente())
    assert r.status_code == 201, r.text
    assert r.json()["registrado_por"] == ctx["u"][rol][0]


@pytest.mark.asyncio
async def test_el_dpo_consulta_pero_no_registra(ctx):
    await ctx["client"].post(RUTA, headers=_como(ctx, "coordinador"), json=_incidente())
    r = await ctx["client"].post(RUTA, headers=_como(ctx, "dpo"), json=_incidente())
    assert r.status_code == 403, r.text
    consulta = await ctx["client"].get(RUTA, headers=_como(ctx, "dpo"))
    assert consulta.status_code == 200
    assert len(consulta.json()["incidentes"]) == 1


@pytest.mark.asyncio
async def test_autoria_hora_plazo_y_huella_los_pone_el_servidor(ctx):
    antes = datetime.now(timezone.utc)
    cuerpo = _incidente(
        reportadoPor="Otra persona",
        registrado_por="usuario-ajeno",
        registrado_en="2020-01-01T00:00:00+00:00",
        slaHorasPersonalizado=500,
        fechaLimiteNotificacion="2030-01-01T00:00:00+00:00",
        huella="f" * 64,
        secuencia=99,
    )
    r = await ctx["client"].post(RUTA, headers=_como(ctx, "implementador"), json=cuerpo)
    assert r.status_code == 201, r.text
    registrado = r.json()
    assert registrado["registrado_por"] == ctx["u"]["implementador"][0]
    assert datetime.fromisoformat(registrado["registrado_en"]) >= antes - timedelta(seconds=5)
    assert registrado["secuencia"] == 1 and registrado["huella"] != "f" * 64
    assert not {"reportadoPor", "slaHorasPersonalizado", "fechaLimiteNotificacion", "estadoSLA"} & set(registrado)

    async with ctx["factory"]() as s:
        eventos = (await s.execute(text(
            "SELECT count(*) FROM audit_events WHERE tenant_id = :t AND action = 'incidente_registrado'"
        ), {"t": ctx["a"]})).scalar_one()
    assert eventos == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("cambio", [
    {"fecha_deteccion": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()},
    {"severidad": "Catastrófica"},
    {"titulo": ""},
])
async def test_datos_fuera_de_regla_son_422_y_no_registran(ctx, cambio):
    r = await ctx["client"].post(RUTA, headers=_como(ctx, "coordinador"), json=_incidente(**cambio))
    assert r.status_code == 422, r.text
    assert (await ctx["client"].get(RUTA, headers=_como(ctx, "coordinador"))).json()["incidentes"] == []


@pytest.mark.asyncio
async def test_sobrevive_a_una_sesion_nueva_y_se_lista_del_mas_reciente(ctx):
    primero = (await ctx["client"].post(RUTA, headers=_como(ctx, "coordinador"), json=_incidente(titulo="Primero"))).json()
    segundo = (await ctx["client"].post(RUTA, headers=_como(ctx, "responsable_area"), json=_incidente(titulo="Segundo"))).json()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as nuevo:
        bitacora = (await nuevo.get(RUTA, headers=_como(ctx, "admin_organizacion"))).json()
    assert [i["id"] for i in bitacora["incidentes"]] == [segundo["id"], primero["id"]]
    assert segundo["huella_anterior"] == primero["huella"]
    assert bitacora["cadena_integra"] is True and bitacora["primer_alterado"] is None


@pytest.mark.asyncio
async def test_alterar_un_incidente_en_la_base_rompe_la_cadena(ctx):
    primero = (await ctx["client"].post(RUTA, headers=_como(ctx, "coordinador"), json=_incidente())).json()
    await ctx["client"].post(RUTA, headers=_como(ctx, "coordinador"), json=_incidente(titulo="Otro"))
    # El dueño de la base (no la aplicación) rebaja la severidad del primero.
    async with ctx["factory"]() as s:
        await fijar_contexto_rls(s, ctx["a"])
        await s.execute(text("UPDATE incidentes SET severidad = 'Baja' WHERE id = :id"), {"id": primero["id"]})
        await s.commit()
    bitacora = (await ctx["client"].get(RUTA, headers=_como(ctx, "dpo"))).json()
    assert bitacora["cadena_integra"] is False
    assert bitacora["primer_alterado"] == primero["id"]


@pytest.mark.asyncio
async def test_la_aplicacion_no_puede_editar_ni_borrar_un_incidente(ctx):
    registrado = (await ctx["client"].post(RUTA, headers=_como(ctx, "coordinador"), json=_incidente())).json()
    for sentencia in (
        "UPDATE incidentes SET severidad = 'Baja' WHERE id = :id",
        "DELETE FROM incidentes WHERE id = :id",
    ):
        async with ctx["factory"]() as s:
            await s.execute(text("SET LOCAL ROLE lopdp_app"))
            await fijar_contexto_rls(s, ctx["a"])
            with pytest.raises(DBAPIError) as error:
                await s.execute(text(sentencia), {"id": registrado["id"]})
            assert error.value.orig.sqlstate == "42501"
            await s.rollback()


@pytest.mark.asyncio
async def test_rls_entre_organizaciones(ctx):
    await ctx["client"].post(RUTA, headers=_como(ctx, "coordinador"), json=_incidente())
    assert (await ctx["client"].get(RUTA, headers=_como(ctx, "coord_b"))).json()["incidentes"] == []
    async with ctx["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, ctx["b"])
        assert (await s.execute(text("SELECT count(*) FROM incidentes"))).scalar_one() == 0
        with pytest.raises(DBAPIError):
            await s.execute(text(
                "INSERT INTO incidentes (id, tenant_id, secuencia, fecha_deteccion, titulo, descripcion, severidad, "
                "afecta_datos_personales, categorias_datos, medidas_inmediatas, registrado_por, registrado_en, "
                "huella_anterior, huella) VALUES (:id, :a, 1, now(), 'x', '', 'Baja', false, '[]', '', :u, now(), :h, :h)"
            ), {"id": str(uuid.uuid4()), "a": ctx["a"], "u": ctx["u"]["coord_b"][0], "h": "e" * 64})
