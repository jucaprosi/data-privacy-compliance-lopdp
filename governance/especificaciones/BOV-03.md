# BOV-03 · Carril Forense Dual (Original SHA-256 Intacto + Preview WebP/AVIF/WebM)
`¤sdd` `¤boveda-cloud` `¤evidencias` `¤adpa`

## 1. Datos

Campos en `boveda_objetos_custodia`: `original_gcs_uri` (TEXT NOT NULL), `sha256_original` (CHAR(64) NOT NULL), `preview_gcs_uri` (TEXT NULL), `preview_formato` (`'WEBP' | 'AVIF' | 'WEBM' | NULL`), `ahorro_peso_pct` (NUMERIC(5,2) NULL).

## 2. API

- `POST /api/v1/boveda-cloud/objetos/{objeto_id}/generar-preview` -> `200 OK`
- `GET /api/v1/boveda-cloud/objetos/{objeto_id}/verificar-integridad` -> `200 OK`

## 3. Reglas

- **R1 · Inmutabilidad del archivo original (`INV_LOPDP_FORENSIC_ORIGINAL_HASH`).** El proceso de generación de vistas previas lee `original_gcs_uri` en modo solo lectura y escribe el resultado comprimido en `preview_gcs_uri` (prefijo `/previews/`); intentar escribir sobre `original_gcs_uri` lanza `ErrorNegocio('BOVEDA_ALTERACION_ORIGINAL_PROHIBIDA')` (409).
- **R2 · Verificación probatoria.** El endpoint `verificar-integridad` recalcula el `SHA-256` del original y confirma coincidencia exacta con el sello inicial.

## 4. Interfaz

Componente `frontend/src/components/pantallas/BOV-03.tsx` con previsualización rápida en `WebP`/`WebM` e insignia verde de verificación `SHA-256` del original.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una evidencia fotográfica o de video subida a la Bóveda, **cuando** se genera su vista previa en formato `WEBP` o `WEBM`, **entonces** `preview_gcs_uri` apunta al derivado ligero mientras `original_gcs_uri` mantiene exactamente el mismo hash `SHA-256`. | `test_carril_forense_dual_preserva_sha256_original` |
| **Dado** un intento de reemplazar `original_gcs_uri` por la versión comprimida, **cuando** se invoca el motor, **entonces** se rechaza con 409 `BOVEDA_ALTERACION_ORIGINAL_PROHIBIDA`. | `test_prohibicion_sobrescribir_original_con_preview` |

## 6. Trazabilidad

- PRD §8.2, §9 criterio 19 e invariante `INV_LOPDP_FORENSIC_ORIGINAL_HASH`.
