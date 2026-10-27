"""Árbitro CAPA-01 contra TEST_DATABASE_URL (rama Neon de desarrollo o test del CI).

Prueba de mutación ejecutada en la rama Neon test-capa-01:
- En features/auditoria_capa/services/capa_engine.py (validar_cierre_sod) se desactivó
  temporalmente la comprobación `if responsable_implementacion_id == auditor_id: raise PermissionError(...)`.
- pytest tests/test_capa_persistencia.py::test_responsable_no_puede_cerrar_su_propia_accion_aunque_sea_coordinador_o_admin
  devolvió 1 (FAILED: assert 200 == 403).
- Se restauró la comprobación en features/auditoria_capa/services/capa_engine.py y se verificó con
  git diff que no quedaron restos de la mutación.
- Sin la mutación: pytest tests/test_capa_persistencia.py devolvió 0.
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
async def capa_env(db_engine, monkeypatch):
    from app_core.db.session import fijar_contexto_rls

    monkeypatch.setenv("AUTH_MODE", "headers")
    # Como en test_rat_persistencia.py: rama de desarrollo o la rama test del CI, nunca producción.
    url = os.environ.get("TEST_DATABASE_URL", "")
    assert url and "ep-late-hall" not in url, "Se requiere una rama de desarrollo o test (nunca producción)"

    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    ta, tb = (f"capa-org-{uuid4().hex[:12]}" for _ in range(2))
    roles = ("dpo", "admin_organizacion", "coordinador", "implementador", "responsable_area")
    usuarios_a = {rol: f"capa-ua-{rol}-{uuid4().hex[:8]}" for rol in roles}
    usuarios_b = {
        "dpo": f"capa-ub-dpo-{uuid4().hex[:8]}",
        "coordinador": f"capa-ub-coord-{uuid4().hex[:8]}",
        "admin_organizacion": f"capa-ub-admin-{uuid4().hex[:8]}",
        "implementador": f"capa-ub-impl-{uuid4().hex[:8]}",
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
                    text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, 'CAPA test A')"),
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
                    text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, 'CAPA test B')"),
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
                    "DELETE FROM capa_tickets WHERE tenant_id = :t",
                    "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
                ):
                    await s.execute(text(sentencia), {"t": tenant})
                await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": tenant})
            for usuario in (*usuarios_a.values(), *usuarios_b.values()):
                await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": usuario})
            await s.commit()


@pytest_asyncio.fixture
async def capa_client(capa_env):
    from api.routers.auditoria_capa import get_capa_session, router
    from app_core.db.session import fijar_contexto_rls

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    async def override_session(
        x_user_id: str = Header(""),
        x_tenant_id: str = Header("tenant-default"),
    ):
        async with capa_env["factory"]() as session:
            await fijar_contexto_rls(session, x_tenant_id, x_user_id)
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_capa_session] = override_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


def _headers(tenant: str, usuario: str, rol: str) -> dict[str, str]:
    return {"X-Tenant-ID": tenant, "X-User-ID": usuario, "X-Role": rol}


def _payload_base(responsable_id: str, control_id: str = "P14") -> dict:
    return {
        "control_id": control_id,
        "severidad": "NO_CONFORMIDAD_MAYOR",
        "descripcion_hallazgo": "Ausencia de cláusulas de encargo de tratamiento firmadas con proveedor cloud",
        "causa_raiz": "Contratación directa sin revisión del área de privacidad",
        "accion_correctiva": "Suscribir adenda de encargo de tratamiento conforme al Art. 33 LOPDP",
        "responsable_implementacion_id": responsable_id,
    }


async def test_caso_sobrevive_a_sesion_nueva_y_registra_eventos_auditoria(capa_env, capa_client):
    """Un hallazgo registrado en PostgreSQL sobrevive a una sesión nueva, se cierra una sola vez y deja traza en audit_events."""
    from app_core.db.session import fijar_contexto_rls
    from features.auditoria_capa.auditoria_capa_service import listar_tickets_capa

    ta = capa_env["a"]
    coordinador = capa_env["usuarios"]["coordinador"]
    dpo = capa_env["usuarios"]["dpo"]
    implementador = capa_env["usuarios"]["implementador"]
    admin = capa_env["usuarios"]["admin_organizacion"]

    # 1. Alta por coordinador
    r_alta = await capa_client.post(
        "/api/v1/capa/tickets",
        headers=_headers(ta, coordinador, "coordinador"),
        json=_payload_base(implementador, control_id="P14"),
    )
    assert r_alta.status_code == 201, r_alta.text
    creado = r_alta.json()
    assert creado["tenant_id"] == ta
    assert creado["control_id"] == "P14"
    assert creado["creado_por"] == coordinador
    assert creado["responsable_implementacion_id"] == implementador
    assert creado["estado"] == "ABIERTO"
    assert creado["fecha_creacion"] is not None
    assert creado["fecha_cierre"] is None

    # 2. Alta por DPO también permitida
    r_alta_dpo = await capa_client.post(
        "/api/v1/capa/tickets",
        headers=_headers(ta, dpo, "dpo"),
        json=_payload_base(implementador, control_id="P22"),
    )
    assert r_alta_dpo.status_code == 201, r_alta_dpo.text
    assert r_alta_dpo.json()["creado_por"] == dpo

    # 3. En una sesión de base de datos completamente nueva, los casos persisten
    async with capa_env["factory"]() as s_nueva:
        await fijar_contexto_rls(s_nueva, ta, implementador)
        persistidos = await listar_tickets_capa(s_nueva, ta)
    ids_persistidos = {t.id for t in persistidos}
    assert creado["id"] in ids_persistidos

    # 4. Cierre por admin_organizacion: se ignora cualquier auditor_id enviado en el cuerpo
    r_cierre = await capa_client.post(
        f"/api/v1/capa/tickets/{creado['id']}/cerrar",
        headers=_headers(ta, admin, "admin_organizacion"),
        json={"auditor_id": "auditor-falso-enviado-en-body", "evidencia_id": "EVD-2026-ADENDA-01"},
    )
    assert r_cierre.status_code == 200, r_cierre.text
    cerrado = r_cierre.json()
    assert cerrado["estado"] == "CERRADO_VERIFICADO"
    assert cerrado["auditor_verificador_id"] == admin
    assert cerrado["evidencia_cierre_id"] == "EVD-2026-ADENDA-01"
    assert cerrado["fecha_cierre"] is not None

    # 5. Cada alta y cada cierre dejaron su evento en audit_events
    async with capa_env["factory"]() as s_audit:
        await fijar_contexto_rls(s_audit, ta, admin)
        filas_audit = (
            await s_audit.execute(
                text(
                    "SELECT action, user_id FROM audit_events "
                    "WHERE tenant_id = :t AND entity_type = 'capa_ticket' AND entity_id = :eid"
                ),
                {"t": ta, "eid": creado["id"]},
            )
        ).mappings().all()
    acciones = {(f["action"], f["user_id"]) for f in filas_audit}
    assert ("registrar_hallazgo", coordinador) in acciones
    assert ("cerrar_hallazgo", admin) in acciones


async def test_permisos_por_rol_en_registro_consulta_y_cierre(capa_env, capa_client):
    """Solo coordinador y dpo registran; admin_organizacion, coordinador, dpo e implementador consultan; solo coordinador y admin_organizacion cierran."""
    ta = capa_env["a"]
    usuarios = capa_env["usuarios"]
    implementador = usuarios["implementador"]

    # Roles sin permiso de registro -> 403
    for rol_no_registra in ("implementador", "admin_organizacion", "responsable_area"):
        r = await capa_client.post(
            "/api/v1/capa/tickets",
            headers=_headers(ta, usuarios[rol_no_registra], rol_no_registra),
            json=_payload_base(implementador),
        )
        assert r.status_code == 403, f"El rol {rol_no_registra} no debe poder registrar hallazgos CAPA"

    # Crear un ticket válido con coordinador
    r_ok = await capa_client.post(
        "/api/v1/capa/tickets",
        headers=_headers(ta, usuarios["coordinador"], "coordinador"),
        json=_payload_base(implementador),
    )
    assert r_ok.status_code == 201
    ticket_id = r_ok.json()["id"]

    # Consulta permitida para admin_organizacion, coordinador, dpo e implementador -> 200
    for rol_lectura in ("admin_organizacion", "coordinador", "dpo", "implementador"):
        r_get = await capa_client.get(
            "/api/v1/capa/tickets",
            headers=_headers(ta, usuarios[rol_lectura], rol_lectura),
        )
        assert r_get.status_code == 200, f"El rol {rol_lectura} debe poder consultar CAPA"
        assert any(t["id"] == ticket_id for t in r_get.json())

    # Consulta prohibida para responsable_area -> 403
    r_get_denegado = await capa_client.get(
        "/api/v1/capa/tickets",
        headers=_headers(ta, usuarios["responsable_area"], "responsable_area"),
    )
    assert r_get_denegado.status_code == 403

    # Cierre prohibido para dpo, implementador y responsable_area -> 403
    for rol_no_cierra in ("dpo", "implementador", "responsable_area"):
        r_close = await capa_client.post(
            f"/api/v1/capa/tickets/{ticket_id}/cerrar",
            headers=_headers(ta, usuarios[rol_no_cierra], rol_no_cierra),
            json={"evidencia_id": "EVD-INTENTO-NO-AUTORIZADO"},
        )
        assert r_close.status_code == 403, f"El rol {rol_no_cierra} no debe poder cerrar CAPA"
        if rol_no_cierra == "dpo":
            assert "Violación SoD" in r_close.json()["detail"]


async def test_responsable_no_puede_cerrar_su_propia_accion_aunque_sea_coordinador_o_admin(
    capa_env, capa_client
):
    """El responsable de la acción no puede cerrarla (403 SoD), aunque tenga rol coordinador o admin_organizacion."""
    ta = capa_env["a"]
    coordinador = capa_env["usuarios"]["coordinador"]
    admin = capa_env["usuarios"]["admin_organizacion"]
    dpo = capa_env["usuarios"]["dpo"]

    # Caso 1: el responsable es el propio coordinador
    r_alta_coord = await capa_client.post(
        "/api/v1/capa/tickets",
        headers=_headers(ta, dpo, "dpo"),
        json=_payload_base(coordinador, control_id="P31"),
    )
    assert r_alta_coord.status_code == 201
    ticket_coord_id = r_alta_coord.json()["id"]

    # El coordinador intenta cerrar su propia acción (incluso enviando otro auditor_id en el body) -> 403
    r_auto_coord = await capa_client.post(
        f"/api/v1/capa/tickets/{ticket_coord_id}/cerrar",
        headers=_headers(ta, coordinador, "coordinador"),
        json={"auditor_id": admin, "evidencia_id": "EVD-AUTO-CIERRE-COORD"},
    )
    assert r_auto_coord.status_code == 403
    assert "SoD" in r_auto_coord.json()["detail"]

    # En cambio, admin_organizacion (persona distinta) sí puede cerrarlo -> 200
    r_cierre_independiente = await capa_client.post(
        f"/api/v1/capa/tickets/{ticket_coord_id}/cerrar",
        headers=_headers(ta, admin, "admin_organizacion"),
        json={"evidencia_id": "EVD-CIERRE-POR-ADMIN"},
    )
    assert r_cierre_independiente.status_code == 200
    assert r_cierre_independiente.json()["auditor_verificador_id"] == admin

    # Caso 2: el responsable es admin_organizacion
    r_alta_admin = await capa_client.post(
        "/api/v1/capa/tickets",
        headers=_headers(ta, coordinador, "coordinador"),
        json=_payload_base(admin, control_id="P32"),
    )
    assert r_alta_admin.status_code == 201
    ticket_admin_id = r_alta_admin.json()["id"]

    # admin_organizacion intenta cerrar su propia acción -> 403
    r_auto_admin = await capa_client.post(
        f"/api/v1/capa/tickets/{ticket_admin_id}/cerrar",
        headers=_headers(ta, admin, "admin_organizacion"),
        json={"evidencia_id": "EVD-AUTO-CIERRE-ADMIN"},
    )
    assert r_auto_admin.status_code == 403
    assert "SoD" in r_auto_admin.json()["detail"]


async def test_responsable_debe_ser_miembro_activo_de_la_organizacion(capa_env, capa_client):
    """Si el responsable no existe o pertenece a otra organización, el alta devuelve 422."""
    ta = capa_env["a"]
    coordinador = capa_env["usuarios"]["coordinador"]
    impl_otra_org = capa_env["usuarios_b"]["implementador"]

    # Usuario inexistente -> 422
    r_inexistente = await capa_client.post(
        "/api/v1/capa/tickets",
        headers=_headers(ta, coordinador, "coordinador"),
        json=_payload_base("usuario-no-miembro-999"),
    )
    assert r_inexistente.status_code == 422

    # Usuario miembro activo pero de otra organización (tb) -> 422
    r_otra_org = await capa_client.post(
        "/api/v1/capa/tickets",
        headers=_headers(ta, coordinador, "coordinador"),
        json=_payload_base(impl_otra_org),
    )
    assert r_otra_org.status_code == 422


async def test_caso_cerrado_no_se_modifica_y_devuelve_409(capa_env, capa_client):
    """Un ticket ya cerrado devuelve 409 al intentar cerrarlo de nuevo y conserva su verificador y evidencia originales."""
    ta = capa_env["a"]
    coordinador = capa_env["usuarios"]["coordinador"]
    admin = capa_env["usuarios"]["admin_organizacion"]
    implementador = capa_env["usuarios"]["implementador"]

    r_alta = await capa_client.post(
        "/api/v1/capa/tickets",
        headers=_headers(ta, coordinador, "coordinador"),
        json=_payload_base(implementador, control_id="P45"),
    )
    assert r_alta.status_code == 201
    ticket_id = r_alta.json()["id"]

    # Primer cierre por coordinador -> 200
    r_cierre_1 = await capa_client.post(
        f"/api/v1/capa/tickets/{ticket_id}/cerrar",
        headers=_headers(ta, coordinador, "coordinador"),
        json={"evidencia_id": "EVD-ORIGINAL-01"},
    )
    assert r_cierre_1.status_code == 200
    fecha_cierre_1 = r_cierre_1.json()["fecha_cierre"]

    # Segundo intento de cierre (por admin_organizacion) -> 409 Conflict
    r_cierre_2 = await capa_client.post(
        f"/api/v1/capa/tickets/{ticket_id}/cerrar",
        headers=_headers(ta, admin, "admin_organizacion"),
        json={"evidencia_id": "EVD-SOBREESCRITURA-02"},
    )
    assert r_cierre_2.status_code == 409

    # Verificar que los datos de cierre originales siguen intactos
    r_lista = await capa_client.get(
        "/api/v1/capa/tickets",
        headers=_headers(ta, admin, "admin_organizacion"),
    )
    assert r_lista.status_code == 200
    encontrado = next(t for t in r_lista.json() if t["id"] == ticket_id)
    assert encontrado["auditor_verificador_id"] == coordinador
    assert encontrado["evidencia_cierre_id"] == "EVD-ORIGINAL-01"
    assert encontrado["fecha_cierre"] == fecha_cierre_1


async def test_rls_aislamiento_entre_organizaciones_y_sin_delete_para_lopdp_app(
    capa_env, capa_client
):
    """RLS con SET LOCAL ROLE lopdp_app impide leer, insertar o actualizar casos de otra organización y prohíbe DELETE."""
    from app_core.db.session import fijar_contexto_rls

    ta = capa_env["a"]
    tb = capa_env["b"]
    coord_a = capa_env["usuarios"]["coordinador"]
    impl_a = capa_env["usuarios"]["implementador"]
    admin_b = capa_env["usuarios_b"]["admin_organizacion"]

    r_alta = await capa_client.post(
        "/api/v1/capa/tickets",
        headers=_headers(ta, coord_a, "coordinador"),
        json=_payload_base(impl_a, control_id="P60"),
    )
    assert r_alta.status_code == 201
    ticket_a_id = r_alta.json()["id"]

    # Desde la API, la organización B no ve ni puede cerrar el caso de la organización A
    r_lista_b = await capa_client.get(
        "/api/v1/capa/tickets",
        headers=_headers(tb, admin_b, "admin_organizacion"),
    )
    assert r_lista_b.status_code == 200
    assert r_lista_b.json() == []

    r_cierre_b = await capa_client.post(
        f"/api/v1/capa/tickets/{ticket_a_id}/cerrar",
        headers=_headers(tb, admin_b, "admin_organizacion"),
        json={"evidencia_id": "EVD-CRUZADA"},
    )
    assert r_cierre_b.status_code == 404

    # Bajo SET LOCAL ROLE lopdp_app con tenant B: no lee ni actualiza filas de A, ni inserta para A
    async with capa_env["factory"]() as s_rls:
        await s_rls.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s_rls, tb, admin_b)

        filas_b = (
            await s_rls.execute(
                text("SELECT id FROM capa_tickets WHERE id = :id"),
                {"id": ticket_a_id},
            )
        ).all()
        assert filas_b == []

        upd = await s_rls.execute(
            text("UPDATE capa_tickets SET estado = 'CERRADO_VERIFICADO' WHERE id = :id"),
            {"id": ticket_a_id},
        )
        assert upd.rowcount == 0

        with pytest.raises(DBAPIError):
            await s_rls.execute(
                text(
                    "INSERT INTO capa_tickets "
                    "(id, tenant_id, control_id, severidad, descripcion_hallazgo, causa_raiz, "
                    "accion_correctiva, responsable_implementacion_id, creado_por, estado, "
                    "snapshot_normativo, fecha_creacion) "
                    "VALUES (:id, :t, 'P1', 'OBSERVACION', 'x', 'y', 'z', :r, :c, 'ABIERTO', "
                    "'LOPDP-Ecuador-2021', now())"
                ),
                {"id": str(uuid4()), "t": ta, "r": impl_a, "c": admin_b},
            )
        await s_rls.rollback()

    # Bajo SET LOCAL ROLE lopdp_app con tenant A: DELETE está revocado para lopdp_app
    async with capa_env["factory"]() as s_del:
        await s_del.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s_del, ta, coord_a)
        with pytest.raises(DBAPIError) as exc_del:
            await s_del.execute(
                text("DELETE FROM capa_tickets WHERE id = :id"),
                {"id": ticket_a_id},
            )
        assert exc_del.value.orig.sqlstate == "42501"
        await s_del.rollback()

    # lopdp_app solo puede escribir las columnas del cierre: el hallazgo no se reescribe
    reescrituras = (
        "UPDATE capa_tickets SET descripcion_hallazgo = 'reescrito' WHERE id = :id",
        "UPDATE capa_tickets SET causa_raiz = 'reescrito' WHERE id = :id",
        "UPDATE capa_tickets SET accion_correctiva = 'reescrito' WHERE id = :id",
        "UPDATE capa_tickets SET responsable_implementacion_id = 'reescrito' WHERE id = :id",
    )
    for sentencia in reescrituras:
        async with capa_env["factory"]() as s_upd:
            await s_upd.execute(text("SET LOCAL ROLE lopdp_app"))
            await fijar_contexto_rls(s_upd, ta, coord_a)
            with pytest.raises(DBAPIError) as exc_upd:
                await s_upd.execute(text(sentencia), {"id": ticket_a_id})
            assert exc_upd.value.orig.sqlstate == "42501", sentencia
            await s_upd.rollback()
