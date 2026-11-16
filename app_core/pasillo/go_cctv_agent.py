# -*- coding: utf-8 -*-
# ¤adpa ¤motor-go-hibrido ¤videovigilancia-cctv ¤boveda-cloud
"""Pasillo para el agente edge en Go (GOCA-01)."""
# --- INICIO GOCA-01 ---
from __future__ import annotations

from typing import Any
from app_core.errors import ErrorNegocio


def validar_telemetria_clip(reporte: dict[str, Any]) -> dict[str, Any]:
    """R1: Supresión forzada de audio en el borde."""
    if reporte.get("has_audio", False) or not reporte.get("strip_audio", True):
        raise ErrorNegocio("CCTV_AUDIO_STREAM_PROHIBIDO", "El stream contiene pista de audio prohibida por la LOPDP.")
    if not reporte.get("sha256_hash") or len(reporte.get("sha256_hash", "")) != 64:
        raise ErrorNegocio("CCTV_HASH_ORIGEN_INVALIDO", "El hash SHA-256 en origen no es válido.")
    return {"valido": True, "clip_id": reporte.get("clip_id"), "sha256": reporte.get("sha256_hash")}
# --- FIN GOCA-01 ---
