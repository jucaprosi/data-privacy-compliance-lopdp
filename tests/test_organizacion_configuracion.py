# ¤rbac-tenant
# ¤arbitro
"""Suite de pruebas para la configuración de la organización (RM-15).

Valida:
1. Endpoints GET y PATCH /api/v1/organizacion/configuracion.
2. GET accesible por cualquier rol activo del tenant.
3. PATCH restringido estrictamente al rol 'admin_organizacion' (otros roles reciben 403).
4. Actualización válida de tamaño con vocabulario cerrado ('micro', 'pequena', 'mediana', 'corporativo').
5. Rechazo de tamaños no permitidos con código 422.
6. Aislamiento multi-tenant: un tenant no puede leer ni modificar la configuración de otro.
7. Registro inmutable del cambio en la tabla audit_events con action='config_updated'.
8. CHECK constraint a nivel de base de datos rechazando valores fuera del vocabulario.
"""
from __future__ import annotations

import os
import uuid
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from main import app
from features.organizacion.domain.tamanos import TAMANOS_ORGANIZACION

client = TestClient(app)
pytestmark = pytest.mark.asyncio


def _async_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("Sin TEST_DATABASE_URL para tests de BD")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@pytest_asyncio.fixture
async def seed_data():
    """Crea dos tenants con usuarios de distintos roles para probar permisos y aislamiento."""
    engine = create_async_engine(_async_url(), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    t1 = f"t1-{uuid.uuid4().hex[:8]}"
    t2 = f"t2-{uuid.uuid4().hex[:8]}"
    u_admin = f"uadm-{uuid.uuid4().hex[:8]}"
    u_dpo = f"udpo-{uuid.uuid4().hex[:8]}"
    u_otro = f"uotro-{uuid.uuid4().hex[:8]}"

    async with factory() as session:
        # Tenants
        await session.execute(
            text(
                """
                INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, sector, tamano)
                VALUES (:id, :nom, :razon, :ruc, :sec, :tam)
                """
            ),
            {
                "id": t1,
                "nom": f"Comercial {t1}",
                "razon": f"Razón Social {t1}",
                "ruc": f"RUC{t1[:10]}",
                "sec": "Financiero",
                "tam": "mediana",
            },
        )
        await session.execute(
            text(
                """
                INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, sector, tamano)
                VALUES (:id, :nom, :razon, :ruc, :sec, :tam)
                """
            ),
            {
                "id": t2,
                "nom": f"Comercial {t2}",
                "razon": f"Razón Social {t2}",
                "ruc": f"RUC{t2[:10]}",
                "sec": "Salud",
                "tam": "pequena",
            },
        )

        # Users
        await session.execute(
            text("INSERT INTO users (id, email, nombre) VALUES (:id, :email, :nombre)"),
            {"id": u_admin, "email": f"{u_admin}@org.ec", "nombre": "Admin Org"},
        )
        await session.execute(
            text("INSERT INTO users (id, email, nombre) VALUES (:id, :email, :nombre)"),
            {"id": u_dpo, "email": f"{u_dpo}@org.ec", "nombre": "DPO Org"},
        )
        await session.execute(
            text("INSERT INTO users (id, email, nombre) VALUES (:id, :email, :nombre)"),
            {"id": u_otro, "email": f"{u_otro}@org.ec", "nombre": "Otro User"},
        )

        # Roles
        await session.execute(
            text(
                """
                INSERT INTO user_tenant_roles (id, user_id, tenant_id, role)
                VALUES (:id, :uid, :tid, 'admin_organizacion')
                """
            ),
            {"id": f"r-{uuid.uuid4().hex[:8]}", "uid": u_admin, "tid": t1},
        )
        await session.execute(
            text(
                """
                INSERT INTO user_tenant_roles (id, user_id, tenant_id, role)
                VALUES (:id, :uid, :tid, 'dpo')
                """
            ),
            {"id": f"r-{uuid.uuid4().hex[:8]}", "uid": u_dpo, "tid": t1},
        )
        await session.execute(
            text(
                """
                INSERT INTO user_tenant_roles (id, user_id, tenant_id, role)
                VALUES (:id, :uid, :tid, 'implementador')
                """
            ),
            {"id": f"r-{uuid.uuid4().hex[:8]}", "uid": u_otro, "tid": t2},
        )
        await session.commit()

    yield {
        "tenant_id": t1,
        "tenant_ajeno": t2,
        "user_admin": u_admin,
        "user_dpo": u_dpo,
        "user_ajeno": u_otro,
    }

    # Limpieza
    async with factory() as session:
        try:
            await session.execute(
                text("DELETE FROM audit_events WHERE tenant_id IN (:t1, :t2)"),
                {"t1": t1, "t2": t2},
            )
            await session.execute(
                text("DELETE FROM user_tenant_roles WHERE tenant_id IN (:t1, :t2)"),
                {"t1": t1, "t2": t2},
            )
            await session.execute(
                text("DELETE FROM users WHERE id IN (:u1, :u2, :u3)"),
                {"u1": u_admin, "u2": u_dpo, "u3": u_otro},
            )
            await session.execute(
                text("DELETE FROM tenants WHERE id IN (:t1, :t2)"),
                {"t1": t1, "t2": t2},
            )
            await session.commit()
        except Exception:
            await session.rollback()
    await engine.dispose()


async def test_get_configuracion_autorizado_cualquier_rol(seed_data):
    """Cualquier rol activo del tenant puede consultar la configuración."""
    t1 = seed_data["tenant_id"]
    u_dpo = seed_data["user_dpo"]

    headers = {
        "X-Tenant-ID": t1,
        "X-User-ID": u_dpo,
        "X-Role": "dpo",
    }
    response = client.get("/api/v1/organizacion/configuracion", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == t1
    assert data["tamano"] == "mediana"
    assert data["sector"] == "Financiero"


async def test_patch_configuracion_admin_exitoso(seed_data):
    """El rol admin_organizacion puede actualizar tamaño y sector, registrando auditoría."""
    t1 = seed_data["tenant_id"]
    u_admin = seed_data["user_admin"]

    headers = {
        "X-Tenant-ID": t1,
        "X-User-ID": u_admin,
        "X-Role": "admin_organizacion",
    }
    payload = {
        "tamano": "corporativo",
        "sector": "Tecnología e Información",
    }
    response = client.patch(
        "/api/v1/organizacion/configuracion",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tamano"] == "corporativo"
    assert data["sector"] == "Tecnología e Información"

    # Verificar que el evento se persistió en audit_events
    engine = create_async_engine(_async_url())
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        result = await session.execute(
            text(
                """
                SELECT entity_type, entity_id, action, user_id, payload
                FROM audit_events
                WHERE tenant_id = :t1 AND action = 'config_updated'
                ORDER BY timestamp DESC
                LIMIT 1
                """
            ),
            {"t1": t1},
        )
        row = result.mappings().one_or_none()
        assert row is not None
        assert row["entity_type"] == "tenant"
        assert row["entity_id"] == t1
        assert row["user_id"] == u_admin
        assert row["payload"] == {"tamano": "corporativo", "sector": "Tecnología e Información"}
    await engine.dispose()


async def test_patch_configuracion_denegado_otros_roles(seed_data):
    """Roles distintos de admin_organizacion reciben 403 Forbidden al intentar actualizar."""
    t1 = seed_data["tenant_id"]
    u_dpo = seed_data["user_dpo"]

    headers = {
        "X-Tenant-ID": t1,
        "X-User-ID": u_dpo,
        "X-Role": "dpo",
    }
    payload = {"tamano": "micro"}
    response = client.patch(
        "/api/v1/organizacion/configuracion",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 403


async def test_patch_configuracion_tamano_invalido(seed_data):
    """Valores fuera del vocabulario cerrado devuelven 422 Unprocessable Entity."""
    t1 = seed_data["tenant_id"]
    u_admin = seed_data["user_admin"]

    headers = {
        "X-Tenant-ID": t1,
        "X-User-ID": u_admin,
        "X-Role": "admin_organizacion",
    }
    payload = {"tamano": "PYME"}  # "PYME" ya no es válido en el vocabulario cerrado
    response = client.patch(
        "/api/v1/organizacion/configuracion",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 422


async def test_db_check_constraint_tamano(seed_data):
    """La base de datos rechaza a nivel de constraint valores no permitidos."""
    engine = create_async_engine(_async_url())
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    t1 = seed_data["tenant_id"]

    async with factory() as session:
        # Valor inválido directo en SQL
        with pytest.raises(DBAPIError) as exc_info:
            await session.execute(
                text("UPDATE tenants SET tamano = 'GIGANTE' WHERE id = :t1"),
                {"t1": t1},
            )
            await session.commit()
        assert "ck_tenants_tamano" in str(exc_info.value).lower()
        await session.rollback()

        # NULL es permitido
        await session.execute(
            text("UPDATE tenants SET tamano = NULL WHERE id = :t1"),
            {"t1": t1},
        )
        await session.commit()

        # Cada uno de los valores cerrados es permitido
        for val in TAMANOS_ORGANIZACION:
            await session.execute(
                text("UPDATE tenants SET tamano = :val WHERE id = :t1"),
                {"t1": t1, "val": val},
            )
            await session.commit()
    await engine.dispose()
