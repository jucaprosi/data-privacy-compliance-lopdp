"""Cliente Cloudflare R2 con URLs prefirmadas.

- Bucket privado. Subida directa desde frontend vía PUT prefirmada.
- Descarga vía GET prefirmada.
- Prefijo de key: {tenant_id}/{task_id}/{uuid}_{filename}
"""
import os
import uuid

import boto3
from botocore.config import Config

_R2_ENDPOINT = os.environ.get("R2_ENDPOINT_URL")
_R2_BUCKET = os.environ.get("R2_BUCKET_NAME")
_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=_R2_ENDPOINT,
            aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
            region_name="auto",
            config=Config(signature_version="s3v4"),
        )
    return _client


def build_key(tenant_id: str, task_id: str, filename: str) -> str:
    """Construye el prefijo organizado del bucket."""
    safe = filename.replace("/", "_").replace("\\", "_")
    return f"{tenant_id}/{task_id}/{uuid.uuid4().hex}_{safe}"


def generate_upload_url(key: str, mime_type: str, expires: int = 900) -> dict:
    """URL PUT prefirmada. El frontend sube directo a R2."""
    url = _get_client().generate_presigned_url(
        "put_object",
        Params={"Bucket": _R2_BUCKET, "Key": key, "ContentType": mime_type},
        ExpiresIn=expires,
    )
    return {"url": url, "key": key, "headers": {"Content-Type": mime_type}}


def generate_download_url(key: str, expires: int = 900) -> str:
    """URL GET prefirmada para descarga."""
    return _get_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": _R2_BUCKET, "Key": key},
        ExpiresIn=expires,
    )


def delete_object(key: str) -> None:
    """Elimina un objeto del bucket."""
    _get_client().delete_object(Bucket=_R2_BUCKET, Key=key)
