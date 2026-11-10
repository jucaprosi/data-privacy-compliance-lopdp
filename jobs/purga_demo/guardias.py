# -*- coding: utf-8 -*-
# ¤demo ¤seguridad
"""Guardias del job: solo corre en el proyecto y la base de la demo, nunca en producción."""
from __future__ import annotations

import os
from typing import Callable, Mapping, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from app_core.entorno.guardias import proyecto_en_ejecucion
from app_core.huellas_produccion import apunta_a_produccion, base_es_produccion

SEGUNDOS_CONEXION = 5


class PurgaRechazada(RuntimeError):
    """El job se niega a correr; el mensaje nombra la causa y nunca incluye la URL de la base."""


def _base_sin_marcador_de_entorno(url: str) -> bool:
    """Abre una conexión síncrona y pregunta `base_es_produccion`. Un fallo cuenta como producción."""
    try:
        destino = make_url(url)
        if not destino.drivername.startswith("postgresql"):
            return True
        motor = create_engine(destino.set(drivername="postgresql+psycopg"),
                              connect_args={"connect_timeout": SEGUNDOS_CONEXION}, pool_pre_ping=False)
        try:
            with motor.connect() as conexion:
                return base_es_produccion(conexion)
        finally:
            motor.dispose()
    except Exception:
        return True


def exigir_demo(
    url: Optional[str],
    entorno: Optional[Mapping[str, str]] = None,
    proyecto: Optional[Callable[[], Optional[str]]] = None,
    comprobar_base: Callable[[str], bool] = _base_sin_marcador_de_entorno,
) -> None:
    """Lanza `PurgaRechazada` salvo que `APP_ENV=demo`, el proyecto sea el de la demo y la base no sea producción."""
    env = os.environ if entorno is None else entorno
    if env.get("APP_ENV", "").strip().lower() != "demo":
        raise PurgaRechazada("la purga solo corre con APP_ENV=demo.")
    huella = env.get("HUELLA_PROYECTO_PRODUCCION", "").strip().lower()
    if not huella:
        raise PurgaRechazada("falta HUELLA_PROYECTO_PRODUCCION; no se puede descartar el proyecto de producción.")
    actual = ((proyecto() if proyecto else proyecto_en_ejecucion()) or "").strip().lower()
    if not actual:
        raise PurgaRechazada("no se pudo determinar el proyecto de Google Cloud donde corre el job.")
    if actual == huella:
        raise PurgaRechazada("el job corre en el proyecto de Google Cloud de producción.")
    esperado = env.get("PURGA_PROYECTO_DEMO", "").strip().lower()
    if esperado and actual != esperado:
        raise PurgaRechazada("el proyecto de Google Cloud no es el de la demo.")
    if not url or not url.strip():
        raise PurgaRechazada("falta PURGA_DATABASE_URL.")
    if huella in url.lower() or apunta_a_produccion(url, env):
        raise PurgaRechazada("la base es la de producción.")
    if comprobar_base(url):
        raise PurgaRechazada("la base no tiene el marcador de entorno 'demo' o 'pruebas'.")
