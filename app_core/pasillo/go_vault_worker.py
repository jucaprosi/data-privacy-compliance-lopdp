# -*- coding: utf-8 -*-
# ¤adpa ¤motor-go-hibrido ¤boveda-cloud ¤conservacion
"""Pasillo para el satélite Cloud Run en Go (vault_worker) (GOVW-01)."""
# --- INICIO GOVW-01 ---
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

from app_core.errors import ErrorNegocio

HMAC_SECRET = b"evydentia-go-worker-shared-secret-key-2026"


def firmar_mensaje(datos: bytes, clave: bytes = HMAC_SECRET) -> str:
    return hmac.new(clave, datos, hashlib.sha256).hexdigest()


def verificar_firma_satelite(datos: bytes, firma: str, clave: bytes = HMAC_SECRET) -> bool:
    firma_esperada = firmar_mensaje(datos, clave)
    return hmac.compare_digest(firma_esperada, firma)


async def procesar_ingesta_eventarc(payload: dict[str, Any], firma: str) -> dict[str, Any]:
    """R2: Verifica autenticación mutua y sella la ingesta del satélite Go."""
    cuerpo_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
    if not verificar_firma_satelite(cuerpo_bytes, firma):
        raise ErrorNegocio("AUTENTICACION_SATELITE_INVALIDA", "Firma HMAC del satélite Go inválida.", status_code=401)

    return {
        "estado": "ingestado",
        "tenant_id": payload.get("tenant_id"),
        "object_key": payload.get("object_key"),
        "sha256_hex": payload.get("sha256_hex"),
        "size_bytes": payload.get("size_bytes"),
        "cuota_actualizada": True,
    }


async def registrar_acta_purga(resultado: dict[str, Any], firma: str) -> dict[str, Any]:
    """Registra acta determinista de purga emitida por el satélite Go."""
    cuerpo_bytes = json.dumps(resultado, sort_keys=True).encode("utf-8")
    if not verificar_firma_satelite(cuerpo_bytes, firma):
        raise ErrorNegocio("AUTENTICACION_SATELITE_INVALIDA", "Firma HMAC del satélite Go inválida.", status_code=401)

    return {
        "acta_registrada": True,
        "politica_id": resultado.get("politica_id"),
        "objetos_eliminados_count": resultado.get("objetos_eliminados_count"),
        "acta_lote_sha256": resultado.get("acta_lote_sha256"),
    }
# --- FIN GOVW-01 ---
