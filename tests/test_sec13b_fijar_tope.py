# ¤seguridad-tenant
"""SEC-13b: fijar_tope es el alta idempotente del tope de IA, contra PostgreSQL de pruebas, como lopdp_app.

Mutación documentada: si `_FIJAR` pierde su `ON CONFLICT`, la segunda llamada de
`test_dos_llamadas_dejan_una_fila` choca con la clave primaria y la prueba queda en rojo.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app_core.limites import tope_organizacion as tope_org
from app_core.limites.tope_organizacion import fijar_tope


async def _como_app(session, tenant: str) -> None:
    if not (await session.execute(text("SELECT 1 FROM pg_roles WHERE rolname = 'lopdp_app'"))).first():
        pytest.skip("rol lopdp_app no existe en la base de prueba")
    await session.execute(text("SET LOCAL ROLE lopdp_app"))
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant})


async def _crear_tenant(fabrica) -> str:
    tid = f"t-sec13b-{uuid.uuid4().hex[:10]}"
    async with fabrica() as s:
        await s.execute(text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, activo) "
                             "VALUES (:t, 'FICTICIO SEC-13b', 'FICTICIO SEC-13b', :ruc, TRUE)"),
                        {"t": tid, "ruc": str(uuid.uuid4().int)[:13]})
        await s.commit()
    return tid


async def _filas(fabrica, como: str, de: str) -> list[tuple]:
    async with fabrica() as s:
        await _como_app(s, como)
        r = await s.execute(text("SELECT tope, usadas FROM ia_tope_organizacion WHERE tenant_id = :t"), {"t": de})
        return [tuple(f) for f in r.all()]


async def _fijar(fabrica, tid: str, tope: int) -> None:
    async with fabrica() as s:
        await _como_app(s, tid)
        await fijar_tope(s, tid, tope)
        await s.commit()


@pytest.mark.asyncio
async def test_dos_llamadas_dejan_una_fila(db_engine):
    fabrica = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    tid = await _crear_tenant(fabrica)
    await _fijar(fabrica, tid, 5)
    await _fijar(fabrica, tid, 5)
    assert await _filas(fabrica, tid, tid) == [(5, 0)]


@pytest.mark.asyncio
async def test_el_tope_se_actualiza_sin_tocar_usadas(db_engine):
    fabrica = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    tid = await _crear_tenant(fabrica)
    await _fijar(fabrica, tid, 5)
    async with fabrica() as s:
        await _como_app(s, tid)
        await tope_org.consumir_generacion(s, tid)
        await s.commit()
    await _fijar(fabrica, tid, 9)
    assert await _filas(fabrica, tid, tid) == [(9, 1)]


@pytest.mark.asyncio
async def test_desde_otro_tenant_no_se_ve(db_engine):
    fabrica = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    tid, otro = await _crear_tenant(fabrica), await _crear_tenant(fabrica)
    await _fijar(fabrica, tid, 5)
    assert await _filas(fabrica, otro, tid) == []


def test_la_sentencia_es_un_upsert():
    sql = str(tope_org._FIJAR).upper()
    assert "ON CONFLICT (TENANT_ID) DO UPDATE SET TOPE" in sql
