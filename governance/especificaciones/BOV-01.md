# BOV-01 · Paquetes Comerciales de Bóveda Cloud y Control de Cuotas Multi-Tenant
`¤sdd` `¤boveda-cloud` `¤seguridad-tenant` `¤adpa`

## 1. Datos

Tabla `boveda_suscripciones_tenant` (RLS forzado por `tenant_id`):
- `id` (UUID PK), `tenant_id` (VARCHAR(64) UNIQUE NOT NULL), `paquete_codigo` (`'STARTER_50GB' | 'PRO_250GB' | 'ENTERPRISE_1TB'`), `cuota_almacenamiento_bytes` (BIGINT NOT NULL), `uso_almacenamiento_bytes` (BIGINT NOT NULL DEFAULT 0), `cuota_egress_mensual_bytes` (BIGINT NOT NULL), `uso_egress_mensual_bytes` (BIGINT NOT NULL DEFAULT 0), `estado` (`'ACTIVA' | 'CUOTA_EXCEDIDA' | 'SUSPENDIDA'`).

## 2. API

- `GET /api/v1/boveda-cloud/suscripcion` -> `200 OK`
- `POST /api/v1/boveda-cloud/suscripcion` -> `201 Created`
- `POST /api/v1/boveda-cloud/suscripcion/validar-consumo` -> `200 OK` | `409 Conflict`

## 3. Reglas

- **R1 · Blindaje de margen contra exceso de Egress.** Antes de emitir una URL firmada de descarga o visualización, `boveda_cloud_service` comprueba que `uso_egress_mensual_bytes + bytes_solicitados <= cuota_egress_mensual_bytes`; si lo supera, lanza `ErrorNegocio('BOVEDA_CUOTA_EGRESS_EXCEDIDA')` (409).
- **R2 · Límite estricto de almacenamiento contratado.** Ninguna subida nueva se autoriza si supera `cuota_almacenamiento_bytes` (`BOVEDA_CUOTA_ALMACENAMIENTO_EXCEDIDA`, 409).

## 4. Interfaz

Pantalla `frontend/src/components/pantallas/BOV-01.tsx` con barras de uso de almacenamiento (GB), cuota de Egress mensual y sello de certificaciones ISO 27001 / ISO 27701 / SOC 2 de la Bóveda.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un inquilino con paquete `STARTER_50GB` y cuota de Egress agotada, **cuando** solicita descargar un objeto adicional, **entonces** el servicio responde 409 `BOVEDA_CUOTA_EGRESS_EXCEDIDA`. | `test_bloqueo_preventivo_cuota_egress_excedida` |
| **Dado** dos organizaciones A y B con suscripciones de Bóveda, **cuando** B consulta `/api/v1/boveda-cloud/suscripcion`, **entonces** solo recibe su propia suscripción por aislamiento RLS. | `test_boveda_suscripcion_aislamiento_rls` |

## 6. Trazabilidad

- PRD §8.1, §7.1 (`boveda_cloud`) e invariante `INV_LOPDP_TENANT_BULKHEAD`.
