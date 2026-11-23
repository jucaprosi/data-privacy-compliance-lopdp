# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"""Pruebas de BOV-03: Carril Forense Dual en Bóveda Cloud."""
from __future__ import annotations

import hashlib
import pytest

from app_core.errors import ErrorNegocio
from features.boveda_cloud.domain import errores
from features.boveda_cloud.services.forensic_preview_engine import (
    ForensicPreviewEngine,
    ObjetoCustodia,
)


def test_carril_forense_dual_preserva_sha256_original():
    """Dado un archivo original, generar preview WebP/WebM registra preview_gcs_uri sin alterar el original."""
    engine = ForensicPreviewEngine()
    contenido = b"DATOS_PROBATORIOS_VIDEO_CCTV_CAM01_TIMESTAMP_20261115_ORIGINAL_INTACTO"
    sha_orig = hashlib.sha256(contenido).hexdigest()

    objeto = ObjetoCustodia(
        id="obj-cctv-001",
        tenant_id="tenant-prueba",
        original_gcs_uri="gs://boveda-evidencias/tenant-prueba/cctv/20261115_clip.mp4",
        sha256_original=sha_orig,
        bytes_originales=contenido,
    )

    res = engine.generar_preview(objeto, formato_destino="WEBP")

    assert res["integro"] is True
    assert res["sha256_original"] == sha_orig
    assert objeto.preview_gcs_uri == "/previews/obj-cctv-001.webp"
    assert objeto.preview_formato == "WEBP"
    assert objeto.ahorro_peso_pct is not None and objeto.ahorro_peso_pct > 0
    # Invariante clave: los bytes del original y su hash siguen inalterados bit a bit
    assert hashlib.sha256(objeto.bytes_originales).hexdigest() == sha_orig


def test_prohibicion_sobrescribir_original_con_preview():
    """Rechaza con 409 BOVEDA_ALTERACION_ORIGINAL_PROHIBIDA cualquier intento de sobrescribir original_gcs_uri."""
    engine = ForensicPreviewEngine()
    contenido = b"EVIDENCIA_FOTOGRAFICA_ORIGINAL"
    sha_orig = hashlib.sha256(contenido).hexdigest()
    uri_orig = "gs://boveda-evidencias/tenant-prueba/fotos/foto_001.raw"

    objeto = ObjetoCustodia(
        id="obj-foto-001",
        tenant_id="tenant-prueba",
        original_gcs_uri=uri_orig,
        sha256_original=sha_orig,
        bytes_originales=contenido,
    )

    with pytest.raises(ErrorNegocio) as exc:
        engine.generar_preview(objeto, formato_destino="WEBP", destino_gcs_uri=uri_orig)

    assert exc.value.code == errores.BOVEDA_ALTERACION_ORIGINAL_PROHIBIDA
    assert exc.value.status_code == 409


def test_verificacion_integridad_forense():
    """R2: verificar_integridad confirma el SHA-256 exacto del original."""
    engine = ForensicPreviewEngine()
    contenido = b"EVIDENCIA_DOCUMENTO_FIRMADO"
    sha_orig = hashlib.sha256(contenido).hexdigest()

    objeto = ObjetoCustodia(
        id="obj-doc-001",
        tenant_id="tenant-prueba",
        original_gcs_uri="gs://boveda-evidencias/tenant-prueba/docs/doc_001.pdf",
        sha256_original=sha_orig,
        bytes_originales=contenido,
    )

    verif_ok = engine.verificar_integridad(objeto)
    assert verif_ok["integro"] is True
    assert verif_ok["sha256_calculado"] == sha_orig

    # Alterar un solo byte para comprobar detección forense
    objeto_corrupto = ObjetoCustodia(
        id="obj-doc-001",
        tenant_id="tenant-prueba",
        original_gcs_uri="gs://boveda-evidencias/tenant-prueba/docs/doc_001.pdf",
        sha256_original=sha_orig,
        bytes_originales=contenido + b"_CORRUPCION",
    )
    verif_bad = engine.verificar_integridad(objeto_corrupto)
    assert verif_bad["integro"] is False
    assert verif_bad["sha256_calculado"] != sha_orig
