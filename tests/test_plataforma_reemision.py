# ¤seguridad
# ¤rbac-tenant
# ¤arbitro
"""Árbitro ORG-11: reemisión segura de la invitación inicial."""
from __future__ import annotations

import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

pytestmark = pytest.mark.asyncio


def _async_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada")
    return url.replace("postgresql://", "postgresql+psycopg://", 1)


@pytest_asyncio.fixture
async def conn():
    engine = create_async_engine(_async_url(), echo=False)
    async with engine.connect() as connection:
        trans = await connection.begin()
        yield connection
        await trans.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def cliente_http(conn):
    from app_core.db.session import get_session
    from main import app

    async def _override_session():
        factory = async_sessionmaker(bind=conn, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.pop(get_session, None)


async def _crear_operador(conn) -> tuple[str, dict[str, str]]:
    operador_id = f"op-{uuid.uuid4().hex[:10]}"
    email = f"operador-{uuid.uuid4().hex[:8]}@example.test"
    await conn.execute(
        text(
            """
            INSERT INTO operadores_plataforma (id, email, nombre, activo)
            VALUES (:id, :email, 'Operador ORG-11', TRUE)
            """
        ),
        {"id": operador_id, "email": email},
    )
    return operador_id, {"X-User-Email": email, "X-User-ID": operador_id}


async def _crear_organizacion(conn, cliente_http) -> tuple[str, dict[str, str], dict]:
    operador_id, headers = await _crear_operador(conn)
    respuesta = await cliente_http.post(
        "/api/v1/plataforma/organizaciones",
        headers=headers,
        json={
            "nombre_comercial": "Organización ORG-11",
            "razon_social": "Organización ORG-11 S.A.",
            "ruc_identificacion": f"17{uuid.uuid4().int % 10000000000:010d}001",
            "tamano": "mediana",
            "email_admin_inicial": "admin-inicial@example.test",
        },
    )
    assert respuesta.status_code == 201, respuesta.text
    return operador_id, headers, respuesta.json()


async def test_reemite_tras_caducar_y_revoca_la_anterior(conn, cliente_http, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    operador_id, headers, alta = await _crear_organizacion(conn, cliente_http)
    await conn.execute(
        text("UPDATE invitaciones_organizacion SET expira_en = NOW() - INTERVAL '1 day' WHERE id = :id"),
        {"id": alta["invitacion_id"]},
    )

    respuesta = await cliente_http.post(
        f"/api/v1/plataforma/organizaciones/{alta['tenant_id']}/invitaciones",
        headers=headers,
    )

    assert respuesta.status_code == 200, respuesta.text
    nueva = respuesta.json()
    assert nueva["invitacion_id"] != alta["invitacion_id"]
    anterior = (
        await conn.execute(
            text("SELECT estado, revoked_by FROM invitaciones_organizacion WHERE id = :id"),
            {"id": alta["invitacion_id"]},
        )
    ).mappings().one()
    assert anterior == {"estado": "revocada", "revoked_by": operador_id}


async def test_reemite_tras_revocar_y_reutiliza_el_correo(conn, cliente_http, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    _operador_id, headers, alta = await _crear_organizacion(conn, cliente_http)
    revocada = await cliente_http.post(
        f"/api/v1/plataforma/invitaciones/{alta['invitacion_id']}/revocar",
        headers=headers,
    )
    assert revocada.status_code == 200

    respuesta = await cliente_http.post(
        f"/api/v1/plataforma/organizaciones/{alta['tenant_id']}/invitaciones",
        headers=headers,
    )

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["email_invitado"] == "admin-inicial@example.test"


async def test_reemision_rechaza_organizacion_con_admin_activo(conn, cliente_http, monkeypatch):
    """Prueba diana: falla si se elimina la comprobación de administrador activo."""
    monkeypatch.setenv("AUTH_MODE", "headers")
    _operador_id, headers, alta = await _crear_organizacion(conn, cliente_http)
    usuario_id = f"u-{uuid.uuid4().hex[:10]}"
    await conn.execute(
        text("INSERT INTO users (id, email, nombre) VALUES (:id, :email, 'Admin ORG-11')"),
        {"id": usuario_id, "email": f"{usuario_id}@example.test"},
    )
    await conn.execute(
        text(
            """
            INSERT INTO user_tenant_roles (id, user_id, tenant_id, role)
            VALUES (:id, :user_id, :tenant_id, 'admin_organizacion')
            """
        ),
        {"id": f"r-{uuid.uuid4().hex[:10]}", "user_id": usuario_id, "tenant_id": alta["tenant_id"]},
    )

    respuesta = await cliente_http.post(
        f"/api/v1/plataforma/organizaciones/{alta['tenant_id']}/invitaciones",
        headers=headers,
    )

    assert respuesta.status_code == 409
    assert "administrador activo" in respuesta.json()["detail"]


async def test_reemision_responde_404_sin_organizacion(conn, cliente_http, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    _operador_id, headers = await _crear_operador(conn)
    respuesta = await cliente_http.post(
        "/api/v1/plataforma/organizaciones/tenant-inexistente/invitaciones",
        headers=headers,
        json={"email_admin_inicial": "nuevo-admin@example.test"},
    )
    assert respuesta.status_code == 404


async def test_reemision_rechaza_no_operador(cliente_http, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    respuesta = await cliente_http.post(
        "/api/v1/plataforma/organizaciones/tenant-inexistente/invitaciones",
        headers={"X-User-Email": "no-operador@example.test", "X-User-ID": "no-operador"},
    )
    assert respuesta.status_code == 403


async def test_indice_impide_dos_emitidas_para_el_mismo_tenant(conn, cliente_http, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    _operador_id, _headers, alta = await _crear_organizacion(conn, cliente_http)
    with pytest.raises(IntegrityError):
        async with conn.begin_nested():
            await conn.execute(
                text(
                    """
                    INSERT INTO invitaciones_organizacion (
                        id, tenant_id, email, codigo_hash, expira_en, estado, created_by
                    ) VALUES (:id, :tenant_id, :email, :hash, NOW() + INTERVAL '7 days', 'emitida', :actor)
                    """
                ),
                {
                    "id": f"inv-{uuid.uuid4().hex[:10]}",
                    "tenant_id": alta["tenant_id"],
                    "email": "duplicada@example.test",
                    "hash": uuid.uuid4().hex,
                    "actor": "prueba-org-11",
                },
            )


async def test_evento_reemision_no_guarda_codigo_en_claro(conn, cliente_http, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    _operador_id, headers, alta = await _crear_organizacion(conn, cliente_http)
    await cliente_http.post(
        f"/api/v1/plataforma/invitaciones/{alta['invitacion_id']}/revocar",
        headers=headers,
    )
    respuesta = await cliente_http.post(
        f"/api/v1/plataforma/organizaciones/{alta['tenant_id']}/invitaciones",
        headers=headers,
        json={"email_admin_inicial": "corregido@example.test"},
    )
    assert respuesta.status_code == 200, respuesta.text

    evento = (
        await conn.execute(
            text(
                """
                SELECT payload
                FROM auditoria_plataforma
                WHERE tenant_id = :tenant_id AND accion = 'reemitir_invitacion'
                ORDER BY created_at DESC LIMIT 1
                """
            ),
            {"tenant_id": alta["tenant_id"]},
        )
    ).scalar_one()
    assert evento["invitacion_id"] == respuesta.json()["invitacion_id"]
    assert evento["invitacion_revocada_id"] is None
    assert respuesta.json()["codigo_invitacion"] not in str(evento)


async def test_reemision_rechaza_admin_activo_tambien_con_el_rol_de_la_aplicacion(conn, cliente_http, monkeypatch):
    """Como en producción: lopdp_app sin tenant fijado no ve user_tenant_roles (RLS).

    La comprobación de administrador activo no puede depender de leer esa tabla con el
    contexto del operador, que nunca fija tenant (ORG-09).
    """
    monkeypatch.setenv("AUTH_MODE", "headers")
    _operador_id, headers, alta = await _crear_organizacion(conn, cliente_http)
    usuario_id = f"u-{uuid.uuid4().hex[:10]}"
    await conn.execute(
        text("INSERT INTO users (id, email, nombre) VALUES (:id, :email, 'Admin ORG-11')"),
        {"id": usuario_id, "email": f"{usuario_id}@example.test"},
    )
    await conn.execute(
        text(
            """
            INSERT INTO user_tenant_roles (id, user_id, tenant_id, role)
            VALUES (:id, :user_id, :tenant_id, 'admin_organizacion')
            """
        ),
        {"id": f"r-{uuid.uuid4().hex[:10]}", "user_id": usuario_id, "tenant_id": alta["tenant_id"]},
    )
    await conn.execute(text("SET LOCAL ROLE lopdp_app"))

    respuesta = await cliente_http.post(
        f"/api/v1/plataforma/organizaciones/{alta['tenant_id']}/invitaciones",
        headers=headers,
    )

    assert respuesta.status_code == 409, respuesta.text
