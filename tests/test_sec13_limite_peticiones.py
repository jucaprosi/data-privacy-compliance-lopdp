# ¤seguridad ¤seguridad-tenant ¤copiloto-ia
"""SEC-13: límite de peticiones por IP, usuario y organización, con tope de gasto de IA.

App mínima con el middleware, el limitador en memoria y un resolutor de identidad de prueba
(sin AUTH_MODE=headers: la identidad simulada entra por el resolutor inyectado).
"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.middleware.limite_peticiones import Identidad, LimitePeticionesMiddleware, ip_cliente
from app_core.errors import CATALOGO_ERRORES
from app_core.limites import (
    LimitadorMemoria,
    LimitadorPostgres,
    LimiteNoDisponible,
    cargar_politicas,
    clave_limite,
    politicas_de_ruta,
)


async def _resolver_prueba(scope, es_ia):  # noqa: ANN001
    cabeceras = {k.decode(): v.decode() for k, v in scope.get("headers") or []}
    return Identidad(cabeceras.get("x-prueba-usuario"), cabeceras.get("x-prueba-org"))


class _Modelo:
    def __init__(self) -> None:
        self.llamadas = 0


def _app(limitador=None, politicas=None):  # noqa: ANN001
    modelo = _Modelo()
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/api/v1/health")
    def health_api():
        return {"ok": True}

    @app.post("/api/v1/auth/sesion")
    def iniciar():
        return {"ok": True}

    @app.post("/api/v1/ai/diagnosticar")
    def copiloto():
        modelo.llamadas += 1
        return {"ok": True}

    @app.get("/api/v1/rat")
    def general():
        return {"ok": True}

    @app.post("/api/v1/roadmaps/tasks/t1/evidence/upload-url")
    def url():
        return {"ok": True}

    limitador = limitador or LimitadorMemoria()
    app.add_middleware(
        LimitePeticionesMiddleware,
        limitador=limitador,
        resolver=_resolver_prueba,
        politicas=politicas or cargar_politicas({}),
    )
    return TestClient(app), modelo, limitador


def _u(usuario: str, org: str | None = None) -> dict:
    h = {"x-prueba-usuario": usuario}
    if org:
        h["x-prueba-org"] = org
    return h


def test_inicio_sesion_429_con_retry_after():
    cliente, _, _ = _app()
    for _ in range(10):
        assert cliente.post("/api/v1/auth/sesion").status_code == 200
    r = cliente.post("/api/v1/auth/sesion")
    assert r.status_code == 429
    assert int(r.headers["retry-after"]) > 0
    assert r.json() == {"codigo": "LIMITE_PETICIONES", "politica": "inicio_sesion"}


def test_ia_rechazada_antes_de_llamar_al_modelo():
    cliente, modelo, _ = _app()
    for _ in range(30):
        assert cliente.post("/api/v1/ai/diagnosticar", headers=_u("u1", "orgA")).status_code == 200
    llamadas = modelo.llamadas
    r = cliente.post("/api/v1/ai/diagnosticar", headers=_u("u1", "orgA"))
    assert r.status_code == 429
    assert r.json()["politica"] == "ia_usuario"
    assert modelo.llamadas == llamadas == 30


def test_cupo_aislado_por_organizacion():
    politicas = cargar_politicas({"LIMITE_IA_ORGANIZACION": "3"})
    cliente, _, _ = _app(politicas=politicas)
    for i in range(3):
        assert cliente.post("/api/v1/ai/diagnosticar", headers=_u(f"a{i}", "orgA")).status_code == 200
    r = cliente.post("/api/v1/ai/diagnosticar", headers=_u("a9", "orgA"))
    assert r.status_code == 429 and r.json()["politica"] == "ia_organizacion"
    assert cliente.post("/api/v1/ai/diagnosticar", headers=_u("b1", "orgB")).status_code == 200


def test_fallo_seguro_asimetrico(caplog):
    limitador = LimitadorMemoria()
    limitador.caido = True
    cliente, modelo, _ = _app(limitador=limitador)
    with caplog.at_level(logging.WARNING, logger="jubys_lopdp_json_logger"):
        ia = cliente.post("/api/v1/ai/diagnosticar", headers=_u("u1", "orgA"))
        general = cliente.get("/api/v1/rat", headers=_u("u1"))
    assert ia.status_code == 503 and ia.json() == {"codigo": "LIMITE_NO_DISPONIBLE"}
    assert modelo.llamadas == 0
    assert general.status_code == 200
    assert any("sin límite" in r.getMessage() for r in caplog.records)


def test_health_fuera_de_politicas():
    politicas = cargar_politicas({"LIMITE_API_GENERAL": "1"})
    cliente, _, _ = _app(politicas=politicas)
    cliente.get("/api/v1/rat", headers=_u("u1"))
    assert cliente.get("/api/v1/rat", headers=_u("u1")).status_code == 429
    for _ in range(5):
        assert cliente.get("/health").status_code == 200
        assert cliente.get("/api/v1/health").status_code == 200


def test_url_firmada_y_api_general_por_usuario():
    politicas = cargar_politicas({"LIMITE_URL_FIRMADA": "2", "LIMITE_API_GENERAL": "2"})
    cliente, _, _ = _app(politicas=politicas)
    ruta = "/api/v1/roadmaps/tasks/t1/evidence/upload-url"
    assert cliente.post(ruta, headers=_u("u1")).status_code == 200
    assert cliente.post(ruta, headers=_u("u1")).status_code == 200
    r = cliente.post(ruta, headers=_u("u1"))
    assert r.status_code == 429 and r.json()["politica"] == "url_firmada"
    assert cliente.post(ruta, headers=_u("u2")).status_code == 200
    assert cliente.get("/api/v1/rat", headers=_u("u1")).status_code == 200


def test_clasificacion_de_rutas():
    assert politicas_de_ruta("/health", "GET") == ()
    assert politicas_de_ruta("/api/v1/health/", "GET") == ()
    assert politicas_de_ruta("/api/v1/auth/sesion", "POST") == ("inicio_sesion",)
    assert politicas_de_ruta("/api/v1/preanalisis/analizar", "POST") == ("ia_usuario", "ia_organizacion")
    assert politicas_de_ruta("/api/v1/roadmaps/generate", "POST") == ("ia_usuario", "ia_organizacion")
    assert politicas_de_ruta("/api/v1/ai/historial", "GET") == ("api_general",)
    assert politicas_de_ruta("/api/v1/biblioteca/plantillas/p/descargar", "POST") == ("url_firmada",)
    assert politicas_de_ruta("/api/v1/rat", "GET") == ("api_general",)


def test_valores_ajustables_por_entorno():
    p = cargar_politicas({"LIMITE_IA_USUARIO": "50", "LIMITE_API_GENERAL": "no"})
    assert p["ia_usuario"].limite == 50
    assert p["api_general"].limite == 300


def test_clave_sin_datos_personales():
    p = cargar_politicas({})["api_general"]
    clave = clave_limite(p, "persona@ejemplo.invalid")
    assert "persona" not in clave and "@" not in clave
    assert clave.startswith("lim:api_general:usuario:")


def test_ventana_deslizante_reinicia_por_tiempo():
    reloj = [1_000_000.0 - (1_000_000 % 60)]
    limitador = LimitadorMemoria(reloj=lambda: reloj[0])
    p = cargar_politicas({"LIMITE_API_GENERAL": "2"})["api_general"]

    async def correr():
        assert (await limitador.consumir(p, "u")).admitido
        assert (await limitador.consumir(p, "u")).admitido
        r = await limitador.consumir(p, "u")
        assert not r.admitido and r.retry_after == 60
        reloj[0] += 59  # siguiente ventana pesa casi toda la anterior: sigue rechazando
        assert not (await limitador.consumir(p, "u")).admitido
        reloj[0] += 180  # ventanas vencidas: la fila se reinicia
        assert (await limitador.consumir(p, "u")).admitido

    asyncio.run(correr())


def test_ip_tras_balanceador():
    scope = {"headers": [(b"x-forwarded-for", b"1.1.1.1, 203.0.113.7")], "client": ("10.0.0.1", 1)}
    assert ip_cliente(scope, 1) == "203.0.113.7"  # SEC-21: n=1, Cloud Run directo
    assert ip_cliente({"headers": [], "client": ("10.0.0.1", 1)}, 0) == "10.0.0.1"  # SEC-21: n=0, sin proxy


def test_codigos_en_catalogo():
    assert CATALOGO_ERRORES["LIMITE_PETICIONES"].status_code == 429
    assert CATALOGO_ERRORES["LIMITE_NO_DISPONIBLE"].status_code == 503


def test_postgres_caido_es_no_disponible():
    def fabrica():
        raise OSError("sin conexión")

    p = cargar_politicas({})["ia_usuario"]
    with pytest.raises(LimiteNoDisponible):
        asyncio.run(LimitadorPostgres(session_factory=fabrica).consumir(p, "u"))


def test_postgres_upsert_reinicia_sin_delete():
    """Contra la base de pruebas migrada: UPSERT atómico y reinicio de la ventana vencida."""
    url = os.environ.get("DATABASE_URL", "")
    if not url.startswith("postgresql"):
        pytest.skip("sin PostgreSQL de pruebas")
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool

    async def correr():
        motor = create_async_engine(url.replace("postgresql://", "postgresql+psycopg://", 1), poolclass=NullPool)
        try:
            fabrica = async_sessionmaker(motor, class_=AsyncSession, expire_on_commit=False)
            reloj = [2_000_000.0 - (2_000_000 % 60)]
            limitador = LimitadorPostgres(session_factory=fabrica, reloj=lambda: reloj[0])
            p = cargar_politicas({"LIMITE_API_GENERAL": "2"})["api_general"]
            ident = f"u-{uuid.uuid4()}"
            assert (await limitador.consumir(p, ident)).admitido
            assert (await limitador.consumir(p, ident)).admitido
            assert not (await limitador.consumir(p, ident)).admitido
            reloj[0] += 600
            assert (await limitador.consumir(p, ident)).admitido
            async with fabrica() as s:
                filas = (await s.execute(
                    text("SELECT contador, previo FROM ventana_peticiones WHERE clave = :c"),
                    {"c": clave_limite(p, ident)},
                )).all()
            assert filas == [(1, 0)]
        finally:
            await motor.dispose()

    asyncio.run(correr())
