"""Fixtures compartidos. Fuerza tests contra el branch test de Neon.

IMPORTANTE: en Windows, psycopg async requiere SelectorEventLoop,
no ProactorEventLoop. La policy se fija AL INICIO, antes de cualquier
import que toque asyncio.
"""
import asyncio
import os
import sys
import uuid
from pathlib import Path

# ---- FIX Windows + psycopg async ----
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH, override=False)

# Forzar DATABASE_URL al branch test (session.py lo lee al importar)
if "TEST_DATABASE_URL" in os.environ:
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest_asyncio.fixture
async def db_engine():
    """Engine async apuntando al branch test."""
    url = os.environ["TEST_DATABASE_URL"]
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_async_engine(url, pool_pre_ping=True)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Sesión async con cleanup automático."""
    factory = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def seed_tenants(db_session):
    """Crea 2 tenants + 2 users + roles. Cleanup al final."""
    ta = f"test-ta-{uuid.uuid4().hex[:8]}"
    tb = f"test-tb-{uuid.uuid4().hex[:8]}"
    ua = f"test-ua-{uuid.uuid4().hex[:8]}"
    ub = f"test-ub-{uuid.uuid4().hex[:8]}"

    for tid in (ta, tb):
        await db_session.execute(
            text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                 "VALUES (:id, :n, :r, :ruc)"),
            {"id": tid, "n": f"Test {tid}", "r": f"Test {tid} SA", "ruc": f"RUC{tid[:20]}"},
        )

    for uid in (ua, ub):
        await db_session.execute(
            text("INSERT INTO users (id, email, nombre) VALUES (:id, :e, :n)"),
            {"id": uid, "e": f"{uid}@test.local", "n": f"User {uid}"},
        )

    await db_session.execute(
        text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) "
             "VALUES (:id, :uid, :tid, 'implementador')"),
        {"id": f"role-a-{uuid.uuid4().hex[:8]}", "uid": ua, "tid": ta},
    )
    await db_session.execute(
        text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) "
             "VALUES (:id, :uid, :tid, 'implementador')"),
        {"id": f"role-b-{uuid.uuid4().hex[:8]}", "uid": ub, "tid": tb},
    )
    await db_session.commit()

    yield {"tenant_a": ta, "tenant_b": tb, "user_a": ua, "user_b": ub}

    # Cleanup
    try:
        await db_session.execute(
            text("DELETE FROM task_audit_log WHERE tenant_id IN (:a, :b)"),
            {"a": ta, "b": tb},
        )
        await db_session.execute(
            text("DELETE FROM task_evidence WHERE tenant_id IN (:a, :b)"),
            {"a": ta, "b": tb},
        )
        await db_session.execute(
            text("DELETE FROM task_dependencies WHERE task_id IN "
                 "(SELECT id FROM roadmap_tasks WHERE tenant_id IN (:a, :b))"),
            {"a": ta, "b": tb},
        )
        await db_session.execute(
            text("DELETE FROM roadmap_tasks WHERE tenant_id IN (:a, :b)"),
            {"a": ta, "b": tb},
        )
        await db_session.execute(
            text("DELETE FROM roadmap_waves WHERE tenant_id IN (:a, :b)"),
            {"a": ta, "b": tb},
        )
        await db_session.execute(
            text("DELETE FROM roadmaps WHERE tenant_id IN (:a, :b)"),
            {"a": ta, "b": tb},
        )
        await db_session.execute(
            text("DELETE FROM user_tenant_roles WHERE tenant_id IN (:a, :b)"),
            {"a": ta, "b": tb},
        )
        await db_session.execute(
            text("DELETE FROM users WHERE id IN (:a, :b)"),
            {"a": ua, "b": ub},
        )
        await db_session.execute(
            text("DELETE FROM tenants WHERE id IN (:a, :b)"),
            {"a": ta, "b": tb},
        )
        await db_session.commit()
    except Exception:
        await db_session.rollback()
