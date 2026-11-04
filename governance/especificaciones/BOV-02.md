# BOV-02 · Enrutador de Bóveda Dual GCS y Signed URLs V4 Direct-to-GCS
`¤sdd` `¤boveda-cloud` `¤conservacion` `¤evidencias`

## 1. Datos

Registro `boveda_objetos_custodia` en `features/boveda_cloud/models.py` (`id`, `tenant_id`, `bucket_destino` en `{'lopdp360-vault-short-ttl', 'lopdp360-vault-long-retention'}`, `storage_class`, `autoclass_activo` BOOL, `worm_lock_hasta` TIMESTAMPTZ NULL, `retencion_dias` INT, `sha256_original` VARCHAR(64)).

## 2. API

- `POST /api/v1/boveda-cloud/objetos/url-subida-firmada` -> `201 Created`
- `POST /api/v1/boveda-cloud/objetos/{objeto_id}/url-descarga-firmada` -> `200 OK`

## 3. Reglas

- **R1 · Separación estricta de tiers (`INV_LOPDP_VAULT_TIER_SEPARATION`).** Todo objeto con `retencion_dias < 30` va obligatoriamente a `lopdp360-vault-short-ttl` con `autoclass_activo = False`; todo objeto con `retencion_dias >= 30` va a `lopdp360-vault-long-retention` con `autoclass_activo = True` y `worm_lock_hasta`.
- **R2 · Subida directa sin tránsito por RAM (`INV_LOPDP_DIRECT_TO_GCS_ZERO_RAM_STREAM`).** La API devuelve únicamente la URL firmada V4 con restricción de `Content-Length` y `X-Goog-Content-Sha256`.

## 4. Interfaz

Integrado en los flujos de carga directa de evidencias, documentos y clips de cámaras.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una solicitud de carga con `retencion_dias = 15` (videovigilancia), **cuando** el motor resuelve el destino, **entonces** selecciona `lopdp360-vault-short-ttl`, desactiva Autoclass y fija borrado automático al día 15. | `test_enrutamiento_short_ttl_sin_autoclass_15_dias` |
| **Dado** una solicitud de carga con `retencion_dias = 1825` (5 años para contrato DPA), **cuando** el motor resuelve el destino, **entonces** selecciona `lopdp360-vault-long-retention` con Autoclass y retención WORM. | `test_enrutamiento_long_retention_autoclass_worm` |

## 6. Trazabilidad

- PRD §8.2, §9 criterios 20 y 22 e invariantes `INV_LOPDP_VAULT_TIER_SEPARATION` e `INV_LOPDP_DIRECT_TO_GCS_ZERO_RAM_STREAM`.
