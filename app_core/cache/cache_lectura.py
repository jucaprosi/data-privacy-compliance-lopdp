# ¤cloud-run-perf ¤seguridad-tenant
"""Caché de lectura en Memorystore con la clave siempre separada por tenant (GCP-06).

`INV_EDGE_CACHE_PUBLIC_STATIC_ONLY`: la clave lleva `tenant_id` y versión del recurso; un cambio de
versión produce otra clave y borra la entrada anterior, así que ninguna organización lee la caché de otra.
El almacén se inyecta: `AlmacenMemoria` es el doble sin red de Memorystore; `AlmacenRedis` envuelve un
cliente ya creado (no se importa ninguna librería de red aquí).
"""
from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass
from typing import Callable, Protocol

CABECERA_NO_STORE = {"Cache-Control": "no-store"}
CABECERA_ESTATICOS = {"Cache-Control": "public, max-age=31536000, immutable"}
_PREFIJO = "cache:v1"


def cabeceras_datos_de_organizacion() -> dict[str, str]:
    """Cabeceras de toda respuesta con datos de una organización (copia nueva en cada llamada)."""
    return dict(CABECERA_NO_STORE)


@dataclass(frozen=True)
class ClaveCache:
    tenant_id: uuid.UUID
    recurso: str
    version: str

    def __post_init__(self):
        if not isinstance(self.tenant_id, uuid.UUID):
            raise ValueError("tenant_id debe ser un UUID: la caché nunca se comparte entre organizaciones")
        for campo in ("recurso", "version"):
            valor = getattr(self, campo)
            if not isinstance(valor, str) or not valor or ":" in valor:
                raise ValueError(f"{campo} debe ser un texto no vacío sin ':'")

    def texto(self) -> str:
        return f"{_PREFIJO}:{self.tenant_id}:{self.recurso}:{self.version}"

    def prefijo_recurso(self) -> str:
        return f"{_PREFIJO}:{self.tenant_id}:{self.recurso}:"


class AlmacenCache(Protocol):
    def get(self, clave: str) -> str | None: ...
    def set(self, clave: str, valor: str, ttl_s: int) -> None: ...
    def delete(self, clave: str) -> None: ...
    def keys(self, prefijo: str) -> list[str]: ...


class AlmacenMemoria:
    """Doble de Memorystore: sin red, con vencimiento por reloj inyectable."""

    def __init__(self, reloj: Callable[[], float] = time.monotonic):
        self._datos: dict[str, tuple[str, float]] = {}
        self._reloj = reloj

    def get(self, clave):
        par = self._datos.get(clave)
        if par is None or par[1] <= self._reloj():
            self._datos.pop(clave, None)
            return None
        return par[0]

    def set(self, clave, valor, ttl_s):
        self._datos[clave] = (valor, self._reloj() + ttl_s)

    def delete(self, clave):
        self._datos.pop(clave, None)

    def keys(self, prefijo):
        return [k for k in list(self._datos) if k.startswith(prefijo) and self.get(k) is not None]


class AlmacenRedis:
    """Adaptador de un cliente redis-py (decode_responses=True) ya creado por el arranque."""

    def __init__(self, cliente):
        self._c = cliente

    def get(self, clave):
        return self._c.get(clave)

    def set(self, clave, valor, ttl_s):
        self._c.set(clave, valor, ex=ttl_s)

    def delete(self, clave):
        self._c.delete(clave)

    def keys(self, prefijo):
        return list(self._c.scan_iter(match=prefijo + "*"))


class CacheLectura:
    def __init__(self, almacen: AlmacenCache, ttl_s: int = 300):
        if ttl_s <= 0:
            raise ValueError("ttl_s debe ser positivo")
        self._almacen, self._ttl = almacen, ttl_s

    def obtener(self, clave: ClaveCache) -> str | None:
        return self._almacen.get(clave.texto())

    def guardar(self, clave: ClaveCache, valor: str) -> None:
        # Invalidación por versión: se borran las entradas de otras versiones del mismo recurso y tenant.
        propia = clave.texto()
        for otra in self._almacen.keys(clave.prefijo_recurso()):
            if otra != propia:
                self._almacen.delete(otra)
        self._almacen.set(propia, valor, self._ttl)

    def obtener_o_cargar(self, clave: ClaveCache, cargar: Callable[[], str]) -> str:
        valor = self.obtener(clave)
        if valor is None:
            valor = cargar()
            self.guardar(clave, valor)
        return valor


def cache_desde_entorno(entorno: dict | None = None, ttl_s: int = 300) -> CacheLectura:
    """Sin REDIS_URL la caché usa memoria local por proceso: la app funciona sin Memorystore.

    Con REDIS_URL se importa `redis` en ese momento (no al importar el módulo).
    """
    env = os.environ if entorno is None else entorno
    url = (env.get("REDIS_URL") or "").strip()
    if not url:
        return CacheLectura(AlmacenMemoria(), ttl_s)
    import redis  # noqa: PLC0415 - import tardío: solo si hay Memorystore configurado

    return CacheLectura(AlmacenRedis(redis.Redis.from_url(url, decode_responses=True)), ttl_s)
