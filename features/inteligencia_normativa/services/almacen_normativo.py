# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤vigilancia-spdp ¤inteligencia-normativa ¤seguridad ¤monitoreo-job
"""Almacén real de los originales de la SPDP sobre `app_core.storage` (NORM-04, EVI-04).

Dos puertas, una por cuenta, sobre el bucket propio `evydentia-corpus-normativo`
(`GCP_STORAGE_BUCKET_NORMATIVO`, nunca `GCP_STORAGE_BUCKET`):

- **Escritura**, solo en el Cloud Run Job del monitoreo (`CLOUD_RUN_JOB`, cuenta `sa-evydentia-normativa`).
  Escritura única: lo que ya existe no se sobrescribe. Fuera del Job falla cerrado sin crear el cliente.
- **Lectura**, solo en el backend (`K_SERVICE`, cuenta con `roles/storage.objectViewer`). No tiene ningún método
  de escritura.
"""
from __future__ import annotations

import os
from typing import Any, Callable, Mapping, Optional

from app_core.config import VARIABLE_DE_CLOUD_RUN
from app_core.storage.gcs import Almacen, AlmacenGcs, ObjetoDemasiadoGrande, ObjetoYaExiste
from features.inteligencia_normativa.domain.errores import AlmacenNoDisponible
from features.inteligencia_normativa.services.conector_spdp import MAXIMO_BYTES

VARIABLE_BUCKET_NORMATIVO = "GCP_STORAGE_BUCKET_NORMATIVO"
VARIABLE_DE_CLOUD_RUN_JOB = "CLOUD_RUN_JOB"  # un Job no define K_SERVICE (app_core/config.py)

Fabrica = Callable[[str], Almacen]


def _crear_gcs(bucket: str) -> Almacen:
    """Cliente real con las credenciales por defecto de la cuenta que corre el proceso (sin claves)."""
    import google.auth  # type: ignore[import-not-found]
    from google.cloud import storage  # type: ignore[import-not-found]

    credenciales, proyecto = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    return AlmacenGcs(storage.Client(project=proyecto, credentials=credenciales), bucket, credenciales)


def _bucket(entorno: Mapping[str, str]) -> str:
    return entorno.get(VARIABLE_BUCKET_NORMATIVO, "").strip()


class AlmacenNormativo:
    """`AlmacenOriginales` del monitoreo: escritura única, `False` si el original ya estaba."""

    def __init__(self, almacen: Almacen) -> None:
        self._almacen = almacen

    def guardar(self, clave: str, contenido: bytes, tipo: str) -> bool:
        try:
            self._almacen.subir(clave, contenido, tipo)
        except ObjetoYaExiste:
            return False
        return True


class LectorNormativo:
    """`LectorOriginales` del backend: solo lee, con el tope de la descarga de NORM-01."""

    def __init__(self, almacen: Almacen) -> None:
        self._almacen = almacen

    def leer(self, clave: str) -> Optional[bytes]:
        try:
            return self._almacen.descargar(clave, MAXIMO_BYTES)
        except ObjetoDemasiadoGrande:
            return None


def almacen_normativo_por_defecto(entorno: Mapping[str, str] | None = None, *, crear: Fabrica | None = None) -> AlmacenNormativo:
    """Solo escribe un Cloud Run Job con el bucket normativo configurado; si no, falla cerrado sin conectar."""
    entorno = os.environ if entorno is None else entorno
    bucket = _bucket(entorno)
    if VARIABLE_DE_CLOUD_RUN_JOB not in entorno or not bucket:
        raise AlmacenNoDisponible("almacén normativo no disponible")
    return AlmacenNormativo((crear or _crear_gcs)(bucket))


def lector_normativo_por_defecto(entorno: Mapping[str, str] | None = None, *, crear: Fabrica | None = None) -> Any:
    """El lector real solo existe en el backend (`K_SERVICE`) con el bucket configurado; si no, el lector cerrado."""
    from features.inteligencia_normativa.services.revision import LectorOriginalesCerrado

    entorno = os.environ if entorno is None else entorno
    bucket = _bucket(entorno)
    if VARIABLE_DE_CLOUD_RUN not in entorno or not bucket:
        return LectorOriginalesCerrado()
    return LectorNormativo((crear or _crear_gcs)(bucket))
