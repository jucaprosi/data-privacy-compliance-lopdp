# DLP-01 · Descubrimiento Muestreado de Datos Sensibles (Cloud DLP Sampling + Módulo 10)
`¤sdd` `¤dlp-muestreo` `¤rat` `¤seguridad-tenant`

## 1. Datos

Tabla `dlp_escaneos_muestreados` (RLS forzado por `tenant_id`):
- `id` (UUID PK), `tenant_id` (VARCHAR(64) NOT NULL), `fuente_nombre` (VARCHAR(160) NOT NULL), `limite_muestra` (INTEGER NOT NULL DEFAULT 250 CHECK (`limite_muestra` <= 1000)), `infotypes_detectados` (JSONB NOT NULL), `contiene_datos_sensibles` (BOOLEAN NOT NULL), `actividad_rat_id` (VARCHAR(64) NULL).

## 2. API

- `POST /api/v1/dlp-discovery/escanear-muestra` -> `201 Created`
- `GET /api/v1/dlp-discovery/escaneos` -> `200 OK`

## 3. Reglas

- **R1 · Muestreo acotado y lista blanca de infoTypes.** Ningún escaneo procesa más de `limite_muestra` registros ni activa `infoTypes` globales innecesarios; solo evalúa `EC_CEDULA_MOD10`, `EC_RUC`, `EMAIL`, `PHONE` y `SALUD`.
- **R2 · Cero persistencia del dato personal hallado.** En la base de datos solo se guarda el tipo de hallazgo y el conteo estadístico, nunca la cédula ni el nombre encontrados (`INV_LOPDP_DLP_ECUADORIAN_CEDULA_MODULO10`).

## 4. Interfaz

Pantalla `frontend/src/components/pantallas/DLP-01.tsx` para lanzar escaneos muestreados y vincular las categorías detectadas con una actividad del RAT.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una muestra con cédulas ecuatorianas válidas (Módulo 10) y correos electrónicos, **cuando** se ejecuta `escanear-muestra`, **entonces** registra `EC_CEDULA_MOD10` y `EMAIL` en `infotypes_detectados` sin guardar ningún número de cédula en la tabla. | `test_escaneo_muestreado_detecta_cedula_sin_persistir_pii` |
| **Dado** una solicitud con `limite_muestra = 50000`, **cuando** se valida en la compuerta, **entonces** se rechaza con 422 `DLP_MUESTRA_EXCEDE_LIMITE`. | `test_rechazo_muestra_excesiva_dlp` |

## 6. Trazabilidad

- PRD §8.4, §7.1 (`dlp_discovery`) e invariante `INV_LOPDP_DLP_ECUADORIAN_CEDULA_MODULO10`.
