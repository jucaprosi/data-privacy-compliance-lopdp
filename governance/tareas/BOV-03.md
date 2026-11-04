+++
id = "BOV-03"
titulo = "Carril Forense Dual: custodia del original intacto SHA-256 y derivados de previsualización WebP/AVIF/WebM"
ola = "D"
estado = "pendiente"
sala = "boveda_cloud"
depende_de = ["BOV-02"]
propiedad = ["features/boveda_cloud/services/forensic_preview_engine.py", "features/boveda_cloud/boveda_cloud_service.py#BOV-03", "features/boveda_cloud/domain/errores.py#BOV-03", "app_core/pasillo/boveda_cloud.py#BOV-03", "frontend/src/components/pantallas/BOV-03.tsx", "frontend/src/components/pantallas/index.tsx#BOV-03", "tests/test_bov03_forensic_preview.py"]
arbitro = "pytest tests/test_bov03_forensic_preview.py + suite completa + vigilantes"
rastros = ["¤boveda-cloud", "¤evidencias", "¤adpa"]
+++
# BOV-03 · Carril Forense Dual: custodia del original intacto SHA-256 y derivados de previsualización WebP/AVIF/WebM

## Entrega
- Motor `features/boveda_cloud/services/forensic_preview_engine.py` que preserva inalterado el objeto original con su hash `sha256_original` para inspecciones de la SPDP y registra por separado la ruta del derivado optimizado (`preview_uri` en `.webp`, `.avif` o `.webm`) para carga instantánea en la UI.
- Validador de integridad forense que rechaza con `BOVEDA_ALTERACION_ORIGINAL_PROHIBIDA` (409) cualquier intento de sobrescribir el blob original con un archivo recomprimido.
- Visor `frontend/src/components/pantallas/BOV-03.tsx` que carga por defecto la vista previa ligera (`WebP`/`WebM`) y ofrece descarga verificada del original con comprobación `SHA-256`.

## Pruebas
- `pytest tests/test_bov03_forensic_preview.py` demuestra que tras generar la vista previa `.webp`/`.webm`, el `sha256_original` y los bytes del documento primario permanecen idénticos bit a bit (`INV_LOPDP_FORENSIC_ORIGINAL_HASH`).
