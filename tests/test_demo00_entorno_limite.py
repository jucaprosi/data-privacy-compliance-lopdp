# -*- coding: utf-8 -*-
# ¤demo
# ¤seguridad
"""DEMO-00: `GET /api/v1/entorno` es pública, pero no ilimitada.

La consulta anónima (antes del login, sin token) cae en `entorno_publico` (SEC-21, ámbito IP) y se cuenta por IP. Se usa el router real de EP-01, el middleware real y su resolutor
OIDC: sin token, la identidad queda vacía. El límite se baja con `LIMITE_ENTORNO_PUBLICO`.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.middleware.limite_peticiones import LimitePeticionesMiddleware
from api.routers.entorno import router as router_entorno
from app_core.limites import LimitadorMemoria, cargar_politicas, politicas_de_ruta

LIMITE = 3
RUTA = "/api/v1/entorno"


@pytest.fixture
def cliente(monkeypatch):
    monkeypatch.setenv("LIMITE_ENTORNO_PUBLICO", str(LIMITE))  # SEC-21: la ruta ya no cae en api_general
    monkeypatch.setenv("PROXIES_CONFIABLES", "1")  # SEC-21: sin esto X-Forwarded-For se ignora (n=0)
    app = FastAPI()
    app.include_router(router_entorno, prefix="/api/v1")
    app.add_middleware(LimitePeticionesMiddleware, limitador=LimitadorMemoria(), politicas=cargar_politicas())
    return TestClient(app)


def _desde(ip: str) -> dict[str, str]:
    return {"X-Forwarded-For": ip}


def test_entorno_cae_en_la_politica_publica_por_ip():
    assert politicas_de_ruta(RUTA, "GET") == ("entorno_publico",)


def test_entorno_anonima_429_al_pasar_el_limite_desde_la_misma_ip(cliente):
    for _ in range(LIMITE):
        r = cliente.get(RUTA, headers=_desde("198.51.100.7"))
        assert r.status_code == 200
        assert "authorization" not in {k.lower() for k in r.request.headers}
    r = cliente.get(RUTA, headers=_desde("198.51.100.7"))
    assert r.status_code == 429
    assert int(r.headers["Retry-After"]) >= 1
    assert r.json()["codigo"] == "LIMITE_PETICIONES"


def test_el_limite_es_por_ip_y_no_global(cliente):
    """Sin el respaldo a IP, todos los anónimos compartirían un contador y esto fallaría."""
    for _ in range(LIMITE + 1):
        cliente.get(RUTA, headers=_desde("198.51.100.7"))
    assert cliente.get(RUTA, headers=_desde("198.51.100.7")).status_code == 429
    assert cliente.get(RUTA, headers=_desde("203.0.113.9")).status_code == 200
