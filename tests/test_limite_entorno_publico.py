# -*- coding: utf-8 -*-
# ¤seguridad
"""SEC-21 · Límite por IP en la ruta pública `GET /api/v1/entorno` y saltos de proxy.

Sin base de datos: limitador en memoria y el router real de EP-01. Solo IPs de documentación (RFC 5737 y
RFC 3849) y valores simulados; nunca `AUTH_MODE=headers`.

Mutaciones documentadas (ficha SEC-21); cada una pone en rojo la prueba que se indica:
- M1 quitar `PREFIJOS_PUBLICOS_IP` de `politicas_de_ruta` ⟹ test_ruta_entorno_publica.
- M2 cambiar el ámbito de `entorno_publico` a «usuario» ⟹ test_la_peticion_61_da_429_y_otra_ip_sigue_en_200.
- M3 contar desde la izquierda (E[0]) ⟹ test_n1_toma_la_ultima_entrada, test_n2_toma_la_entrada_del_cliente.
- M4 usar `scope["client"]` o E[0] de respaldo con n ≥ 1 ⟹ test_con_menos_entradas_que_n_o_entrada_invalida_clave_comun.
- M5 quedarse solo con la última cabecera X-Forwarded-For ⟹ test_varias_cabeceras_se_unen_en_orden.
- M6 aceptar un n inválido ⟹ test_n_invalido_falla_cerrado.
- M7 leer X-Forwarded-For con n = 0 ⟹ test_n0_ignora_xff_y_comparte_cubeta_por_conexion.
- M8 devolver «desconocida» siempre con n = 0 ⟹ test_n0_sin_xff_cada_conexion_su_cubeta.
- M9 no agrupar IPv6 por /64 ⟹ test_ipv6_se_agrupa_por_64.
- M10 no exigir la variable en la nube ⟹ test_en_la_nube_sin_la_variable_falla.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.middleware.limite_peticiones import (
    CLAVE_COMUN, LimitePeticionesMiddleware, ip_cliente, proxies_confiables,
)
from api.routers.entorno import router as router_entorno
from app_core.limites import LimitadorMemoria, cargar_politicas, politicas_de_ruta

RUTA = "/api/v1/entorno"


def _scope(*xff: str, cliente="10.0.0.1"):
    cabeceras = [(b"x-forwarded-for", v.encode()) for v in xff]
    return {"headers": cabeceras, "client": (cliente, 40000) if cliente else None}


def _cliente(proxies: int, entorno: dict | None = None) -> TestClient:
    app = FastAPI()
    app.include_router(router_entorno, prefix="/api/v1")
    politicas = cargar_politicas(entorno or {})
    app.add_middleware(LimitePeticionesMiddleware, limitador=LimitadorMemoria(), politicas=politicas, proxies=proxies)
    return TestClient(app)


def _desde(xff: str) -> dict[str, str]:
    return {"X-Forwarded-For": xff}


# ----------------------------------------------------------------------------- política y ruta

@pytest.mark.parametrize("ruta", [RUTA, RUTA + "/"])
def test_ruta_entorno_publica(ruta):
    assert politicas_de_ruta(ruta, "GET") == ("entorno_publico",)


def test_la_politica_es_por_ip_y_de_60_por_minuto():
    p = cargar_politicas({})["entorno_publico"]
    assert (p.ambito, p.limite, p.ventana_segundos) == ("ip", 60, 60)


def test_la_peticion_61_da_429_y_otra_ip_sigue_en_200():
    cliente = _cliente(1)
    for _ in range(60):
        assert cliente.get(RUTA, headers=_desde("198.51.100.7")).status_code == 200
    r = cliente.get(RUTA, headers=_desde("198.51.100.7"))
    assert r.status_code == 429 and r.json()["politica"] == "entorno_publico"
    assert cliente.get(RUTA, headers=_desde("203.0.113.9")).status_code == 200


def test_el_tope_se_cambia_con_la_variable():
    cliente = _cliente(1, {"LIMITE_ENTORNO_PUBLICO": "5"})
    assert [cliente.get(RUTA, headers=_desde("198.51.100.7")).status_code for _ in range(6)] == [200] * 5 + [429]


def test_health_sigue_libre():
    assert politicas_de_ruta("/api/v1/health", "GET") == ()
    assert politicas_de_ruta("/health", "GET") == ()


# ----------------------------------------------------------------------------- saltos de proxy

def test_n1_toma_la_ultima_entrada():
    assert ip_cliente(_scope("198.51.100.4"), 1) == "198.51.100.4"
    assert ip_cliente(_scope("192.0.2.66, 198.51.100.4"), 1) == "198.51.100.4"  # lo que antepone el cliente no cuenta


def test_n2_toma_la_entrada_del_cliente():
    assert ip_cliente(_scope("192.0.2.66, 198.51.100.4, 203.0.113.1"), 2) == "198.51.100.4"


def test_n2_clientes_distintos_cubetas_distintas_y_mismo_cliente_con_entradas_falsas_comparte():
    cliente = _cliente(2)
    for falsa in range(60):
        r = cliente.get(RUTA, headers=_desde(f"192.0.2.{falsa + 1}, 198.51.100.4, 203.0.113.1"))
        assert r.status_code == 200
    r = cliente.get(RUTA, headers=_desde("192.0.2.200, 198.51.100.4, 203.0.113.1"))
    assert r.status_code == 429, "el mismo cliente con otra entrada falsa sigue en su cubeta"
    assert cliente.get(RUTA, headers=_desde("192.0.2.1, 198.51.100.5, 203.0.113.1")).status_code == 200


def test_n0_ignora_xff_y_comparte_cubeta_por_conexion():
    cliente = _cliente(0)
    for i in range(60):
        assert cliente.get(RUTA, headers=_desde(f"192.0.2.{i + 1}")).status_code == 200
    assert cliente.get(RUTA, headers=_desde("192.0.2.222")).status_code == 429


def test_n0_sin_xff_cada_conexion_su_cubeta():
    assert ip_cliente(_scope(cliente="10.0.0.1"), 0) == "10.0.0.1"
    assert ip_cliente(_scope(cliente="10.0.0.2"), 0) == "10.0.0.2"
    assert ip_cliente(_scope("192.0.2.9", cliente="10.0.0.1"), 0) == "10.0.0.1"
    assert ip_cliente(_scope(cliente=None), 0) == CLAVE_COMUN


@pytest.mark.parametrize("cabecera,n", [
    ("", 2), ("198.51.100.4", 2), ("192.0.2.1, ,", 2),  # menos entradas que n
    ("no-es-una-ip", 1), ("192.0.2.1, no-es-una-ip", 1), ("192.0.2.1,%00", 1),  # la entrada elegida no es una IP
])
def test_con_menos_entradas_que_n_o_entrada_invalida_clave_comun(cabecera, n):
    assert ip_cliente(_scope(cabecera, cliente="10.0.0.1"), n) == CLAVE_COMUN


def test_con_n_mayor_que_cero_sin_la_cabecera_nunca_se_usa_scope_client():
    assert ip_cliente(_scope(cliente="10.0.0.1"), 1) == CLAVE_COMUN


def test_varias_cabeceras_se_unen_en_orden():
    assert ip_cliente(_scope("192.0.2.66", "198.51.100.4"), 1) == "198.51.100.4"
    assert ip_cliente(_scope("192.0.2.66", "198.51.100.4, 203.0.113.1"), 2) == "198.51.100.4"
    assert ip_cliente(_scope("198.51.100.4", "203.0.113.1"), 2) == "198.51.100.4", "cada proxy pudo añadir su cabecera"


def test_ipv6_se_agrupa_por_64():
    uno = ip_cliente(_scope("2001:db8::1"), 1)
    assert uno == ip_cliente(_scope("2001:db8::2"), 1)
    assert uno != ip_cliente(_scope("2001:db9::1"), 1)
    assert ip_cliente(_scope("2001:db8:0:1::1"), 1) != uno, "otro /64, otra cubeta"
    assert ip_cliente(_scope("::ffff:198.51.100.4"), 1) == "198.51.100.4"


# ----------------------------------------------------------------------------- configuración

@pytest.mark.parametrize("valor", ["abc", "-1", "1.5", "٣", "1 2", "0x1", "99999999999999999999,1"])
def test_n_invalido_falla_cerrado(valor):
    for entorno in ({"PROXIES_CONFIABLES": valor}, {"PROXIES_CONFIABLES": valor, "K_SERVICE": "servicio-ficticio"}):
        with pytest.raises(RuntimeError, match="SEC-21") as error:
            proxies_confiables(entorno)
        assert valor not in str(error.value), "el error no repite el valor"


@pytest.mark.parametrize("valor,esperado", [("0", 0), ("1", 1), (" 2 ", 2), ("10", 10)])
def test_n_valido(valor, esperado):
    assert proxies_confiables({"PROXIES_CONFIABLES": valor}) == esperado
    assert proxies_confiables({"PROXIES_CONFIABLES": valor, "K_SERVICE": "servicio-ficticio"}) == esperado


def test_fuera_de_la_nube_sin_la_variable_vale_0():
    assert proxies_confiables({}) == 0
    assert proxies_confiables({"PROXIES_CONFIABLES": ""}) == 0


@pytest.mark.parametrize("entorno", [{"K_SERVICE": "servicio-ficticio"}, {"K_SERVICE": "", "PROXIES_CONFIABLES": "  "}])
def test_en_la_nube_sin_la_variable_falla(entorno):
    with pytest.raises(RuntimeError, match="SEC-21"):
        proxies_confiables(entorno)


def test_el_middleware_no_arranca_en_la_nube_sin_la_variable(monkeypatch):
    monkeypatch.setenv("K_SERVICE", "servicio-ficticio")
    monkeypatch.delenv("PROXIES_CONFIABLES", raising=False)
    with pytest.raises(RuntimeError, match="SEC-21"):
        LimitePeticionesMiddleware(app=None, limitador=LimitadorMemoria())
    monkeypatch.setenv("PROXIES_CONFIABLES", "1")
    assert LimitePeticionesMiddleware(app=None, limitador=LimitadorMemoria()).proxies == 1
