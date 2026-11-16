# ¤evidencias
"""Almacén de documentos en Google Cloud Storage (EVI-01).

- Credenciales por defecto de la cuenta de servicio de Cloud Run: sin claves ni archivos JSON. La URL
  firmada V4 se firma con IAM Credentials (`signBlob`) a través de la cuenta y el token por defecto.
- Escritura única: la URL de subida firma la cabecera `x-goog-if-generation-match: 0`, así que una
  segunda subida a la misma clave la rechaza el almacén.
- Este módulo nunca borra objetos: el backend no tiene ese permiso y ninguna función lo pide.
- Fuera de la nube falla cerrado y no intenta conectar. `google-cloud-storage` se importa al usarlo
  (lo declara DEP-01 en requirements.txt); en las pruebas se inyecta un almacén simulado.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Protocol

from app_core.config import corre_en_cloud_run

VARIABLE_BUCKET = "GCP_STORAGE_BUCKET"
CABECERA_ESCRITURA_UNICA = "x-goog-if-generation-match"
CADUCIDAD_SUBIDA_SEGUNDOS = 900
MODO_RETENCION = "Unlocked"


@dataclass(frozen=True)
class FirmaSubida:
    """Lo que el navegador necesita para subir: la URL, el método y las cabeceras que se firmaron."""

    clave: str
    url: str
    metodo: str = "PUT"
    cabeceras: dict[str, str] = field(default_factory=dict)
    caduca_en_segundos: int = CADUCIDAD_SUBIDA_SEGUNDOS


class AlmacenNoDisponible(Exception):
    """No hay almacén real: se corre fuera de la nube o falta el bucket."""


class ObjetoDemasiadoGrande(Exception):
    """El objeto guardado supera el máximo que el servidor acepta descargar."""


class ObjetoYaExiste(Exception):
    """La clave ya tiene un objeto: la escritura es única y nunca se sobrescribe (EVI-04)."""


class Almacen(Protocol):
    def firmar_subida(self, clave: str, tipo_mime: str) -> FirmaSubida: ...

    def subir(self, clave: str, contenido: bytes, tipo_mime: str) -> None:
        """Sube bytes del servidor con escritura única; ObjetoYaExiste si la clave ya existe."""
        ...

    def descargar(self, clave: str, maximo_bytes: int) -> Optional[bytes]:
        """Contenido del objeto, o None si no existe. ObjetoDemasiadoGrande si pasa del máximo."""
        ...

    def fijar_retencion(self, clave: str, retener_hasta: datetime) -> None:
        """Fija la retención del objeto en modo desbloqueado; lanza una excepción si no lo logra."""
        ...


class AlmacenGcs:
    """Implementación sobre un cliente de Cloud Storage y las credenciales por defecto."""

    def __init__(self, cliente: Any, bucket: str, credenciales: Any, peticion: Any = None) -> None:
        self._bucket = cliente.bucket(bucket)
        self._credenciales = credenciales
        self._peticion = peticion

    def _token(self) -> str:
        if self._peticion is None:
            from google.auth.transport.requests import Request  # type: ignore[import-not-found]

            self._peticion = Request()
        self._credenciales.refresh(self._peticion)
        return self._credenciales.token

    def firmar_subida(self, clave: str, tipo_mime: str) -> FirmaSubida:
        cabeceras = {CABECERA_ESCRITURA_UNICA: "0"}
        url = self._bucket.blob(clave).generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=CADUCIDAD_SUBIDA_SEGUNDOS),
            method="PUT",
            content_type=tipo_mime,
            headers=cabeceras,
            service_account_email=self._credenciales.service_account_email,
            access_token=self._token(),
        )
        return FirmaSubida(
            clave=clave, url=url, cabeceras={**cabeceras, "Content-Type": tipo_mime}
        )

    def subir(self, clave: str, contenido: bytes, tipo_mime: str) -> None:
        from google.api_core.exceptions import PreconditionFailed  # type: ignore[import-not-found]

        try:
            self._bucket.blob(clave).upload_from_string(contenido, content_type=tipo_mime, if_generation_match=0)
        except PreconditionFailed as exc:
            raise ObjetoYaExiste(clave) from exc

    def descargar(self, clave: str, maximo_bytes: int) -> Optional[bytes]:
        from google.api_core.exceptions import NotFound  # type: ignore[import-not-found]

        blob = self._bucket.blob(clave)
        try:
            blob.reload()
        except NotFound:
            return None
        if (blob.size or 0) > maximo_bytes:
            raise ObjetoDemasiadoGrande(clave)
        return blob.download_as_bytes()

    def fijar_retencion(self, clave: str, retener_hasta: datetime) -> None:
        blob = self._bucket.blob(clave)
        blob.reload()
        blob.retention.mode = MODO_RETENCION
        blob.retention.retain_until_time = retener_hasta.astimezone(timezone.utc)
        blob.patch()


def almacen_por_defecto() -> Almacen:
    """Almacén real de la nube; fuera de Cloud Run o sin bucket falla cerrado sin conectar."""
    bucket = os.environ.get(VARIABLE_BUCKET, "").strip()
    if not corre_en_cloud_run() or not bucket:
        raise AlmacenNoDisponible(VARIABLE_BUCKET)
    import google.auth  # type: ignore[import-not-found]
    from google.cloud import storage  # type: ignore[import-not-found]

    credenciales, proyecto = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    return AlmacenGcs(storage.Client(project=proyecto, credentials=credenciales), bucket, credenciales)
