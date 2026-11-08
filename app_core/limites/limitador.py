# ¤seguridad ¤seguridad-tenant
"""Limitador de ventana deslizante (SEC-13).

Algoritmo de contador de ventana deslizante: por clave se guardan el contador de la ventana fija
actual y el de la anterior; la estimación es `previo * (1 - transcurrido/ventana) + actual`.

`LimitadorPostgres` usa la tabla `ventana_peticiones` (una fila por clave) con un único UPSERT
atómico que reinicia la ventana vencida sobre la misma fila: nunca DELETE, porque `lopdp_app` no
tiene ese permiso. `LimitadorMemoria` existe solo para pruebas.
"""
from __future__ import annotations

import asyncio
import hashlib
import math
import time
from dataclasses import dataclass
from typing import Callable, Optional, Protocol

from sqlalchemy import text

from app_core.limites.politicas import Politica


class LimiteNoDisponible(Exception):
    """El almacén del limitador no responde."""


@dataclass(frozen=True)
class Resultado:
    admitido: bool
    retry_after: int  # segundos; 0 si se admite


def clave_limite(politica: Politica, identificador: str) -> str:
    """`lim:<politica>:<ambito>:<id>` con el id resumido en SHA-256 (R5: sin datos personales)."""
    resumen = hashlib.sha256(identificador.encode("utf-8")).hexdigest()[:32]
    return f"lim:{politica.nombre}:{politica.ambito}:{resumen}"


def _evaluar(politica: Politica, actual: int, previo: int, inicio: int, ahora: float) -> Resultado:
    ventana = politica.ventana_segundos
    transcurrido = max(0.0, ahora - inicio)
    estimado = previo * max(0.0, 1.0 - transcurrido / ventana) + actual
    if estimado <= politica.limite:
        return Resultado(True, 0)
    return Resultado(False, max(1, math.ceil(ventana - transcurrido)))


class Limitador(Protocol):
    async def consumir(self, politica: Politica, identificador: str) -> Resultado: ...


class LimitadorMemoria:
    """Solo para pruebas: mismo algoritmo, en un diccionario del proceso."""

    def __init__(self, reloj: Callable[[], float] = time.time) -> None:
        self._reloj = reloj
        self._filas: dict[str, tuple[int, int, int]] = {}  # clave -> (inicio, actual, previo)
        self._candado = asyncio.Lock()
        self.caido = False

    async def consumir(self, politica: Politica, identificador: str) -> Resultado:
        if self.caido:
            raise LimiteNoDisponible("limitador en memoria marcado como caído")
        ahora = self._reloj()
        ventana = politica.ventana_segundos
        inicio = int(ahora // ventana) * ventana
        clave = clave_limite(politica, identificador)
        async with self._candado:
            fila = self._filas.get(clave)
            if fila is None:
                actual, previo = 1, 0
            elif fila[0] == inicio:
                actual, previo = fila[1] + 1, fila[2]
            elif fila[0] == inicio - ventana:
                actual, previo = 1, fila[1]
            else:
                actual, previo = 1, 0
            self._filas[clave] = (inicio, actual, previo)
        return _evaluar(politica, actual, previo, inicio, ahora)


_UPSERT = text(
    """
    INSERT INTO ventana_peticiones AS v (clave, inicio, contador, previo)
    VALUES (:clave, :inicio, 1, 0)
    ON CONFLICT (clave) DO UPDATE SET
        previo = CASE
            WHEN v.inicio = EXCLUDED.inicio THEN v.previo
            WHEN v.inicio = EXCLUDED.inicio - :ventana THEN v.contador
            ELSE 0 END,
        contador = CASE WHEN v.inicio = EXCLUDED.inicio THEN v.contador + 1 ELSE 1 END,
        inicio = EXCLUDED.inicio
    RETURNING contador, previo
    """
)


class LimitadorPostgres:
    """Tabla `ventana_peticiones` en Cloud SQL; un UPSERT por consumo (1 RTT)."""

    def __init__(
        self,
        session_factory: Optional[Callable] = None,
        reloj: Callable[[], float] = time.time,
    ) -> None:
        self._session_factory = session_factory
        self._reloj = reloj

    def _fabrica(self) -> Callable:
        if self._session_factory is None:
            from app_core.db.session import async_session_factory  # diferido: lee DATABASE_URL

            self._session_factory = async_session_factory
        return self._session_factory

    async def consumir(self, politica: Politica, identificador: str) -> Resultado:
        ahora = self._reloj()
        ventana = politica.ventana_segundos
        inicio = int(ahora // ventana) * ventana
        try:
            async with self._fabrica()() as session:
                fila = (await session.execute(
                    _UPSERT,
                    {"clave": clave_limite(politica, identificador), "inicio": inicio, "ventana": ventana},
                )).one()
                await session.commit()
        except Exception as exc:  # noqa: BLE001 - cualquier fallo del almacén es «no disponible»
            raise LimiteNoDisponible(type(exc).__name__) from exc
        return _evaluar(politica, int(fila[0]), int(fila[1]), inicio, ahora)
