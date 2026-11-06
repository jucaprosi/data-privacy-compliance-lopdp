# GCP-01 · Chasis Cloud Run ASGI y Sesión RLS en 1 RTT con PgBouncer
`¤sdd` `¤cloud-run-perf` `¤seguridad-tenant` `¤adpa`

## 1. Datos

Parámetros de sesión transaccional PostgreSQL `app.current_tenant_id` y `app.current_user_id` fijados en una única consulta `SELECT set_config('app.current_tenant_id', :tid, true), set_config('app.current_user_id', :uid, true)` y configuración de motor `prepare_threshold=None`.

## 2. API

- `GET /api/v1/health/cloudrun` (vía `gcp_runtime.py`) -> `200 OK` con telemetría de modo ASGI (`uvloop`), estado de pooler y ADC.

## 3. Reglas

- **R1 · Fijación RLS en un solo viaje de red (`INV_LOPDP_SINGLE_RTT_RLS_PGBOUNCER`).** La sesión de base de datos ejecuta una única sentencia SQL para fijar simultáneamente tenant y usuario antes de cualquier consulta de negocio.
- **R2 · Compatibilidad PgBouncer en modo transaccional.** Cuando el DSN corresponde a un pooler transaccional, `create_async_engine` desactiva el umbral de sentencias preparadas (`prepare_threshold=None`) para impedir `DuplicatePreparedStatementError`.
- **R3 · Inicialización perezosa en Cloud Run.** Los clientes de Google Cloud Storage, Vertex AI y Cloud DLP se instancian al primer uso y no durante el arranque del proceso.

## 4. Interfaz

No introduce pantallas de usuario; provee el chasis de ejecución para Cloud Run y worktrees locales autenticados por ADC.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un contexto autenticado con `tenant_id` y `user_id`, **cuando** se abre la sesión en `app_core/db/session.py#GCP-01`, **entonces** se emite una sola sentencia SQL con ambos `set_config` y ambos valores quedan activos en la transacción. | `test_rls_set_config_un_solo_viaje_sql` |
| **Dado** una cadena de conexión con pooler transaccional, **cuando** `gcp_runtime` construye los argumentos de motor, **entonces** `prepare_threshold` es `None` y el contenedor declara `uvicorn` con `uvloop` y `--concurrency=80`. | `test_pgbouncer_prepare_threshold_y_manifiesto_cloudrun` |

## 6. Trazabilidad

- PRD §8.4, §9 criterio 23 e invariante `INV_LOPDP_SINGLE_RTT_RLS_PGBOUNCER`.
