+++
id = "BOV-02"
titulo = "Bóveda Dual en Google Cloud Storage (short-ttl Standard vs long-retention Autoclass WORM) e ingesta Direct-to-GCS"
ola = "D"
estado = "pendiente"
sala = "boveda_cloud"
depende_de = ["BOV-01"]
propiedad = ["features/boveda_cloud/services/__init__.py", "features/boveda_cloud/services/gcs_dual_vault_engine.py", "features/boveda_cloud/boveda_cloud_service.py#BOV-02", "features/boveda_cloud/domain/errores.py#BOV-02", "features/boveda_cloud/routes/boveda_objetos_routes.py", "app_core/pasillo/boveda_cloud.py#BOV-02", "tests/test_bov02_gcs_dual_vault.py"]
arbitro = "pytest tests/test_bov02_gcs_dual_vault.py + suite completa + vigilantes"
rastros = ["¤boveda-cloud", "¤conservacion", "¤evidencias"]
+++
# BOV-02 · Bóveda Dual en Google Cloud Storage (short-ttl Standard vs long-retention Autoclass WORM) e ingesta Direct-to-GCS

## Entrega
- Motor `features/boveda_cloud/services/gcs_dual_vault_engine.py` que clasifica cada objeto según su plazo normativo de retención: si `retencion_dias < 30` (ej. videovigilancia a 15 días), lo asigna al bucket `lopdp360-vault-short-ttl` (`storage_class='STANDARD'`, `autoclass=False`, `lifecycle_delete_days=retencion_dias`); si `retencion_dias >= 30`, lo asigna a `lopdp360-vault-long-retention` (`autoclass=True`, `object_lock_worm=True`).
- Generador de `Signed URLs V4` para subida y descarga directa (`PUT`/`GET`) acotada al prefijo `{tenant_id}/{categoria}/{objeto_id}` sin pasar los bytes del archivo por la memoria de FastAPI.

## Pruebas
- `pytest tests/test_bov02_gcs_dual_vault.py` comprueba el enrutamiento determinista entre `short-ttl` (sin Autoclass) y `long-retention` (con Autoclass + WORM) y el aislamiento de prefijos por `tenant_id` (`INV_LOPDP_VAULT_TIER_SEPARATION`, `INV_LOPDP_DIRECT_TO_GCS_ZERO_RAM_STREAM`).
