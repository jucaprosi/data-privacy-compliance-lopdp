# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤videovigilancia-cctv ¤motor-go-hibrido ¤adpa
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "services_go" / "cctv_agent" / "config_schema.json"


def generar_bundle_aprovisionamiento(camara_id: str, tenant_id: str) -> dict[str, Any]:
    """Genera configuración compatible con config_schema.json del agente en Go."""
    return {
        "tenant_id": tenant_id,
        "camara_id": camara_id,
        "codec_required": "H265",
        "strip_audio": True,
        "max_segment_seconds": 120,
        "upload_signed_url_endpoint": f"https://api.evydentia.cloud/api/v1/boveda-cloud/upload-url/{tenant_id}",
    }


def validar_contra_schema(config: dict[str, Any]) -> bool:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    requeridos = schema.get("required", [])
    for campo in requeridos:
        if campo not in config:
            return False
    if config.get("codec_required") != "H265":
        return False
    if config.get("strip_audio") is not True:
        return False
    return True
