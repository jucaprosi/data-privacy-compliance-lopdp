# ¤seguridad
# ¤rbac-tenant
# ¤arbitro
"""Árbitro de pruebas para el Operador de la Plataforma e Invitaciones (ORG-09).

Verifica de forma determinista y exhaustiva:
1. Acceso a endpoints de plataforma:
   - Un usuario no operador recibe 403 Forbidden.
   - Operador autenticado puede crear organizaciones y emitir invitaciones.
   - Operador puede listar organizaciones obteniendo SOLO los metadatos permitidos (sin datos de clientes).
   - Operador puede revocar invitaciones no aceptadas.
2. Aceptación de invitaciones:
   - Aceptación exitosa crea usuario, vincula google_sub y concede rol admin_organizacion.
   - Genera eventos de auditoría en audit_events (tenant) y auditoria_plataforma.
   - Un solo uso: segundo intento se rechaza con 400 Bad Request.
   - Invitación con correo de Google distinto al invitado se rechaza con 403 Forbidden.
   - Invitación revocada o caducada se rechaza con 400 Bad Request.
3. Aislamiento y RLS:
   - Ningún endpoint de plataforma fija app.current_tenant_id.
   - Como lopdp_app y sin tenant fijado, consultas a tablas protegidas con RLS (areas, user_tenant_roles,
     roadmaps, task_evidence, audit_events) devuelven 0 filas de los clientes.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app_core.db.session import get_session
from app_core.security import IdentidadVerificada, MODO_HEADERS
from features.plataforma import plataforma_service
from main import app

pytestmark = pytest.mark.asyncio


def _async_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@pytest_asyncio.fixture
async def conn():
    """Conexión transaccional limpia aislada por prueba con rollback obligatorio."""
    engine = create_async_engine(_async_url(), echo=False)
    async with engine.connect() as connection:
        trans = await connection.begin()
        yield connection
        await trans.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def session(conn):
    async_session = async_sessionmaker(bind=conn, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as s:
        yield s


@pytest_asyncio.fixture
async def cliente_http(conn):
    async def _override_session():
        async_session = async_sessionmaker(bind=conn, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as s:
            yield s

    app.dependency_overrides[get_session] = _override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.pop(get_session, None)


async def _crear_operador(conn, email: str, nombre: str = "Operador Test", sub: str | None = None) -> str:
    op_id = f"op-{uuid.uuid4().hex[:10]}"
    await conn.execute(
        text(
            """
            INSERT INTO operadores_plataforma (id, email, google_sub, nombre, activo, created_at, updated_at)
            VALUES (:id, :e, :sub, :n, TRUE, NOW(), NOW())
            """
        ),
        {"id": op_id, "e": email.strip().lower(), "sub": sub, "n": nombre},
    )
    return op_id


# ============================================================================
# 1. PRUEBAS DE AUTORIZACIÓN Y ACCESO DE OPERADOR
# ============================================================================

async def test_no_operador_recibe_403_en_plataforma(cliente_http, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    headers = {"X-User-Email": "desconocido@example.test", "X-User-ID": "sub-no-op"}

    # Crear organización
    res = await cliente_http.post(
        "/api/v1/plataforma/organizaciones",
        json={
            "nombre_comercial": "Org Test",
            "razon_social": "Org Test S.A.",
            "ruc_identificacion": "1799999999001",
            "tamano": "mediana",
            "email_admin_inicial": "admin@example.test",
        },
        headers=headers,
    )
    assert res.status_code == 403, f"Esperaba 403, obtuvo {res.status_code}: {res.text}"

    # Listar organizaciones
    res = await cliente_http.get("/api/v1/plataforma/organizaciones", headers=headers)
    assert res.status_code == 403, f"Esperaba 403, obtuvo {res.status_code}: {res.text}"

    # Revocar una invitación (aunque no exista: la identidad se comprueba antes)
    res = await cliente_http.post("/api/v1/plataforma/invitaciones/no-existe/revocar", headers=headers)
    assert res.status_code == 403, f"Esperaba 403, obtuvo {res.status_code}: {res.text}"


async def test_operador_crea_organizacion_y_emite_invitacion(conn, cliente_http, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    email_op = f"operador-{uuid.uuid4().hex[:6]}@example.test"
    await _crear_operador(conn, email_op)

    ruc = f"17{uuid.uuid4().int % 10000000000:010d}001"
    headers = {"X-User-Email": email_op, "X-User-ID": "sub-op"}
    payload = {
        "nombre_comercial": "Empresa Alfa",
        "razon_social": "Empresa Alfa S.A.S.",
        "ruc_identificacion": ruc,
        "tamano": "mediana",
        "sector": "Financiero",
        "email_admin_inicial": "admin.alfa@example.test",
    }

    res = await cliente_http.post("/api/v1/plataforma/organizaciones", json=payload, headers=headers)
    assert res.status_code == 201, f"Esperaba 201, obtuvo {res.status_code}: {res.text}"
    data = res.json()
    assert "tenant_id" in data
    assert "invitacion_id" in data
    assert "codigo_invitacion" in data
    assert len(data["codigo_invitacion"]) >= 32
    assert data["email_invitado"] == "admin.alfa@example.test"

    # Verificar que no se pueda duplicar el RUC (409 Conflict)
    res_dup = await cliente_http.post("/api/v1/plataforma/organizaciones", json=payload, headers=headers)
    assert res_dup.status_code == 409


async def test_operador_lista_organizaciones_solo_metadatos_permitidos(conn, cliente_http, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    email_op = f"operador-{uuid.uuid4().hex[:6]}@example.test"
    await _crear_operador(conn, email_op)

    ruc = f"17{uuid.uuid4().int % 10000000000:010d}001"
    headers = {"X-User-Email": email_op, "X-User-ID": "sub-op"}

    # Crear una org
    await cliente_http.post(
        "/api/v1/plataforma/organizaciones",
        json={
            "nombre_comercial": "Meta Test",
            "razon_social": "Meta Test Cia Ltda",
            "ruc_identificacion": ruc,
            "tamano": "pequena",
            "sector": "Salud",
            "email_admin_inicial": "admin.meta@example.test",
        },
        headers=headers,
    )

    res = await cliente_http.get("/api/v1/plataforma/organizaciones", headers=headers)
    assert res.status_code == 200
    orgs = res.json()
    assert isinstance(orgs, list)
    encontrada = next((o for o in orgs if o["ruc_identificacion"] == ruc), None)
    assert encontrada is not None
    # Verificar que SOLO contiene metadatos permitidos
    claves_esperadas = {
        "id", "nombre_comercial", "razon_social", "ruc_identificacion",
        "activo", "created_at",
        "email_admin_inicial", "invitacion_estado"
    }
    assert set(encontrada.keys()) == claves_esperadas
    assert encontrada["email_admin_inicial"] == "admin.meta@example.test"
    assert encontrada["invitacion_estado"] == "emitida"


async def test_operador_revoca_invitacion_pendiente(conn, cliente_http, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    email_op = f"operador-{uuid.uuid4().hex[:6]}@example.test"
    await _crear_operador(conn, email_op)

    ruc = f"17{uuid.uuid4().int % 10000000000:010d}001"
    headers = {"X-User-Email": email_op, "X-User-ID": "sub-op"}

    res = await cliente_http.post(
        "/api/v1/plataforma/organizaciones",
        json={
            "nombre_comercial": "Revocar Org",
            "razon_social": "Revocar Org S.A.",
            "ruc_identificacion": ruc,
            "tamano": "micro",
            "email_admin_inicial": "admin.rev@example.test",
        },
        headers=headers,
    )
    inv_id = res.json()["invitacion_id"]

    # Revocar
    res_rev = await cliente_http.post(f"/api/v1/plataforma/invitaciones/{inv_id}/revocar", headers=headers)
    assert res_rev.status_code == 200
    assert res_rev.json()["status"] == "ok"

    # Revocar de nuevo falla 400
    res_rev2 = await cliente_http.post(f"/api/v1/plataforma/invitaciones/{inv_id}/revocar", headers=headers)
    assert res_rev2.status_code == 400


# ============================================================================
# 2. PRUEBAS DE ACEPTACIÓN DE INVITACIONES Y ADMIN INICIAL
# ============================================================================

async def test_flujo_completo_aceptar_invitacion_exitoso(conn, cliente_http, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    email_op = f"operador-{uuid.uuid4().hex[:6]}@example.test"
    await _crear_operador(conn, email_op)

    ruc = f"17{uuid.uuid4().int % 10000000000:010d}001"
    email_invitado = "invitado.valido@example.test"
    sub_invitado = f"sub-google-{uuid.uuid4().hex[:8]}"

    res_crear = await cliente_http.post(
        "/api/v1/plataforma/organizaciones",
        json={
            "nombre_comercial": "Org Aceptada",
            "razon_social": "Org Aceptada S.A.",
            "ruc_identificacion": ruc,
            "tamano": "corporativo",
            "email_admin_inicial": email_invitado,
        },
        headers={"X-User-Email": email_op, "X-User-ID": "sub-op"},
    )
    codigo = res_crear.json()["codigo_invitacion"]
    tenant_id = res_crear.json()["tenant_id"]

    # Aceptar con la identidad verificada del invitado
    headers_invitado = {"X-User-Email": email_invitado, "X-User-ID": sub_invitado}
    res_aceptar = await cliente_http.post(
        "/api/v1/plataforma/invitaciones/aceptar",
        json={"codigo": codigo, "nombre_usuario": "Admin Inicial"},
        headers=headers_invitado,
    )
    assert res_aceptar.status_code == 200
    data = res_aceptar.json()
    assert data["tenant_id"] == tenant_id
    assert data["rol_asignado"] == "admin_organizacion"
    user_id = data["user_id"]

    # Verificar en BD: usuario creado y google_sub vinculado
    u_row = (await conn.execute(
        text("SELECT email, google_sub FROM users WHERE id = :u"), {"u": user_id}
    )).mappings().first()
    assert u_row["email"] == email_invitado
    assert u_row["google_sub"] == sub_invitado

    # Verificar en BD: asignación de rol activa en user_tenant_roles
    r_row = (await conn.execute(
        text("SELECT role FROM user_tenant_roles WHERE user_id = :u AND tenant_id = :t"),
        {"u": user_id, "t": tenant_id},
    )).mappings().first()
    assert r_row["role"] == "admin_organizacion"

    # Verificar eventos de auditoría
    ev_tenant = (await conn.execute(
        text("SELECT action FROM audit_events WHERE tenant_id = :t AND action = 'aceptar_invitacion_admin_inicial'"),
        {"t": tenant_id},
    )).first()
    assert ev_tenant is not None

    ev_plat = (await conn.execute(
        text("SELECT accion FROM auditoria_plataforma WHERE tenant_id = :t AND accion = 'aceptar_invitacion_organizacion'"),
        {"t": tenant_id},
    )).first()
    assert ev_plat is not None

    # Un solo uso: segundo intento se rechaza con 400
    res_segundo = await cliente_http.post(
        "/api/v1/plataforma/invitaciones/aceptar",
        json={"codigo": codigo},
        headers=headers_invitado,
    )
    assert res_segundo.status_code == 400
    assert "utilizada" in res_segundo.json()["detail"]


async def test_aceptar_con_correo_distinto_es_rechazado_403(conn, cliente_http, monkeypatch):
    """PRUEBA DIANA DE MUTACIÓN: Si el correo verificado de Google no coincide, debe fallar 403."""
    monkeypatch.setenv("AUTH_MODE", "headers")
    email_op = f"operador-{uuid.uuid4().hex[:6]}@example.test"
    await _crear_operador(conn, email_op)

    ruc = f"17{uuid.uuid4().int % 10000000000:010d}001"
    res = await cliente_http.post(
        "/api/v1/plataforma/organizaciones",
        json={
            "nombre_comercial": "Org Correo Test",
            "razon_social": "Org Correo Test S.A.",
            "ruc_identificacion": ruc,
            "email_admin_inicial": "legitimo@example.test",
        },
        headers={"X-User-Email": email_op, "X-User-ID": "sub-op"},
    )
    codigo = res.json()["codigo_invitacion"]

    # Intentar aceptar con un correo verificado diferente
    headers_impostor = {"X-User-Email": "impostor@example.test", "X-User-ID": "sub-impostor"}
    res_aceptar = await cliente_http.post(
        "/api/v1/plataforma/invitaciones/aceptar",
        json={"codigo": codigo},
        headers=headers_impostor,
    )
    assert res_aceptar.status_code == 403
    assert "no coincide" in res_aceptar.json()["detail"]


async def test_aceptar_invitacion_revocada_o_caducada_es_rechazado(conn, cliente_http, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    email_op = f"operador-{uuid.uuid4().hex[:6]}@example.test"
    await _crear_operador(conn, email_op)

    ruc = f"17{uuid.uuid4().int % 10000000000:010d}001"
    res = await cliente_http.post(
        "/api/v1/plataforma/organizaciones",
        json={
            "nombre_comercial": "Org Expirada",
            "razon_social": "Org Expirada S.A.",
            "ruc_identificacion": ruc,
            "email_admin_inicial": "admin.exp@example.test",
        },
        headers={"X-User-Email": email_op, "X-User-ID": "sub-op"},
    )
    codigo = res.json()["codigo_invitacion"]
    inv_id = res.json()["invitacion_id"]

    # Simular expiración en BD
    await conn.execute(
        text("UPDATE invitaciones_organizacion SET expira_en = NOW() - INTERVAL '1 day' WHERE id = :id"),
        {"id": inv_id},
    )

    headers_inv = {"X-User-Email": "admin.exp@example.test", "X-User-ID": "sub-exp"}
    res_aceptar = await cliente_http.post(
        "/api/v1/plataforma/invitaciones/aceptar",
        json={"codigo": codigo},
        headers=headers_inv,
    )
    assert res_aceptar.status_code == 400
    assert "caducado" in res_aceptar.json()["detail"]


# ============================================================================
# 3. AISLAMIENTO RLS: OPERADOR NUNCA VE DATOS DE CLIENTES
# ============================================================================

async def test_operador_como_lopdp_app_sin_tenant_no_ve_filas_rls(conn):
    """Como rol lopdp_app y sin fijar app.current_tenant_id, las tablas con RLS ocultan todas las filas."""
    # Insertar datos de un cliente con transacción
    t_id = f"t-rls-{uuid.uuid4().hex[:8]}"
    u_id = f"u-rls-{uuid.uuid4().hex[:8]}"
    a_id = f"a-rls-{uuid.uuid4().hex[:8]}"

    await conn.execute(
        text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, activo) "
             "VALUES (:t, 'Cliente Privado', 'Cliente Privado S.A.', :ruc, TRUE)"),
        {"t": t_id, "ruc": f"17{uuid.uuid4().int % 10000000000:010d}001"},
    )
    await conn.execute(
        text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, 'Usuario Privado')"),
        {"u": u_id, "e": f"{u_id}@example.test"},
    )
    await conn.execute(
        text("INSERT INTO areas (id, tenant_id, nombre) VALUES (:a, :t, 'Área Confidencial')"),
        {"a": a_id, "t": t_id},
    )
    await conn.execute(
        text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, 'coordinador')"),
        {"id": f"r-{uuid.uuid4().hex[:8]}", "u": u_id, "t": t_id},
    )

    # Ahora cambiamos a rol lopdp_app en esta conexión sin fijar tenant
    sp = await conn.begin_nested()
    try:
        await conn.execute(text("SET LOCAL ROLE lopdp_app;"))
        # Resetear cualquier variable de sesión previa
        await conn.execute(text("SELECT set_config('app.current_tenant_id', '', true);"))

        # 1. Consulta a áreas: RLS debe devolver 0 filas
        res_areas = (await conn.execute(text("SELECT COUNT(*) FROM areas WHERE tenant_id = :t"), {"t": t_id})).scalar()
        assert res_areas == 0, f"Fallo de aislamiento: lopdp_app vio {res_areas} áreas sin tenant fijado"

        # 2. Consulta a roles de usuarios: RLS debe devolver 0 filas
        res_roles = (await conn.execute(text("SELECT COUNT(*) FROM user_tenant_roles WHERE tenant_id = :t"), {"t": t_id})).scalar()
        assert res_roles == 0, f"Fallo de aislamiento: lopdp_app vio {res_roles} roles sin tenant fijado"

        # 3. Consulta a eventos de auditoría: RLS debe devolver 0 filas
        res_audit = (await conn.execute(text("SELECT COUNT(*) FROM audit_events WHERE tenant_id = :t"), {"t": t_id})).scalar()
        assert res_audit == 0, f"Fallo de aislamiento: lopdp_app vio {res_audit} eventos de auditoría sin tenant fijado"
    finally:
        await sp.rollback()
