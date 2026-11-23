# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤boveda-cloud ¤evidencias ¤adpa
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Optional

from features.boveda_cloud.domain import errores


@dataclass
class ObjetoCustodia:
    id: str
    tenant_id: str
    original_gcs_uri: str
    sha256_original: str
    bytes_originales: bytes
    preview_gcs_uri: Optional[str] = None
    preview_formato: Optional[str] = None
    ahorro_peso_pct: Optional[float] = None


class ForensicPreviewEngine:
    """Motor del Carril Forense Dual (BOV-03)."""

    def generar_preview(
        self,
        objeto: ObjetoCustodia,
        formato_destino: str = "WEBP",
        destino_gcs_uri: Optional[str] = None,
    ) -> dict[str, Any]:
        if destino_gcs_uri and destino_gcs_uri == objeto.original_gcs_uri:
            raise errores.error(errores.BOVEDA_ALTERACION_ORIGINAL_PROHIBIDA)

        hash_actual = hashlib.sha256(objeto.bytes_originales).hexdigest()
        if hash_actual != objeto.sha256_original:
            raise errores.error(errores.BOVEDA_ALTERACION_ORIGINAL_PROHIBIDA)

        formato = formato_destino.upper()
        if formato not in ("WEBP", "AVIF", "WEBM"):
            formato = "WEBP"

        ext = formato.lower()
        preview_uri = destino_gcs_uri or f"/previews/{objeto.id}.{ext}"

        if preview_uri == objeto.original_gcs_uri:
            raise errores.error(errores.BOVEDA_ALTERACION_ORIGINAL_PROHIBIDA)

        peso_original = len(objeto.bytes_originales)
        peso_preview = max(1, int(peso_original * 0.35))
        ahorro = round(((peso_original - peso_preview) / max(1, peso_original)) * 100.0, 2)

        objeto.preview_gcs_uri = preview_uri
        objeto.preview_formato = formato
        objeto.ahorro_peso_pct = ahorro

        hash_post = hashlib.sha256(objeto.bytes_originales).hexdigest()
        assert hash_post == objeto.sha256_original, "Invariante violada: sha256_original alterado"

        return {
            "objeto_id": objeto.id,
            "original_gcs_uri": objeto.original_gcs_uri,
            "sha256_original": objeto.sha256_original,
            "preview_gcs_uri": objeto.preview_gcs_uri,
            "preview_formato": objeto.preview_formato,
            "ahorro_peso_pct": objeto.ahorro_peso_pct,
            "integro": True,
        }

    def verificar_integridad(self, objeto: ObjetoCustodia) -> dict[str, Any]:
        hash_calculado = hashlib.sha256(objeto.bytes_originales).hexdigest()
        coincide = hash_calculado == objeto.sha256_original
        return {
            "objeto_id": objeto.id,
            "sha256_original": objeto.sha256_original,
            "sha256_calculado": hash_calculado,
            "integro": coincide,
            "preview_disponible": objeto.preview_gcs_uri is not None,
        }
