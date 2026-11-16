# -*- coding: utf-8 -*-
"""Pruebas de GOCA-01: Contrato del Agente Edge en Go para CCTV."""
from __future__ import annotations

import pytest

from app_core.errors import ErrorNegocio
from app_core.pasillo.go_cctv_agent import validar_telemetria_clip
from app_core.pasillo.videovigilancia import generar_aprovisionamiento_agente_go
from features.videovigilancia.services.cctv_provisioning_bundle import (
    generar_bundle_aprovisionamiento,
    validar_contra_schema,
)


@pytest.mark.asyncio
async def test_aprovisionamiento_agente_edge_go_valido():
    """Dado una cámara conforme, el JSON generado cumple el schema con strip_audio=True."""
    config = await generar_aprovisionamiento_agente_go(camara_id="cam-001", tenant_id="tenant-prueba")

    assert config["camara_id"] == "cam-001"
    assert config["tenant_id"] == "tenant-prueba"
    assert config["codec_required"] == "H265"
    assert config["strip_audio"] is True
    assert config["max_segment_seconds"] == 120
    assert validar_contra_schema(config) is True


def test_agente_go_rechaza_stream_con_audio():
    """R1: telemetría que reporta audio activo es rechazada por el pasillo."""
    reporte_con_audio = {
        "clip_id": "clip-001",
        "has_audio": True,
        "strip_audio": False,
        "sha256_hash": "a" * 64,
    }

    with pytest.raises(ErrorNegocio) as exc:
        validar_telemetria_clip(reporte_con_audio)

    assert exc.value.code == "CCTV_AUDIO_STREAM_PROHIBIDO"


def test_agente_go_acepta_telemetria_sin_audio():
    """Telemetría sin audio y con hash SHA-256 de 64 caracteres es válida."""
    reporte_limpio = {
        "clip_id": "clip-002",
        "has_audio": False,
        "strip_audio": True,
        "sha256_hash": "b" * 64,
    }

    resultado = validar_telemetria_clip(reporte_limpio)
    assert resultado["valido"] is True
    assert resultado["clip_id"] == "clip-002"
