# ¤seguridad-tenant ¤copiloto-ia
"""SEC-13a: tope total de generaciones de IA por organización, contra PostgreSQL de pruebas."""
from __future__ import annotations

import asyncio
import os
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import api.middleware.limite_peticiones as mw
from app_core.errors import CATALOGO_ERRORES, ErrorNegocio
from app_core.limites import LimitadorMemoria, cargar_politicas
from app_core.limites.tope_organizacion import consumir_generacion

URL = os.environ.get("DATABASE_URL", "")
pytestmark = pytest.mark.skipif(not URL.startswith("postgresql"), reason="sin PostgreSQL de pruebas")


def _motor():
    return create_async_engine(URL.replace("postgresql://", "postgresql+psycopg://", 1), poolclass=NullPool)


async def _contexto(session, tenant: str) -> None:
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :t, true), set_config('app.current_user_id', 'u-prueba', true)"),
        {"t": tenant},
    )


def _sembrar(tope: int | None, con_fila: bool = True) -> str:
    tenant = f"t-sec13a-{uuid.uuid4().hex[:10]}"

    async def correr():
        motor = _motor()
        try:
            async with async_sessionmaker(motor, class_=AsyncSession)() as s:
                await s.execute(
                    text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                         "VALUES (:t, :t, :t, :r)"),
                    {"t": tenant, "r": f"RUC{uuid.uuid4().hex[:12]}"},
                )
                if con_fila:
                    await _contexto(s, tenant)
                    await s.execute(
                        text("INSERT INTO ia_tope_organizacion (tenant_id, tope) VALUES (:t, :tope)"),
                        {"t": tenant, "tope": tope},
                    )
                await s.commit()
        finally:
            await motor.dispose()

    asyncio.run(correr())
    return tenant


async def _consumir(tenant: str) -> bool:
    motor = _motor()
    try:
        async with async_sessionmaker(motor, class_=AsyncSession)() as s:
            await _contexto(s, tenant)
            try:
                await consumir_generacion(s, tenant)
            except ErrorNegocio as exc:
                assert exc.code == "IA_TOPE_ORGANIZACION"
                return False
            await s.commit()
            return True
    finally:
        await motor.dispose()


async def _consumir_por_identidad(identidad) -> None:  # noqa: ANN001
    motor = _motor()
    try:
        async with async_sessionmaker(motor, class_=AsyncSession)() as s:
            await _contexto(s, identidad.organizacion_id)
            await consumir_generacion(s, identidad.organizacion_id)
            await s.commit()
    finally:
        await motor.dispose()


async def _resolver(scope, es_ia):  # noqa: ANN001
    h = {k.decode(): v.decode() for k, v in scope.get("headers") or []}
    return mw.Identidad(h.get("x-prueba-usuario"), h.get("x-prueba-org"))


def _cliente(monkeypatch):  # noqa: ANN001
    monkeypatch.setattr(mw, "consumir_tope_ia", _consumir_por_identidad)
    app = FastAPI()
    llamadas = []

    @app.post("/api/v1/ai/diagnosticar")
    def copiloto():
        llamadas.append(1)
        return {"ok": True}

    app.add_middleware(
        mw.LimitePeticionesMiddleware,
        limitador=LimitadorMemoria(),
        resolver=_resolver,
        politicas=cargar_politicas({}),
    )
    return TestClient(app), llamadas


def test_tope_5_la_sexta_responde_429(monkeypatch):
    tenant = _sembrar(5)
    cliente, llamadas = _cliente(monkeypatch)
    h = {"x-prueba-usuario": "u1", "x-prueba-org": tenant}
    for _ in range(5):
        assert cliente.post("/api/v1/ai/diagnosticar", headers=h).status_code == 200
    r = cliente.post("/api/v1/ai/diagnosticar", headers=h)
    assert r.status_code == 429
    assert r.json() == {
        "codigo": "IA_TOPE_ORGANIZACION",
        "mensaje": "Tu organización alcanzó su límite de generaciones con IA",
    }
    assert len(llamadas) == 5


def test_sin_tope_no_se_niega_nada():
    nulo = _sembrar(None)
    sin_fila = _sembrar(None, con_fila=False)

    async def correr():
        for _ in range(8):
            assert await _consumir(nulo)
            assert await _consumir(sin_fila)

    asyncio.run(correr())


def test_consumo_aislado_por_organizacion():
    a, b = _sembrar(1), _sembrar(1)

    async def correr():
        assert await _consumir(a)
        assert not await _consumir(a)
        assert await _consumir(b)

    asyncio.run(correr())


def test_concurrencia_solo_una_pasa():
    tenant = _sembrar(3)

    async def correr():
        assert await _consumir(tenant)
        assert await _consumir(tenant)  # usadas = tope - 1
        resultados = await asyncio.gather(_consumir(tenant), _consumir(tenant))
        assert sorted(resultados) == [False, True]

    asyncio.run(correr())


def test_ventanas_de_sec13_siguen_igual(monkeypatch):
    tenant = _sembrar(None)
    cliente, _ = _cliente(monkeypatch)
    h = {"x-prueba-usuario": "u-vent", "x-prueba-org": tenant}
    for _ in range(30):
        assert cliente.post("/api/v1/ai/diagnosticar", headers=h).status_code == 200
    r = cliente.post("/api/v1/ai/diagnosticar", headers=h)
    assert r.status_code == 429 and r.json()["politica"] == "ia_usuario"


def test_tope_no_disponible_cierra_la_ia(monkeypatch):
    async def caido(identidad):  # noqa: ANN001
        raise OSError("sin conexión")

    cliente, llamadas = _cliente(monkeypatch)
    monkeypatch.setattr(mw, "consumir_tope_ia", caido)
    r = cliente.post("/api/v1/ai/diagnosticar", headers={"x-prueba-usuario": "u", "x-prueba-org": "t-x"})
    assert r.status_code == 503 and r.json() == {"codigo": "LIMITE_NO_DISPONIBLE"}
    assert llamadas == []


def test_consumir_tope_ia_real_contra_postgres():
    """La versión real (async_session_factory + fijar_contexto_rls), sin sustituir."""
    from app_core.db.session import engine

    tenant = _sembrar(1)
    identidad = mw.Identidad("u-real", tenant)

    async def correr():
        try:
            await mw.consumir_tope_ia(identidad)
            with pytest.raises(ErrorNegocio) as exc:
                await mw.consumir_tope_ia(identidad)
            assert exc.value.code == "IA_TOPE_ORGANIZACION"
        finally:
            await engine.dispose()

    asyncio.run(correr())


def test_codigo_en_catalogo():
    assert CATALOGO_ERRORES["IA_TOPE_ORGANIZACION"].status_code == 429
