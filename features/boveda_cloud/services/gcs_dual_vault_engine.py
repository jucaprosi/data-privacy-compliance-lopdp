# ¤boveda-cloud ¤conservacion ¤evidencias
"""Motor de la bóveda dual: enrutamiento por plazo de retención y URLs firmadas V4 directas a Cloud Storage (BOV-02).

- `INV_LOPDP_VAULT_TIER_SEPARATION`: `retencion_dias < 30` va al bucket de vida corta (STANDARD, sin Autoclass,
  borrado automático al cumplirse el plazo); `>= 30`, al de retención larga con Autoclass y bloqueo WORM.
- `INV_LOPDP_DIRECT_TO_GCS_ZERO_RAM_STREAM`: el servidor solo firma; los bytes los sube o baja el navegador.
  La firma de subida fija `Content-Length` y `x-goog-content-sha256`.
- Todo objeto vive bajo `{tenant_id}/{categoria}/{objeto_id}`: la URL firmada no sale de ese prefijo.
- Funciones puras: la firma real se inyecta (`Firmador`). Sin nube falla cerrado y no intenta conectar.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Protocol

from app_core.config import corre_en_cloud_run

BUCKET_CORTO = "lopdp360-vault-short-ttl"
BUCKET_LARGO = "lopdp360-vault-long-retention"
UMBRAL_RETENCION_DIAS = 30
CADUCIDAD_FIRMA_SEGUNDOS = 900
CABECERA_SHA256 = "x-goog-content-sha256"

_SEGMENTO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class AlmacenBovedaNoDisponible(Exception):
    """No hay almacén real: se corre fuera de la nube."""


class ClaveInvalida(ValueError):
    """Un segmento de la clave (tenant, categoría u objeto) no es válido."""


@dataclass(frozen=True)
class DestinoBoveda:
    bucket: str
    storage_class: str
    autoclass: bool
    object_lock_worm: bool
    lifecycle_delete_days: Optional[int]


@dataclass(frozen=True)
class FirmaV4:
    url: str
    metodo: str
    cabeceras: dict[str, str]
    caduca_en_segundos: int = CADUCIDAD_FIRMA_SEGUNDOS


class Firmador(Protocol):
    def firmar(self, bucket: str, clave: str, metodo: str, cabeceras: dict[str, str]) -> str:
        """URL firmada V4 para `metodo` sobre bucket/clave, con esas cabeceras firmadas."""
        ...


def resolver_destino(retencion_dias: int) -> DestinoBoveda:
    """R1: el destino es función solo del plazo de retención."""
    if retencion_dias <= 0:
        raise ValueError("retencion_dias debe ser positivo")
    if retencion_dias < UMBRAL_RETENCION_DIAS:
        return DestinoBoveda(BUCKET_CORTO, "STANDARD", False, False, retencion_dias)
    return DestinoBoveda(BUCKET_LARGO, "STANDARD", True, True, None)


def worm_lock_hasta(retencion_dias: int, ahora: Optional[datetime] = None) -> Optional[datetime]:
    """Fin del bloqueo WORM; None en el bucket de vida corta."""
    if not resolver_destino(retencion_dias).object_lock_worm:
        return None
    return (ahora or datetime.now(timezone.utc)) + timedelta(days=retencion_dias)


def construir_clave(tenant_id: str, categoria: str, objeto_id: str) -> str:
    """`{tenant_id}/{categoria}/{objeto_id}`; ningún segmento puede traer `/`, `..` ni estar vacío."""
    for segmento in (tenant_id, categoria, objeto_id):
        if not isinstance(segmento, str) or not _SEGMENTO.match(segmento) or ".." in segmento:
            raise ClaveInvalida("segmento de clave no válido")
    return f"{tenant_id}/{categoria}/{objeto_id}"


def clave_pertenece_a_tenant(clave: str, tenant_id: str) -> bool:
    partes = clave.split("/")
    return len(partes) == 3 and partes[0] == tenant_id and all(partes)


def _exigir_sha256(sha256: str) -> str:
    huella = sha256.strip().lower()
    if not _SHA256.match(huella):
        raise ValueError("sha256 no válido")
    return huella


def firmar_subida(firmador: Firmador, tenant_id: str, categoria: str, objeto_id: str, retencion_dias: int,
                  tamano_bytes: int, sha256: str) -> tuple[DestinoBoveda, FirmaV4]:
    """R2: URL PUT con `Content-Length` y `x-goog-content-sha256` firmados; la API no recibe bytes."""
    if tamano_bytes <= 0:
        raise ValueError("tamano_bytes debe ser positivo")
    destino = resolver_destino(retencion_dias)
    clave = construir_clave(tenant_id, categoria, objeto_id)
    cabeceras = {"Content-Length": str(tamano_bytes), CABECERA_SHA256: _exigir_sha256(sha256)}
    url = firmador.firmar(destino.bucket, clave, "PUT", cabeceras)
    return destino, FirmaV4(url=url, metodo="PUT", cabeceras=cabeceras)


def firmar_descarga(firmador: Firmador, bucket: str, tenant_id: str, categoria: str, objeto_id: str) -> FirmaV4:
    """URL GET acotada a la clave del objeto; solo vale para los dos buckets de la bóveda."""
    if bucket not in (BUCKET_CORTO, BUCKET_LARGO):
        raise ValueError("bucket fuera de la bóveda")
    clave = construir_clave(tenant_id, categoria, objeto_id)
    return FirmaV4(url=firmador.firmar(bucket, clave, "GET", {}), metodo="GET", cabeceras={})


class FirmadorGcs:
    """Firma V4 con IAM Credentials (`signBlob`) y las credenciales por defecto de Cloud Run: sin claves."""

    def __init__(self, cliente: Any, credenciales: Any, peticion: Any = None) -> None:
        self._cliente = cliente
        self._credenciales = credenciales
        self._peticion = peticion

    def _token(self) -> str:
        if self._peticion is None:
            from google.auth.transport.requests import Request  # type: ignore[import-not-found]

            self._peticion = Request()
        self._credenciales.refresh(self._peticion)
        return self._credenciales.token

    def firmar(self, bucket: str, clave: str, metodo: str, cabeceras: dict[str, str]) -> str:
        return self._cliente.bucket(bucket).blob(clave).generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=CADUCIDAD_FIRMA_SEGUNDOS),
            method=metodo,
            headers=cabeceras or None,
            service_account_email=self._credenciales.service_account_email,
            access_token=self._token(),
        )


def firmador_por_defecto() -> Firmador:
    """Firmador real; fuera de Cloud Run falla cerrado sin conectar. `google-cloud-storage` se importa al usarlo."""
    if not corre_en_cloud_run():
        raise AlmacenBovedaNoDisponible("fuera de Cloud Run")
    import google.auth  # type: ignore[import-not-found]
    from google.cloud import storage  # type: ignore[import-not-found]

    credenciales, proyecto = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    return FirmadorGcs(storage.Client(project=proyecto, credentials=credenciales), credenciales)
