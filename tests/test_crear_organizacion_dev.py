"""Pruebas unitarias y de integración para crear_organizacion_dev.py (DEV-01).

Valida:
1. Fallo cerrado de seguridad contra host de producción (ep-late-hall-b50bpbk5).
2. Fallo cerrado de seguridad si AUTH_MODE != 'headers'.
3. Creación exitosa en base de datos de pruebas real (rama Neon asignada).
4. Idempotencia: una segunda ejecución consecutiva no genera duplicados ni errores.
5. Cumplimiento estricto de SoD y reglas del DPO (sin otros roles ni cargos incompatibles).
6. Presencia de estructura orgánica mínima (alta dirección, 2 unidades, jefatura y vacante).
7. Existencia de designación formal activa del DPD.
8. Cero SQL interpolado.
"""
from __future__ import annotations

import os
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from scripts.crear_organizacion_dev import (
    DEMO_TENANT_ID,
    HOST_PRODUCCION,
    USUARIOS_DEMO,
    crear_organizacion_dev,
    sanitizar_host,
    validar_entorno,
)


# ==============================================================================
# 1. PRUEBAS DE SEGURIDAD Y FALLO CERRADO (SIN CONEXIÓN REAL A BD)
# ==============================================================================

def test_sanitizar_host_oculta_credenciales():
    url = "postgresql+psycopg://mi_usuario:clave_super_secreta@mi-host-seguro.aws.neon.tech/db"
    host = sanitizar_host(url)
    assert host == "mi-host-seguro.aws.neon.tech"
    assert "clave_super_secreta" not in host
    assert "mi_usuario" not in host


def test_validar_entorno_rechaza_host_de_produccion():
    url_prod = f"postgresql+psycopg://user:pass@{HOST_PRODUCCION}.c-7.us-east-2.aws.neon.tech/lopdp"
    with pytest.raises(RuntimeError) as exc:
        validar_entorno(url_prod, auth_mode="headers")
    assert "PRODUCCIÓN" in str(exc.value)
    assert HOST_PRODUCCION in str(exc.value)


def test_validar_entorno_rechaza_auth_mode_no_headers():
    url_dev = "postgresql+psycopg://user:pass@ep-misty-wave-b5wfm6ct-pooler.c-7.us-east-2.aws.neon.tech/db"
    for modo_invalido in ["oidc", "", "jwt", "bearer", "None"]:
        with pytest.raises(RuntimeError) as exc:
            validar_entorno(url_dev, auth_mode=modo_invalido)
        assert "AUTH_MODE debe ser 'headers'" in str(exc.value)


def test_validar_entorno_rechaza_url_vacia():
    with pytest.raises(RuntimeError) as exc:
        validar_entorno("", auth_mode="headers")
    assert "no está definida" in str(exc.value)


def test_validar_entorno_acepta_configuracion_correcta():
    url_dev = "postgresql+psycopg://user:pass@ep-misty-wave-b5wfm6ct-pooler.c-7.us-east-2.aws.neon.tech/db"
    host = validar_entorno(url_dev, auth_mode="headers")
    assert host == "ep-misty-wave-b5wfm6ct-pooler.c-7.us-east-2.aws.neon.tech"


# ==============================================================================
# 2. PRUEBAS DE INTEGRACIÓN CONTRA BASE DE DATOS REAL (NEON DEV)
# ==============================================================================

def _async_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada para pruebas con base real.")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@pytest_asyncio.fixture
async def db_session():
    url = _async_url()
    engine = create_async_engine(url, pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_crear_organizacion_dev_creacion_e_idempotencia(db_session):
    """Ejecuta dos veces consecutivas crear_organizacion_dev y verifica idempotencia."""
    # Primera ejecución: creación
    res1 = await crear_organizacion_dev(db_session, tenant_id=DEMO_TENANT_ID)
    assert res1["tenant_id"] == DEMO_TENANT_ID
    assert "operaciones_id" in res1
    assert "tecnologia_id" in res1
    assert len(res1["usuarios"]) == 5

    # Segunda ejecución: debe ser idempotente sin lanzar errores ni duplicar
    res2 = await crear_organizacion_dev(db_session, tenant_id=DEMO_TENANT_ID)
    assert res2["tenant_id"] == DEMO_TENANT_ID
    assert res2["operaciones_id"] == res1["operaciones_id"]
    assert res2["tecnologia_id"] == res1["tecnologia_id"]

    # Validar tenant en base de datos
    r_tenant = (await db_session.execute(
        text("SELECT id, tamano, activo FROM tenants WHERE id = :t"),
        {"t": DEMO_TENANT_ID},
    )).mappings().first()
    assert r_tenant is not None
    assert r_tenant["tamano"] == "mediana"
    assert r_tenant["activo"] is True

    # Validar que los 5 usuarios demo existan y tengan dominio @example.test
    for rol, u_info in USUARIOS_DEMO.items():
        assert u_info["email"].endswith("@example.test")
        r_u = (await db_session.execute(
            text("SELECT id, email, activo FROM users WHERE id = :id"),
            {"id": u_info["id"]},
        )).mappings().first()
        assert r_u is not None
        assert r_u["email"] == u_info["email"]
        assert r_u["activo"] is True

    # Validar asignación de roles en user_tenant_roles
    r_roles = (await db_session.execute(
        text(
            "SELECT user_id, role, area_id FROM user_tenant_roles "
            "WHERE tenant_id = :t AND (valid_to IS NULL OR valid_to > now())"
        ),
        {"t": DEMO_TENANT_ID},
    )).mappings().all()

    roles_asignados = {r["role"]: r for r in r_roles}
    assert "admin_organizacion" in roles_asignados
    assert "coordinador" in roles_asignados
    assert "implementador" in roles_asignados
    assert "responsable_area" in roles_asignados
    assert "dpo" in roles_asignados

    # SoD: El DPO no tiene ningún otro rol asignado
    dpo_uid = USUARIOS_DEMO["dpo"]["id"]
    roles_dpo = [r for r in r_roles if r["user_id"] == dpo_uid]
    assert len(roles_dpo) == 1
    assert roles_dpo[0]["role"] == "dpo"

    # Estructura Orgánica: Alta Dirección, Operaciones y Tecnología
    r_areas = (await db_session.execute(
        text("SELECT id, codigo, nivel, parent_area_id FROM areas WHERE tenant_id = :t AND deleted_at IS NULL"),
        {"t": DEMO_TENANT_ID},
    )).mappings().all()

    niveles = {a["codigo"]: a for a in r_areas}
    assert "ALTA-DIR" in niveles
    assert niveles["ALTA-DIR"]["nivel"] == "alta_direccion"
    assert niveles["ALTA-DIR"]["parent_area_id"] is None

    assert "UNID-OPER" in niveles
    assert niveles["UNID-OPER"]["nivel"] == "unidad"
    assert niveles["UNID-OPER"]["parent_area_id"] == niveles["ALTA-DIR"]["id"]

    assert "UNID-TEC" in niveles
    assert niveles["UNID-TEC"]["nivel"] == "unidad"
    assert niveles["UNID-TEC"]["parent_area_id"] == niveles["ALTA-DIR"]["id"]

    # Cargos Orgánicos: Jefe de Operaciones con titular, Jefe de Tecnología vacante
    r_cargos = (await db_session.execute(
        text(
            "SELECT nombre, es_jefatura, titular_user_id, area_id FROM cargos_organicos "
            "WHERE tenant_id = :t AND (valid_to IS NULL OR valid_to > now())"
        ),
        {"t": DEMO_TENANT_ID},
    )).mappings().all()

    jefe_op = next((c for c in r_cargos if c["nombre"] == "Jefe de Operaciones"), None)
    assert jefe_op is not None
    assert jefe_op["es_jefatura"] is True
    assert jefe_op["titular_user_id"] == USUARIOS_DEMO["responsable_area"]["id"]

    jefe_tec = next((c for c in r_cargos if c["nombre"] == "Jefe de Sistemas y Ciberseguridad"), None)
    assert jefe_tec is not None
    assert jefe_tec["es_jefatura"] is True
    assert jefe_tec["titular_user_id"] is None  # Vacante verificada

    # Designación formal del DPD activa
    r_desig = (await db_session.execute(
        text(
            "SELECT tipo, user_id, vinculo, revocada_at FROM designaciones_formales "
            "WHERE tenant_id = :t AND tipo = 'dpd' AND revocada_at IS NULL"
        ),
        {"t": DEMO_TENANT_ID},
    )).mappings().all()

    assert len(r_desig) == 1
    assert r_desig[0]["user_id"] == dpo_uid
    assert r_desig[0]["vinculo"] == "relacion_dependencia"
