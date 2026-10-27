"""Árbitro DPO-01 contra TEST_DATABASE_URL (rama Neon de desarrollo).

Prueba de mutación ejecutada en la rama Neon dpo-01:
- En api/routers/dpo_cockpit.py (post_emitir_dictamen) se eliminó temporalmente la
  comprobación de rol (`if ctx["role"] != "dpo": raise HTTPException(403, ...)`).
- pytest tests/test_dpo_bitacora.py::test_rol_distinto_de_dpo_no_puede_emitir
  devolvió 1 (FAILED: assert 200 == 403).
- Se restauró la comprobación de rol en api/routers/dpo_cockpit.py y se verificó con
  git diff que no quedaron restos de la mutación.
- Sin la mutación: pytest tests/test_dpo_bitacora.py devolvió 0.
"""
# ¤¤security-engineer
import os
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI, Header
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def dpo_env(db_engine, monkeypatch):
    from app_core.db.session import fijar_contexto_rls

    monkeypatch.setenv("AUTH_MODE", "headers")
    # Como RAT-01: rama de desarrollo o la rama de pruebas del CI, nunca producción.
    url = os.environ.get("TEST_DATABASE_URL", "")
    assert url and "ep-late-hall-b50bpbk5" not in url, "Se requiere una rama de desarrollo"

    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    ta, tb = (f"dpo-org-{uuid4().hex[:12]}" for _ in range(2))
    roles = ("dpo", "admin_organizacion", "coordinador", "implementador", "responsable_area")
    usuarios_a = {rol: f"dpo-ua-{rol}-{uuid4().hex[:8]}" for rol in roles}
    usuarios_b = {
        "dpo": f"dpo-ub-dpo-{uuid4().hex[:8]}",
        "admin_organizacion": f"dpo-ub-admin-{uuid4().hex[:8]}",
    }

    try:
        async with factory() as s:
            for tenant in (ta, tb):
                await s.execute(
                    text(
                        "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                        "VALUES (:t, :t, :t, :t)"
                    ),
                    {"t": tenant},
                )
            for rol, usuario in usuarios_a.items():
                await s.execute(
                    text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, 'DPO test A')"),
                    {"u": usuario, "e": f"{usuario}@example.test"},
                )
                await fijar_contexto_rls(s, ta, usuario)
                await s.execute(
                    text(
                        "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) "
                        "VALUES (:id, :u, :t, :r)"
                    ),
                    {"id": str(uuid4()), "u": usuario, "t": ta, "r": rol},
                )
            for rol, usuario in usuarios_b.items():
                await s.execute(
                    text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, 'DPO test B')"),
                    {"u": usuario, "e": f"{usuario}@example.test"},
                )
                await fijar_contexto_rls(s, tb, usuario)
                await s.execute(
                    text(
                        "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) "
                        "VALUES (:id, :u, :t, :r)"
                    ),
                    {"id": str(uuid4()), "u": usuario, "t": tb, "r": rol},
                )
            await s.commit()
        yield {
            "factory": factory,
            "a": ta,
            "b": tb,
            "usuarios": usuarios_a,
            "usuarios_b": usuarios_b,
        }
    finally:
        async with factory() as s:
            for tenant in (ta, tb):
                await fijar_contexto_rls(s, tenant)
                for sentencia in (
                    "DELETE FROM audit_events WHERE tenant_id = :t",
                    "DELETE FROM dpo_dictamenes WHERE tenant_id = :t",
                    "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
                ):
                    await s.execute(text(sentencia), {"t": tenant})
                await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": tenant})
            for usuario in (*usuarios_a.values(), *usuarios_b.values()):
                await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": usuario})
            await s.commit()


@pytest_asyncio.fixture
async def dpo_client(dpo_env):
    from api.routers.dpo_cockpit import get_dpo_session, router
    from app_core.db.session import fijar_contexto_rls

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    async def sesion(
        tenant: str = Header("tenant-default", alias="X-Tenant-ID"),
        usuario: str = Header("", alias="X-User-ID"),
    ):
        async with dpo_env["factory"]() as s:
            await s.execute(text("SET LOCAL ROLE lopdp_app"))
            await fijar_contexto_rls(s, tenant, usuario)
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    app.dependency_overrides[get_dpo_session] = sesion
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://dpo.test",
    ) as client:
        yield client


def _headers(env, rol="dpo", org_b=False):
    if org_b:
        return {
            "X-Tenant-ID": env["b"],
            "X-User-ID": env["usuarios_b"][rol],
            "X-Role": rol,
        }
    return {
        "X-Tenant-ID": env["a"],
        "X-User-ID": env["usuarios"][rol],
        "X-Role": rol,
    }


def _payload(**overrides):
    base = {
        "tipo": "OPINION_CONSULTIVA",
        "asunto": "Evaluación de retención de expedientes clínicos",
        "referencia_normativa": "Art. 50 LOPDP",
        "cuerpo": "Se recomienda limitar el plazo activo y cifrar el archivo histórico.",
    }
    base.update(overrides)
    return base


async def test_dictamen_sobrevive_a_sesion_nueva(dpo_client, dpo_env):
    from app_core.db.session import fijar_contexto_rls
    from features.dpo_cockpit.dpo_cockpit_service import listar_bitacora_dpo

    h = _headers(dpo_env, "dpo")
    resp = await dpo_client.post("/api/v1/dpo/dictamenes", json=_payload(), headers=h)
    assert resp.status_code == 200, resp.text
    emitido = resp.json()["dictamen"]
    assert emitido["es_vinculante"] is False
    assert emitido["prev_hash"] == "0" * 64
    assert len(emitido["sha256_hash"]) == 64
    assert emitido["acuse_recibo_alta_direccion"] is False
    assert emitido["acuse_por"] is None
    assert emitido["fecha_acuse"] is None

    async with dpo_env["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, dpo_env["a"])
        persistidos = await listar_bitacora_dpo(s, dpo_env["a"])
        assert [d.id for d in persistidos] == [emitido["id"]]
        fila = (
            await s.execute(
                text("SELECT * FROM dpo_dictamenes WHERE id = :id"),
                {"id": emitido["id"]},
            )
        ).mappings().one()
        assert fila["asunto"] == _payload()["asunto"]
        assert fila["cuerpo"] == _payload()["cuerpo"]
        assert fila["dpo_id"] == dpo_env["usuarios"]["dpo"]
        assert fila["sha256_hash"] == emitido["sha256_hash"]

    listado = await dpo_client.get("/api/v1/dpo/bitacora", headers=h)
    assert listado.status_code == 200
    assert listado.json()["total"] == 1
    assert listado.json()["dictamenes"][0]["id"] == emitido["id"]


@pytest.mark.parametrize("rol", ["admin_organizacion", "coordinador", "implementador", "responsable_area"])
async def test_rol_distinto_de_dpo_no_puede_emitir(dpo_client, dpo_env, rol):
    resp = await dpo_client.post(
        "/api/v1/dpo/dictamenes",
        json=_payload(),
        headers=_headers(dpo_env, rol),
    )
    assert resp.status_code == 403


async def test_autor_guardado_es_usuario_autenticado_e_ignora_dpo_id_del_cuerpo(dpo_client, dpo_env):
    from app_core.db.session import fijar_contexto_rls

    h = _headers(dpo_env, "dpo")
    resp = await dpo_client.post(
        "/api/v1/dpo/dictamenes",
        json=_payload(dpo_id="impostor-enviado-por-navegador"),
        headers=h,
    )
    assert resp.status_code == 200, resp.text
    dictamen = resp.json()["dictamen"]
    assert dictamen["dpo_id"] == dpo_env["usuarios"]["dpo"]
    assert dictamen["dpo_id"] != "impostor-enviado-por-navegador"

    async with dpo_env["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, dpo_env["a"])
        autor_bd = (
            await s.execute(
                text("SELECT dpo_id FROM dpo_dictamenes WHERE id = :id"),
                {"id": dictamen["id"]},
            )
        ).scalar_one()
        assert autor_bd == dpo_env["usuarios"]["dpo"]


async def test_permisos_consulta_bitacora(dpo_client, dpo_env):
    await dpo_client.post(
        "/api/v1/dpo/dictamenes",
        json=_payload(),
        headers=_headers(dpo_env, "dpo"),
    )
    for rol_permitido in ("dpo", "admin_organizacion", "coordinador"):
        resp = await dpo_client.get("/api/v1/dpo/bitacora", headers=_headers(dpo_env, rol_permitido))
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    for rol_denegado in ("implementador", "responsable_area"):
        resp = await dpo_client.get("/api/v1/dpo/bitacora", headers=_headers(dpo_env, rol_denegado))
        assert resp.status_code == 403


@pytest.mark.parametrize("rol", ["dpo", "coordinador", "implementador", "responsable_area"])
async def test_acuse_por_rol_distinto_de_admin_organizacion_recibe_403(dpo_client, dpo_env, rol):
    creado = await dpo_client.post(
        "/api/v1/dpo/dictamenes",
        json=_payload(),
        headers=_headers(dpo_env, "dpo"),
    )
    dictamen_id = creado.json()["dictamen"]["id"]
    resp = await dpo_client.post(
        f"/api/v1/dpo/dictamenes/{dictamen_id}/acuse",
        headers=_headers(dpo_env, rol),
    )
    assert resp.status_code == 403


async def test_acuse_otra_organizacion_404_y_segundo_acuse_409(dpo_client, dpo_env):
    creado = await dpo_client.post(
        "/api/v1/dpo/dictamenes",
        json=_payload(),
        headers=_headers(dpo_env, "dpo"),
    )
    dictamen_id = creado.json()["dictamen"]["id"]

    # Acuse desde otra organización -> 404
    ajeno = await dpo_client.post(
        f"/api/v1/dpo/dictamenes/{dictamen_id}/acuse",
        headers=_headers(dpo_env, "admin_organizacion", org_b=True),
    )
    assert ajeno.status_code == 404

    # Primer acuse por admin_organizacion de la misma organización -> 200
    primero = await dpo_client.post(
        f"/api/v1/dpo/dictamenes/{dictamen_id}/acuse",
        headers=_headers(dpo_env, "admin_organizacion"),
    )
    assert primero.status_code == 200, primero.text
    datos = primero.json()["dictamen"]
    assert datos["acuse_recibo_alta_direccion"] is True
    assert datos["acuse_por"] == dpo_env["usuarios"]["admin_organizacion"]
    assert datos["fecha_acuse"] is not None

    # Segundo acuse sobre el mismo dictamen -> 409
    segundo = await dpo_client.post(
        f"/api/v1/dpo/dictamenes/{dictamen_id}/acuse",
        headers=_headers(dpo_env, "admin_organizacion"),
    )
    assert segundo.status_code == 409


async def test_alta_y_acuse_registran_eventos_en_audit_events(dpo_client, dpo_env):
    from app_core.db.session import fijar_contexto_rls

    creado = await dpo_client.post(
        "/api/v1/dpo/dictamenes",
        json=_payload(),
        headers=_headers(dpo_env, "dpo"),
    )
    assert creado.status_code == 200
    dictamen_id = creado.json()["dictamen"]["id"]

    acuse = await dpo_client.post(
        f"/api/v1/dpo/dictamenes/{dictamen_id}/acuse",
        headers=_headers(dpo_env, "admin_organizacion"),
    )
    assert acuse.status_code == 200

    async with dpo_env["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, dpo_env["a"])
        eventos = (
            await s.execute(
                text(
                    "SELECT action, user_id, entity_type FROM audit_events "
                    "WHERE entity_id = :id ORDER BY action"
                ),
                {"id": dictamen_id},
            )
        ).all()
        assert len(eventos) == 2
        por_accion = {e.action: e for e in eventos}
        assert set(por_accion.keys()) == {"emitir_dictamen", "acuse_recibo_alta_direccion"}
        assert por_accion["emitir_dictamen"].user_id == dpo_env["usuarios"]["dpo"]
        assert por_accion["emitir_dictamen"].entity_type == "dpo_dictamen"
        assert por_accion["acuse_recibo_alta_direccion"].user_id == dpo_env["usuarios"]["admin_organizacion"]


async def test_rls_entre_organizaciones_y_permisos_lopdp_app(dpo_client, dpo_env):
    from app_core.db.session import fijar_contexto_rls

    resp_a = await dpo_client.post(
        "/api/v1/dpo/dictamenes",
        json=_payload(asunto="Dictamen Org A"),
        headers=_headers(dpo_env, "dpo", org_b=False),
    )
    resp_b = await dpo_client.post(
        "/api/v1/dpo/dictamenes",
        json=_payload(asunto="Dictamen Org B"),
        headers=_headers(dpo_env, "dpo", org_b=True),
    )
    assert resp_a.status_code == 200 and resp_b.status_code == 200
    id_a = resp_a.json()["dictamen"]["id"]
    id_b = resp_b.json()["dictamen"]["id"]
    # Cada organización inicia su propia cadena con GENESIS_HASH
    assert resp_a.json()["dictamen"]["prev_hash"] == "0" * 64
    assert resp_b.json()["dictamen"]["prev_hash"] == "0" * 64

    async with dpo_env["factory"]() as s:
        estado = (
            await s.execute(
                text(
                    "SELECT relrowsecurity, relforcerowsecurity FROM pg_class "
                    "WHERE oid = 'dpo_dictamenes'::regclass"
                )
            )
        ).one()
        assert estado.relrowsecurity and estado.relforcerowsecurity

        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        rol = (
            await s.execute(
                text("SELECT rolbypassrls, rolsuper FROM pg_roles WHERE rolname = current_user")
            )
        ).one()
        assert not rol.rolbypassrls and not rol.rolsuper

        for tenant, id_propio, id_ajeno in (
            (dpo_env["a"], id_a, id_b),
            (dpo_env["b"], id_b, id_a),
        ):
            await s.execute(
                text("SELECT set_config('app.current_tenant_id', :t, true)"),
                {"t": tenant},
            )
            propios = (
                await s.execute(
                    text("SELECT count(*) FROM dpo_dictamenes WHERE id = :id"),
                    {"id": id_propio},
                )
            ).scalar_one()
            ajenos = (
                await s.execute(
                    text("SELECT count(*) FROM dpo_dictamenes WHERE id = :id"),
                    {"id": id_ajeno},
                )
            ).scalar_one()
            assert propios == 1
            assert ajenos == 0

        await s.execute(text("SELECT set_config('app.current_tenant_id', '', true)"))
        sin_tenant = (
            await s.execute(text("SELECT count(*) FROM dpo_dictamenes"))
        ).scalar_one()
        assert sin_tenant == 0

        # lopdp_app no tiene permiso DELETE
        await fijar_contexto_rls(s, dpo_env["a"])
        with pytest.raises(DBAPIError) as exc_del:
            await s.execute(
                text("DELETE FROM dpo_dictamenes WHERE id = :id"),
                {"id": id_a},
            )
        assert exc_del.value.orig.sqlstate == "42501"
    # lopdp_app solo puede registrar el acuse: reescribir el contenido está prohibido
    async with dpo_env["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, dpo_env["a"])
        with pytest.raises(DBAPIError) as exc_upd:
            await s.execute(
                text("UPDATE dpo_dictamenes SET cuerpo = 'reescrito' WHERE id = :id"),
                {"id": id_a},
            )
        assert exc_upd.value.orig.sqlstate == "42501"
    # Nueva transacción tras el error de permiso para verificar WITH CHECK cruzado
    async with dpo_env["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, dpo_env["b"])
        with pytest.raises(DBAPIError) as exc_ins:
            await s.execute(
                text(
                    "INSERT INTO dpo_dictamenes "
                    "(id, tenant_id, dpo_id, tipo, asunto, referencia_normativa, cuerpo, "
                    "fecha_emision, es_vinculante, prev_hash, sha256_hash, acuse_recibo_alta_direccion) "
                    "VALUES (:id, :tid, 'u', 'OPINION_CONSULTIVA', 'a', 'r', 'c', now(), false, :h, :h, false)"
                ),
                {"id": str(uuid4()), "tid": dpo_env["a"], "h": "0" * 64},
            )
        assert exc_ins.value.orig.sqlstate == "42501"


async def test_alterar_cuerpo_en_bd_rompe_verificacion_cadena(dpo_client, dpo_env):
    from app_core.db.session import fijar_contexto_rls
    from features.dpo_cockpit.dpo_cockpit_service import verificar_cadena_bitacora_dpo

    h = _headers(dpo_env, "dpo")
    ids = []
    hashes = []
    for idx in range(1, 4):
        resp = await dpo_client.post(
            "/api/v1/dpo/dictamenes",
            json=_payload(asunto=f"Dictamen #{idx}", cuerpo=f"Cuerpo íntegro original #{idx}"),
            headers=h,
        )
        assert resp.status_code == 200
        d = resp.json()["dictamen"]
        ids.append(d["id"])
        hashes.append(d["sha256_hash"])
        if idx == 1:
            assert d["prev_hash"] == "0" * 64
        else:
            assert d["prev_hash"] == hashes[idx - 2]

    async with dpo_env["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, dpo_env["a"])
        assert await verificar_cadena_bitacora_dpo(s, dpo_env["a"]) is None

    # La aplicación no puede reescribir el cuerpo (permiso por columnas): la alteración la hace
    # el propietario de la base, como lo haría quien tenga acceso directo a ella.
    async with dpo_env["factory"]() as s:
        await s.execute(
            text("UPDATE dpo_dictamenes SET cuerpo = :nuevo WHERE id = :id"),
            {"nuevo": "Cuerpo manipulado fuera del motor", "id": ids[1]},
        )
        await s.commit()

    async with dpo_env["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, dpo_env["a"])
        alterado = await verificar_cadena_bitacora_dpo(s, dpo_env["a"])
        assert alterado is not None
        assert alterado.id == ids[1]
