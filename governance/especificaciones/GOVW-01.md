# GOVW-01 · Satélite Cloud Run en Go para Ingesta Eventarc, Hashing SHA-256 y Purga Masiva
`¤sdd` `¤motor-go-hibrido` `¤boveda-cloud` `¤conservacion`

## 1. Datos

Payloads firmados `VaultIngestEvent` (`tenant_id`, `object_key`, `size_bytes`, `sha256_hex`, `bucket`) y `VaultPurgeBatchResult` (`politica_id`, `objetos_eliminados_count`, `acta_lote_sha256`, `timestamp_utc`).

## 2. API

- `POST /internal/v1/go-vault-worker/eventarc-ingest` (en `services_go/vault_worker/main.go`) -> `200 OK`
- `POST /internal/v1/go-vault-worker/execute-purge-batch` -> `200 OK`

## 3. Reglas

- **R1 · Streaming en memoria constante (`INV_LOPDP_DIRECT_TO_GCS_ZERO_RAM_STREAM`).** El worker en Go procesa lectores por bloques de 64 KB (`io.Copy` hacia `sha256.New()`) sin cargar el archivo completo en memoria.
- **R2 · Autenticación mutua entre satélite Go y Core Python.** Todo callback hacia el pasillo `app_core/pasillo/go_vault_worker.py#GOVW-01` lleva firma HMAC-SHA256 verificada; si la firma es inválida, se rechaza con 401.

## 4. Interfaz

Servicio de infraestructura backend serverless en Cloud Run (`min-instances=0`); sin pantalla propia.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un evento de subida en GCS procesado por el contrato del satélite Go, **cuando** notifica al pasillo `go_vault_worker.py#GOVW-01` con firma válida, **entonces** sella el `sha256_hex` y actualiza el consumo de cuota del tenant. | `test_contrato_ingesta_eventarc_go_vault_worker` |
| **Dado** un lote de objetos vencidos enviado a purga masiva, **cuando** el worker en Go completa el barrido, **entonces** devuelve `acta_lote_sha256` determinista para el certificado de destrucción. | `test_contrato_purga_masiva_go_vault_worker` |

## 6. Trazabilidad

- PRD §8.2, §8.4, §7.1 (`go_vault_worker`) e invariante `INV_LOPDP_DIRECT_TO_GCS_ZERO_RAM_STREAM`.
