# -*- coding: utf-8 -*-
# ¤demo
"""Objetos de los tenants vencidos: se borran por prefijo `tenant_id/` (clave `{tenant_id}/{tarea}/…`)."""
from __future__ import annotations

import os
from typing import Iterable, Protocol


class Almacen(Protocol):
    def listar(self, prefijo: str) -> list[str]: ...

    def borrar(self, claves: list[str]) -> None: ...


class AlmacenS3:
    """Buckets compatibles con S3 (R2 o la interoperabilidad de Cloud Storage), por `boto3`."""

    def __init__(self, buckets: Iterable[str], cliente=None) -> None:
        self._buckets = tuple(buckets)
        if not self._buckets:
            raise ValueError("sin buckets: define PURGA_BUCKETS o R2_BUCKET_NAME.")
        self._cliente = cliente

    @classmethod
    def desde_entorno(cls, env=os.environ) -> "AlmacenS3":
        nombres = env.get("PURGA_BUCKETS") or env.get("R2_BUCKET_NAME") or ""
        return cls([b.strip() for b in nombres.split(",") if b.strip()])

    def _c(self):
        if self._cliente is None:
            import boto3
            from botocore.config import Config

            self._cliente = boto3.client(
                "s3", endpoint_url=os.environ.get("R2_ENDPOINT_URL"),
                aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
                region_name="auto", config=Config(signature_version="s3v4"))
        return self._cliente

    def _claves(self, bucket: str, prefijo: str) -> list[str]:
        claves: list[str] = []
        for pagina in self._c().get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefijo):
            claves += [o["Key"] for o in pagina.get("Contents", [])]
        return claves

    def listar(self, prefijo: str) -> list[str]:
        return [f"{b}/{k}" for b in self._buckets for k in self._claves(b, prefijo)]

    def borrar(self, claves: list[str]) -> None:
        for bucket in self._buckets:
            propias = [c[len(bucket) + 1:] for c in claves if c.startswith(bucket + "/")]
            for i in range(0, len(propias), 1000):
                self._c().delete_objects(
                    Bucket=bucket, Delete={"Objects": [{"Key": k} for k in propias[i:i + 1000]], "Quiet": True})
