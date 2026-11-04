# GCP-04 · Base de Datos Cloud SQL PostgreSQL 16 y Enrutamiento Cloud Load Balancing
`¤sdd` `¤cloud-run-perf` `¤seguridad-tenant` `¤ci-cd`

## 1. Datos

Configuración de infraestructura `CloudSQLSpec` (`database_version: 'POSTGRES_16'`, `tier: 'db-custom-2-7680'`, `backup_enabled: true`, `point_in_time_recovery: true`, `authorized_networks: []`, `require_ssl: true`).

## 2. API

- Script CLI `python scripts/verificar_cloudsql_conexion.py --dsn <DSN_PRODUCCION>` -> Exit Code 0 si el rol es `lopdp_app` y valida RLS.

## 3. Reglas

- **R1 · Independencia total en base de datos (`INV_LOPDP_CLOUD_SQL_AUTOPROXY`).** La base de datos de producción reside en Google Cloud SQL con backups automáticos y aislamiento de red privada VPC.
- **R2 · Enrutamiento unificado bajo dominio corporativo.** Cloud Load Balancing redirige `/api/*` hacia el servicio `lopdp360-api` y todas las demás rutas hacia `lopdp360-web`, eliminando discrepancias de CORS entre frontend y backend.

## 4. Interfaz

Operación de infraestructura; sin pantallas de aplicación.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** la definición de Cloud SQL en `cloud_sql_instance.yaml`, **cuando** se valida en la prueba, **entonces** exige versión PostgreSQL 16 con backups diarios obligatorios y SSL forzado. | `test_cloud_sql_especificacion_segura` |
| **Dado** el manifiesto de Cloud Load Balancing, **cuando** se evalúa el mapa de URLs, **entonces** mapea `/api/v1/*` al backend Cloud Run y el resto al frontend. | `test_load_balancer_enrutamiento_unificado` |

## 6. Trazabilidad

- PRD §8.4, §9 criterio 25 e invariante `INV_LOPDP_CLOUD_SQL_AUTOPROXY`.
