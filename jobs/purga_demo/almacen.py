# -*- coding: utf-8 -*-
# ¤demo
"""Objetos de los tenants vencidos en Google Cloud Storage: se borran por prefijo `tenant_id/`."""
from __future__ import annotations

import os
from typing import Iterable, Protocol

LOTE = 100


class ErrorAlmacen(RuntimeError):
    """El almacén se niega a funcionar o a borrar; el job sale con error."""


class Almacen(Protocol):
    def listar(self, prefijo: str) -> list[str]: ...

    def borrar(self, claves: list[str]) -> None: ...


def _con_retencion(bucket) -> bool:
    """Política de retención, política bloqueada o retención por objeto: el bucket no admite purga."""
    return bool(getattr(bucket, "retention_period", None)
                or getattr(bucket, "retention_policy_locked", False)
                or getattr(bucket, "object_retention_mode", None))


class AlmacenGCS:
    """Buckets de la demo, con el cliente nativo y las credenciales por defecto de la cuenta del job.

    Las claves que devuelve `listar` son `bucket/objeto`. Solo toca los buckets de `PURGA_BUCKETS`, solo borra
    claves que antes listó bajo un prefijo `tenant_id/` y se niega a construirse si un bucket tiene retención.
    """

    def __init__(self, buckets: Iterable[str], cliente=None) -> None:
        self._buckets = tuple(buckets)
        if not self._buckets:
            raise ErrorAlmacen("falta PURGA_BUCKETS: el job no sabe qué buckets purgar.")
        if cliente is None:
            from google.cloud import storage  # credenciales por defecto; sin claves

            cliente = storage.Client()
        self._cliente = cliente
        self._prefijos: set[str] = set()
        for nombre in self._buckets:  # falla cerrada: lee los metadatos antes de listar nada
            if _con_retencion(cliente.get_bucket(nombre)):
                raise ErrorAlmacen(f"el bucket {nombre} tiene retención u objetos bloqueados; la purga no puede "
                                   "borrar ahí. Los buckets de la demo no llevan retención.")

    @classmethod
    def desde_entorno(cls, env=os.environ, cliente=None) -> "AlmacenGCS":
        nombres = [b.strip() for b in env.get("PURGA_BUCKETS", "").split(",") if b.strip()]
        return cls(nombres, cliente=cliente)

    def listar(self, prefijo: str) -> list[str]:
        if not prefijo or not prefijo.endswith("/"):
            raise ErrorAlmacen("el prefijo de purga debe ser `tenant_id/`.")
        self._prefijos.add(prefijo)
        return [f"{b}/{blob.name}" for b in self._buckets
                for blob in self._cliente.list_blobs(b, prefix=prefijo)]

    def _permitida(self, clave: str) -> tuple[str, str]:
        bucket, _, objeto = clave.partition("/")
        if bucket not in self._buckets:
            raise ErrorAlmacen(f"el bucket {bucket} no está en PURGA_BUCKETS.")
        if not any(objeto.startswith(p) for p in self._prefijos):
            raise ErrorAlmacen("clave fuera del prefijo `tenant_id/` listado; no se borra nada.")
        return bucket, objeto

    def borrar(self, claves: list[str]) -> None:
        destinos = [self._permitida(c) for c in claves]  # se valida todo antes de borrar nada
        for i in range(0, len(destinos), LOTE):
            try:
                with self._cliente.batch():
                    for bucket, objeto in destinos[i:i + LOTE]:
                        self._cliente.bucket(bucket).blob(objeto).delete()
            except Exception as error:
                raise ErrorAlmacen(f"falló el borrado de objetos ({type(error).__name__}); "
                                   "revisa que el bucket no tenga retención.") from None
