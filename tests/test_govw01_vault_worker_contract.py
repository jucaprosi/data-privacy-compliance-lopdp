# -*- coding: utf-8 -*-
"""Pruebas de GOVW-01: Satélite Cloud Run en Go para Ingesta Eventarc y Purga Masiva."""
from __future__ import annotations

import importlib
import json
import pytest

from app_core.errors import ErrorNegocio
from app_core.pasillo.go_vault_worker import (
    firmar_mensaje,
    procesar_ingesta_eventarc,
    registrar_acta_purga,
)


@pytest.mark.asyncio
async def test_contrato_ingesta_eventarc_go_vault_worker():
    """Dado un evento de subida GCS con firma válida, sella el hash y actualiza cuota."""
    payload = {
        "tenant_id": "tenant-xyz",
        "object_key": "evidencias/2026/acta_01.pdf",
        "size_bytes": 1048576,
        "sha256_hex": "c" * 64,
        "bucket": "boveda-evidencias",
    }
    cuerpo = json.dumps(payload, sort_keys=True).encode("utf-8")
    firma_valida = firmar_mensaje(cuerpo)

    res = await procesar_ingesta_eventarc(payload, firma_valida)
    assert res["estado"] == "ingestado"
    assert res["tenant_id"] == "tenant-xyz"
    assert res["sha256_hex"] == "c" * 64
    assert res["cuota_actualizada"] is True

    # Mutación: firma inválida rechaza con 401
    with pytest.raises(ErrorNegocio) as exc:
        await procesar_ingesta_eventarc(payload, "firma_falsa_o_corrupta")
    assert exc.value.code == "AUTENTICACION_SATELITE_INVALIDA"
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_contrato_purga_masiva_go_vault_worker():
    """Dado un lote de purga, devuelve acta_lote_sha256 determinista para el certificado."""
    resultado = {
        "politica_id": "pol-ret-001",
        "objetos_eliminados_count": 25,
        "acta_lote_sha256": "d" * 64,
        "timestamp_utc": "2026-11-15T22:00:00Z",
    }
    cuerpo = json.dumps(resultado, sort_keys=True).encode("utf-8")
    firma_valida = firmar_mensaje(cuerpo)

    mod_cons = importlib.import_module("app_core.pasillo.conservacion")
    res = await mod_cons.registrar_purga_satelite_go(resultado, firma_valida)
    assert res["acta_registrada"] is True
    assert res["politica_id"] == "pol-ret-001"
    assert res["objetos_eliminados_count"] == 25
    assert res["acta_lote_sha256"] == "d" * 64
