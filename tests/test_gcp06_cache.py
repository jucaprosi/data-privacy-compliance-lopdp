"""GCP-06 · Cloud CDN solo para activos estáticos y caché de lectura por tenant (INV_EDGE_CACHE_PUBLIC_STATIC_ONLY).

`¤cloud-run-perf` `¤seguridad-tenant` `¤arbitro`
Garantía de borde: /api/v1/* fuera del CDN (cloud_cdn.yaml). La cabecera no-store del backend en las
rutas reales queda pendiente de otra ficha: aquí solo se prueba el contrato del helper.
"""
import uuid
from pathlib import Path

import pytest

from app_core.cache import (
    CABECERA_ESTATICOS, CABECERA_NO_STORE, AlmacenMemoria, CacheLectura, ClaveCache,
    cabeceras_datos_de_organizacion,
)
from tests._lector_yaml import leer_yaml

CDN = Path(__file__).resolve().parents[1] / "governance/operaciones/cloud_cdn.yaml"
T1, T2 = uuid.uuid4(), uuid.uuid4()


def _manifiesto() -> dict:
    return leer_yaml(CDN.read_text(encoding="utf-8"))


def test_cdn_solo_activos_estaticos():
    m = _manifiesto()
    assert m["cdn"] is True and m["rutas_cacheables"]
    assert all(r.startswith("/_next/static/") for r in m["rutas_cacheables"])
    assert m["cabecera_cache_control"] == CABECERA_ESTATICOS["Cache-Control"]
    assert "evydentia-backend-bs" in m["servicios_sin_cdn"] and m["servicio_backend"] != "evydentia-backend-bs"


def test_datos_de_organizacion_no_cacheables():
    assert not any(r.startswith("/api") for r in _manifiesto()["rutas_cacheables"])
    assert cabeceras_datos_de_organizacion() == {"Cache-Control": "no-store"} == CABECERA_NO_STORE
    cabeceras_datos_de_organizacion()["Cache-Control"] = "x"  # copia: no contamina la constante
    assert CABECERA_NO_STORE["Cache-Control"] == "no-store"


def test_cache_lectura_aislada_por_tenant():
    cache = CacheLectura(AlmacenMemoria())
    cache.guardar(ClaveCache(T1, "catalogo", "v1"), "datos-de-1")
    cache.guardar(ClaveCache(T2, "catalogo", "v1"), "datos-de-2")
    assert cache.obtener(ClaveCache(T1, "catalogo", "v1")) == "datos-de-1"
    assert cache.obtener(ClaveCache(T2, "catalogo", "v1")) == "datos-de-2"
    assert cache.obtener(ClaveCache(uuid.uuid4(), "catalogo", "v1")) is None
    assert str(T1) in ClaveCache(T1, "catalogo", "v1").texto()
    assert ClaveCache(T1, "c", "v1").texto() != ClaveCache(T2, "c", "v1").texto()


def test_cambio_de_version_invalida():
    cache = CacheLectura(AlmacenMemoria())
    cache.guardar(ClaveCache(T1, "paquete", "v1"), "viejo")
    cache.guardar(ClaveCache(T2, "paquete", "v1"), "otro-tenant")
    cache.guardar(ClaveCache(T1, "paquete", "v2"), "nuevo")
    assert cache.obtener(ClaveCache(T1, "paquete", "v1")) is None
    assert cache.obtener(ClaveCache(T1, "paquete", "v2")) == "nuevo"
    assert cache.obtener(ClaveCache(T2, "paquete", "v1")) == "otro-tenant"


def test_obtener_o_cargar_y_vencimiento():
    t = [0.0]
    cache = CacheLectura(AlmacenMemoria(reloj=lambda: t[0]), ttl_s=10)
    llamadas = []
    clave = ClaveCache(T1, "catalogo", "v1")
    for _ in range(2):
        assert cache.obtener_o_cargar(clave, lambda: llamadas.append(1) or "x") == "x"
    assert len(llamadas) == 1
    t[0] = 11.0
    assert cache.obtener(clave) is None


@pytest.mark.parametrize("tenant", [None, "", "no-es-uuid", str(T1)])
def test_clave_sin_tenant_uuid_lanza_error(tenant):
    with pytest.raises(ValueError):
        ClaveCache(tenant, "catalogo", "v1")


def test_mutacion_clave_sin_tenant_da_rojo():
    """Mutación documentada: sin el tenant en la clave, dos organizaciones colisionan (rojo de la prueba de aislación)."""
    def clave_mutada(c):  # copia de ClaveCache.texto() sin el tenant
        return f"cache:v1:{c.recurso}:{c.version}"
    a, b = ClaveCache(T1, "catalogo", "v1"), ClaveCache(T2, "catalogo", "v1")
    assert a.texto() != b.texto()
    assert clave_mutada(a) == clave_mutada(b)
