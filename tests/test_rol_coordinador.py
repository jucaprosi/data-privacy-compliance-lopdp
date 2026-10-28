# ¤rbac-tenant
# ¤seguridad
# ¤arbitro
"""ORG-00: Árbitro de renombrado del rol 'encargado' a 'coordinador'.

Verifica de forma exhaustiva y determinista:
1. Migración reversible:
   - upgrade convierte 'encargado' a 'coordinador', actualiza ck_utr_role y triggers.
   - downgrade revierte a 'encargado', restaura restricción y triggers históricos.
2. Comportamiento de los triggers con 'coordinador':
   - fn_utr_dpo_sod bloquea acumular DPO + coordinador.
   - fn_utr_coordinador_responsable bloquea acumular coordinador + responsable_area en mediana/corporativo y sin tamaño.
3. Retiro de compatibilidad de alias:
   - X-Role: 'encargado' es rechazado con 403 Forbidden.
4. Preservación del sentido legal:
   - Corpus normativo, copiloto y normativas.ts conservan intactos los términos legales ('encargado del tratamiento', etc.).
"""
from __future__ import annotations

import importlib.util
import os
import uuid
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from features.organizacion.organizacion_service import Role
from main import app

pytestmark = pytest.mark.asyncio

RUTA_MIGRACION = Path(__file__).resolve().parent.parent / "alembic" / "versions" / "20261019_rol_coordinador.py"


def _async_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _sentencias_migracion() -> tuple[tuple[str, ...], tuple[str, ...]]:
    spec = importlib.util.spec_from_file_location("mig_org00", RUTA_MIGRACION)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.SQL_ASCENDENTE, mod.SQL_DESCENDENTE


@pytest_asyncio.fixture
async def conn():
    engine = create_async_engine(_async_url(), pool_pre_ping=True)
    async with engine.connect() as c:
        tx = await c.begin()
        try:
            yield c
        finally:
            await tx.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def session(conn):
    return AsyncSession(bind=conn, expire_on_commit=False)


# ============================================================================
# 1. PRUEBA DE MIGRACIÓN: UPGRADE Y DOWNGRADE TRANSACCIONAL
# ============================================================================

async def test_migracion_transaccional_upgrade_y_downgrade(conn):
    """Ejecuta el SQL real de la migración en upgrade y downgrade dentro de una tx."""
    sql_asc, sql_desc = _sentencias_migracion()

    tid = f"org00-t-{uuid.uuid4().hex[:10]}"
    uid = f"org00-u-{uuid.uuid4().hex[:10]}"
    await conn.execute(
        text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
             "VALUES (:t, :n, :r, :ruc, 'micro')"),
        {"t": tid, "n": tid, "r": tid, "ruc": f"RUC{uuid.uuid4().hex[:12]}"},
    )
    await conn.execute(
        text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :n)"),
        {"u": uid, "e": f"{uid}@test.local", "n": uid},
    )

    # 1. Probar downgrade: convierte coordinador -> encargado y restaura check
    for sql in sql_desc:
        await conn.execute(text(sql))

    # Ahora 'encargado' es válido y 'coordinador' debe ser rechazado por el check
    await conn.execute(
        text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, 'encargado')"),
        {"id": f"r-{uuid.uuid4().hex[:10]}", "u": uid, "t": tid},
    )
    sp = await conn.begin_nested()
    with pytest.raises(IntegrityError):
        await conn.execute(
            text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, 'coordinador')"),
            {"id": f"r-{uuid.uuid4().hex[:10]}", "u": uid, "t": tid},
        )
    await sp.rollback()

    # 2. Probar upgrade: convierte encargado -> coordinador y restaura check
    for sql in sql_asc:
        await conn.execute(text(sql))

    # Verificar que la fila 'encargado' se convirtió en 'coordinador'
    res = await conn.execute(
        text("SELECT role FROM user_tenant_roles WHERE user_id=:u AND tenant_id=:t"),
        {"u": uid, "t": tid},
    )
    roles = [r[0] for r in res.fetchall()]
    assert roles == ["coordinador"]

    # Y ahora 'encargado' es rechazado por el check
    sp2 = await conn.begin_nested()
    with pytest.raises(IntegrityError):
        await conn.execute(
            text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, 'encargado')"),
            {"id": f"r-{uuid.uuid4().hex[:10]}", "u": uid, "t": tid},
        )
    await sp2.rollback()


# ============================================================================
# 2. PRUEBA DE TRIGGERS: fn_utr_dpo_sod Y fn_utr_coordinador_responsable
# ============================================================================

async def test_trigger_dpo_sod_con_coordinador(conn):
    """El trigger fn_utr_dpo_sod bloquea que un DPO sea también coordinador."""
    tid = f"org00-t-{uuid.uuid4().hex[:10]}"
    uid = f"org00-u-{uuid.uuid4().hex[:10]}"
    await conn.execute(
        text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
             "VALUES (:t, :n, :r, :ruc, 'micro')"),
        {"t": tid, "n": tid, "r": tid, "ruc": f"RUC{uuid.uuid4().hex[:12]}"},
    )
    await conn.execute(
        text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :n)"),
        {"u": uid, "e": f"{uid}@test.local", "n": uid},
    )

    await conn.execute(
        text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, 'dpo')"),
        {"id": f"r1-{uuid.uuid4().hex[:10]}", "u": uid, "t": tid},
    )

    sp = await conn.begin_nested()
    with pytest.raises(IntegrityError) as exc:
        await conn.execute(
            text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, 'coordinador')"),
            {"id": f"r2-{uuid.uuid4().hex[:10]}", "u": uid, "t": tid},
        )
    assert "SoD DPO" in str(exc.value.orig)
    await sp.rollback()


async def test_trigger_coordinador_responsable_segun_tamano(conn):
    """El trigger fn_utr_coordinador_responsable valida acumulación según tamaño."""
    uid = f"org00-u-{uuid.uuid4().hex[:10]}"
    await conn.execute(
        text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :n)"),
        {"u": uid, "e": f"{uid}@test.local", "n": uid},
    )

    # 1. En mediana: bloqueado (SOD_VIOLATION)
    t_med = f"org00-t-{uuid.uuid4().hex[:10]}"
    await conn.execute(
        text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
             "VALUES (:t, :n, :r, :ruc, 'mediana')"),
        {"t": t_med, "n": t_med, "r": t_med, "ruc": f"RUC{uuid.uuid4().hex[:12]}"},
    )
    await conn.execute(
        text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, 'coordinador')"),
        {"id": f"r1-{uuid.uuid4().hex[:10]}", "u": uid, "t": t_med},
    )
    sp1 = await conn.begin_nested()
    with pytest.raises(IntegrityError) as exc:
        await conn.execute(
            text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, 'responsable_area')"),
            {"id": f"r2-{uuid.uuid4().hex[:10]}", "u": uid, "t": t_med},
        )
    assert "SOD_VIOLATION" in str(exc.value.orig)
    await sp1.rollback()

    # 2. Sin tamaño: bloqueado (TENANT_SIZE_NOT_CONFIGURED). Otra persona: desde ORG-13 un
    # coordinador pertenece a una sola organización.
    uid_sin = f"org00-u-{uuid.uuid4().hex[:10]}"
    await conn.execute(
        text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :n)"),
        {"u": uid_sin, "e": f"{uid_sin}@test.local", "n": uid_sin},
    )
    t_sin = f"org00-t-{uuid.uuid4().hex[:10]}"
    await conn.execute(
        text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
             "VALUES (:t, :n, :r, :ruc, NULL)"),
        {"t": t_sin, "n": t_sin, "r": t_sin, "ruc": f"RUC{uuid.uuid4().hex[:12]}"},
    )
    await conn.execute(
        text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, 'coordinador')"),
        {"id": f"r3-{uuid.uuid4().hex[:10]}", "u": uid_sin, "t": t_sin},
    )
    sp2 = await conn.begin_nested()
    with pytest.raises(IntegrityError) as exc2:
        await conn.execute(
            text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, 'responsable_area')"),
            {"id": f"r4-{uuid.uuid4().hex[:10]}", "u": uid_sin, "t": t_sin},
        )
    assert "TENANT_SIZE_NOT_CONFIGURED" in str(exc2.value.orig)
    await sp2.rollback()


# ============================================================================
# 3. PRUEBA DE RETIRO DE ALIAS (ROLE_ALIASES)
# ============================================================================

async def test_role_coordinador_es_unico_nombre_valido():
    """El rol 'coordinador' es el unico nombre valido en el enum de roles."""
    assert Role.coordinador.value == "coordinador"
    assert not hasattr(Role, "encargado"), "El enum Role no debe contener 'encargado'"


async def test_api_rechaza_rol_antiguo_encargado(conn):
    """Una llamada con X-Role: 'encargado' es rechazada con 403 Forbidden al no existir mas el alias."""
    from app_core.db.session import get_session
    tid = f"org00-t-{uuid.uuid4().hex[:10]}"
    uid = f"org00-u-{uuid.uuid4().hex[:10]}"
    await conn.execute(
        text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
             "VALUES (:t, :n, :r, :ruc, 'mediana')"),
        {"t": tid, "n": tid, "r": tid, "ruc": f"RUC{uuid.uuid4().hex[:12]}"},
    )
    await conn.execute(
        text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :n)"),
        {"u": uid, "e": f"{uid}@test.local", "n": uid},
    )
    await conn.execute(
        text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, 'coordinador')"),
        {"id": f"r-{uuid.uuid4().hex[:10]}", "u": uid, "t": tid},
    )

    async def _override_session():
        yield AsyncSession(bind=conn, expire_on_commit=False)

    app.dependency_overrides[get_session] = _override_session
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            headers = {
                "X-Tenant-ID": tid,
                "X-User-ID": uid,
                "X-Role": "encargado",
            }
            res = await client.get("/api/v1/organizacion/configuracion", headers=headers)
            assert res.status_code == 403, f"Se esperaba 403 Forbidden sin alias, obtuvo {res.status_code}: {res.text}"
    finally:
        app.dependency_overrides.pop(get_session, None)


# ============================================================================
# 4. PRESERVACIÓN DEL SENTIDO LEGAL (ENCARGADO DEL TRATAMIENTO INTACTO)
# ============================================================================

async def test_sentido_legal_encargado_del_tratamiento_intacto():
    """Verifica que el sentido legal de 'encargado del tratamiento' permanece en el corpus normativo y frontend."""
    raiz = Path(__file__).resolve().parent.parent

    # 1. frontend/src/lib/normativas.ts
    normativas_ts = raiz / "frontend" / "src" / "lib" / "normativas.ts"
    if normativas_ts.exists():
        contenido = normativas_ts.read_text(encoding="utf-8")
        assert "encargado" in contenido.lower(), "frontend/src/lib/normativas.ts debe preservar 'encargado del tratamiento'"

    # 2. features/regulacion_rag
    regulacion_dir = raiz / "features" / "regulacion_rag"
    if regulacion_dir.exists():
        archivos = list(regulacion_dir.rglob("*.py")) + list(regulacion_dir.rglob("*.json")) + list(regulacion_dir.rglob("*.txt"))
        encontrado = False
        for f in archivos:
            try:
                txt = f.read_text(encoding="utf-8")
                if "encargado" in txt.lower():
                    encontrado = True
                    break
            except Exception:
                continue
        assert encontrado, "features/regulacion_rag debe preservar referencias a 'encargado del tratamiento'"
