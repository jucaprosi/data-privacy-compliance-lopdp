"""Árbitro RAT-01 contra TEST_DATABASE_URL (rama Neon de desarrollo).

Mutación exigida: sustituir PostgresRATRepository(session) en
obtener_actividades_tenant por un repositorio en memoria recién creado.
test_persistencia_en_sesion_nueva debe fallar al leer el RAT creado por HTTP.
El resultado ejecutado se informa en el PR; esta descripción no certifica la prueba.
"""
# ¤¤security-engineer
import os
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI, Header
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text, insert
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker

pytestmark = pytest.mark.asyncio

# ¤rat
@pytest_asyncio.fixture
async def rat_env(db_engine):
    from app_core.db.session import fijar_contexto_rls
    url = os.environ.get("TEST_DATABASE_URL", "")
    assert url and "ep-late-hall-b50bpbk5" not in url, "Se requiere una rama de desarrollo"
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    ta, tb = (f"rat-{uuid4().hex}" for _ in range(2))
    roles = ("coordinador", "dpo", "implementador", "admin_organizacion", "responsable_area")
    usuarios = {rol: f"rat-u-{uuid4().hex}" for rol in roles}
    otro = f"rat-u-{uuid4().hex}"
    try:
        async with factory() as s:
            for tenant in (ta, tb):
                await s.execute(text(
                    "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                    "VALUES (:t, :t, :t, :t)"
                ), {"t": tenant})
            for rol, usuario, tenant in (
                *((r, u, ta) for r, u in usuarios.items()),
                ("coordinador", otro, tb),
            ):
                await s.execute(text(
                    "INSERT INTO users (id, email, nombre) VALUES (:u, :e, 'RAT test')"
                ), {"u": usuario, "e": f"{usuario}@rat.test"})
                await fijar_contexto_rls(s, tenant, usuario)
                await s.execute(text(
                    "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) "
                    "VALUES (:id, :u, :t, :r)"
                ), {"id": str(uuid4()), "u": usuario, "t": tenant, "r": rol})
            await s.commit()
        yield {"factory": factory, "a": ta, "b": tb, "usuarios": usuarios, "otro": otro}
    finally:
        async with factory() as s:
            for tenant in (ta, tb):
                await fijar_contexto_rls(s, tenant)
                for tabla in ("audit_events", "rat_actividades", "user_tenant_roles"):
                    await s.execute(text(f"DELETE FROM {tabla} WHERE tenant_id = :t"),
                                    {"t": tenant})
                await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": tenant})
            for usuario in (*usuarios.values(), otro):
                await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": usuario})
            await s.commit()


# ¤rat
@pytest_asyncio.fixture
async def rat_client(rat_env):
    from api.routers.rat import router
    from app_core.db.session import get_session, fijar_contexto_rls
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    async def sesion(
        tenant: str = Header(..., alias="X-Tenant-ID"),
        usuario: str = Header(..., alias="X-User-ID"),
    ):
        async with rat_env["factory"]() as s:
            await s.execute(text("SET LOCAL ROLE lopdp_app"))
            await fijar_contexto_rls(s, tenant, usuario)
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    app.dependency_overrides[get_session] = sesion
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://rat.test",
    ) as client:
        yield client


# ¤rat
def _headers(env, rol="coordinador", otro=False):
    return {
        "X-Tenant-ID": env["b"] if otro else env["a"],
        "X-User-ID": env["otro"] if otro else env["usuarios"][rol],
        "X-Role": rol,
    }


# ¤rat
def _payload():
    return {
        "codigo": "RAT-NOMINA", "nombre": "Nómina", "area_responsable": "RRHH",
        "finalidad": "Pago de remuneraciones", "base_legal": "CUMPLIMIENTO_CONTRATO",
        "categorias_titulares": ["EMPLEADOS"], "categorias_datos": ["identificacion"],
        "datos_sensibles": False, "volumen_titulares_estimado": 10,
        "transferencia_internacional": True, "requiere_eipd": False,
        "es_gran_escala": False, "medio_soporte": "Digital",
        "encargados": ["Proveedor"], "destinatarios": ["IESS"],
        "pais_transferencia": "Colombia", "plazo_conservacion": "5 años",
        "medidas_seguridad": ["Cifrado"], "nivel_riesgo": "medio",
        "decisiones_automatizadas": True, "volumen_titulares_12_meses": 20,
        "observaciones_dpo": "Revisado", "origen": "plantilla:servicios",
    }


# ¤rat
async def test_persistencia_en_sesion_nueva(rat_client, rat_env):
    from app_core.db.session import fijar_contexto_rls
    from features.rat.rat_service import listar_actividades_rat
    h = _headers(rat_env)
    respuesta = await rat_client.post("/api/v1/rat/actividades", json=_payload(), headers=h)
    assert respuesta.status_code == 200, respuesta.text
    actividad = respuesta.json()["actividad"]
    # Sesión distinta a la petición: consulta por la compuerta y SQL sin repositorio.
    async with rat_env["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, rat_env["a"])
        persistidas = await listar_actividades_rat(s, rat_env["a"])
        assert [a.id for a in persistidas] == [actividad["id"]]
        fila = (await s.execute(text(
            "SELECT * FROM rat_actividades WHERE id = :id"
        ), {"id": actividad["id"]})).mappings().one()
        for campo, valor in _payload().items():
            assert fila[campo] == valor
    listado = await rat_client.get("/api/v1/rat/actividades", headers=h)
    assert listado.status_code == 200
    assert listado.json()["actividades"] == [actividad]


# ¤rat
async def test_edicion_baja_logica_y_auditoria(rat_client, rat_env):
    from app_core.db.session import fijar_contexto_rls
    h = _headers(rat_env, "dpo")
    creado = await rat_client.post("/api/v1/rat/actividades", json=_payload(), headers=h)
    assert creado.status_code == 200
    rid = creado.json()["actividad"]["id"]
    url = f"/api/v1/rat/actividades/{rid}"
    editado = await rat_client.patch(url, json={"nombre": "Revisado"}, headers=h)
    assert editado.status_code == 200
    assert editado.json()["actividad"]["version"] == 2
    assert editado.json()["actividad"]["nombre"] == "Revisado"
    assert editado.json()["actividad"]["finalidad"] == _payload()["finalidad"]
    assert (await rat_client.delete(url, headers=h)).status_code == 200
    assert (await rat_client.get("/api/v1/rat/actividades", headers=h)).json()["total"] == 0
    assert (await rat_client.patch(url, json={"nombre": "Otra"}, headers=h)).status_code == 404
    assert (await rat_client.delete(url, headers=h)).status_code == 404
    async with rat_env["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, rat_env["a"])
        fila = (await s.execute(text(
            "SELECT deleted_at, version FROM rat_actividades WHERE id = :id"
        ), {"id": rid})).one()
        assert fila.deleted_at is not None and fila.version == 3
        eventos = (await s.execute(text(
            "SELECT action, user_id FROM audit_events WHERE entity_id = :id"
        ), {"id": rid})).all()
        assert sorted(e.action for e in eventos) == ["baja", "crear", "editar"]
        assert all(e.user_id == rat_env["usuarios"]["dpo"] for e in eventos)


# ¤rat
async def test_rls_real_sin_filtro_de_tenant_y_sin_contexto(rat_client, rat_env):
    from app_core.db.session import fijar_contexto_rls
    from features.rat.domain.models import ActividadRAT, rat_actividades
    from dataclasses import asdict
    respuesta = await rat_client.post(
        "/api/v1/rat/actividades", json=_payload(), headers=_headers(rat_env),
    )
    assert respuesta.status_code == 200
    rid = respuesta.json()["actividad"]["id"]
    async with rat_env["factory"]() as s:
        estado = (await s.execute(text(
            "SELECT relrowsecurity, relforcerowsecurity FROM pg_class "
            "WHERE oid = 'rat_actividades'::regclass"
        ))).one()
        assert estado.relrowsecurity and estado.relforcerowsecurity
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        rol = (await s.execute(text(
            "SELECT rolbypassrls, rolsuper FROM pg_roles WHERE rolname = current_user"
        ))).one()
        assert not rol.rolbypassrls and not rol.rolsuper
        assert not (await s.execute(text(
            "SELECT pg_get_userbyid(relowner) = current_user FROM pg_class "
            "WHERE oid = 'rat_actividades'::regclass"
        ))).scalar_one()
        for tenant, esperado in ((rat_env["a"], 1), (rat_env["b"], 0), ("", 0)):
            await s.execute(text(
                "SELECT set_config('app.current_tenant_id', :t, true)"
            ), {"t": tenant})
            assert (await s.execute(text(
                "SELECT count(*) FROM rat_actividades WHERE id = :id"
            ), {"id": rid})).scalar_one() == esperado
        await fijar_contexto_rls(s, rat_env["b"])
        intrusa = ActividadRAT(tenant_id=rat_env["a"])
        with pytest.raises(DBAPIError) as exc:
            await s.execute(insert(rat_actividades).values(**asdict(intrusa)))
        assert exc.value.orig.sqlstate == "42501"
    # También falla cerrado en la API: ni lectura ni edición ni baja ajenas.
    otro = _headers(rat_env, otro=True)
    assert (await rat_client.get("/api/v1/rat/actividades", headers=otro)).json()["total"] == 0
    url = f"/api/v1/rat/actividades/{rid}"
    assert (await rat_client.patch(url, json={"nombre": "Intrusión"}, headers=otro)).status_code == 404
    assert (await rat_client.delete(url, headers=otro)).status_code == 404


# ¤rat
@pytest.mark.parametrize("rol", ["implementador", "admin_organizacion", "responsable_area"])
async def test_permisos_en_todas_las_operaciones(rat_client, rat_env, rol):
    h = _headers(rat_env, rol)
    lectura = await rat_client.get("/api/v1/rat/actividades", headers=h)
    assert lectura.status_code == (403 if rol == "responsable_area" else 200)
    assert (await rat_client.post(
        "/api/v1/rat/actividades", json=_payload(), headers=h,
    )).status_code == 403
    url = "/api/v1/rat/actividades/inexistente"
    assert (await rat_client.patch(url, json={"nombre": "No"}, headers=h)).status_code == 403
    assert (await rat_client.delete(url, headers=h)).status_code == 403
    falsa = dict(h, **{"X-Role": "dpo"})
    assert (await rat_client.get("/api/v1/rat/actividades", headers=falsa)).status_code == 403


# ¤rat
async def test_auditoria_y_actividad_son_atomicas(rat_client, rat_env, monkeypatch):
    import api.routers.rat as router_rat
    from app_core.db.session import fijar_contexto_rls

    async def fallo_auditoria(*args, **kwargs):
        raise RuntimeError("Fallo de auditoría simulado")

    monkeypatch.setattr(router_rat, "registrar_evento", fallo_auditoria)
    respuesta = await rat_client.post(
        "/api/v1/rat/actividades", json=_payload(), headers=_headers(rat_env),
    )
    assert respuesta.status_code == 500
    async with rat_env["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, rat_env["a"])
        assert (await s.execute(text(
            "SELECT count(*) FROM rat_actividades"
        ))).scalar_one() == 0


# ¤rat
async def test_parche_no_admite_identidad_nulos_ni_origen_invalido(rat_client, rat_env):
    h = _headers(rat_env)
    respuesta = await rat_client.post("/api/v1/rat/actividades", json=_payload(), headers=h)
    assert respuesta.status_code == 200
    url = f"/api/v1/rat/actividades/{respuesta.json()['actividad']['id']}"
    for cambio in ({}, {"nombre": None}, {"tenant_id": rat_env["b"]},
                   {"origen": "importado"}, {"volumen_titulares_12_meses": -1}):
        assert (await rat_client.patch(url, json=cambio, headers=h)).status_code == 422
