+++
id = "GCP-01"
titulo = "Chasis Cloud Run ASGI, sesión RLS en 1 RTT con PgBouncer y Secret Manager ADC"
ola = "C"
estado = "pendiente"
sala = "pasillo_central, operaciones"
depende_de = ["RM-00", "RM-02", "ENT-02", "ADPA-02"]
propiedad = ["app_core/db/session.py#GCP-01", "app_core/cloud/__init__.py", "app_core/cloud/gcp_runtime.py", "governance/operaciones/Dockerfile.cloudrun", "governance/operaciones/cloudrun_service.yaml", "tests/test_gcp01_cloudrun_rls_single_rtt.py", "tests/test_database_rls.py#GCP-01"]
arbitro = "pytest tests/test_gcp01_cloudrun_rls_single_rtt.py + suite completa + vigilantes"
rastros = ["¤cloud-run-perf", "¤seguridad-tenant", "¤adpa"]
+++
# GCP-01 · Chasis Cloud Run ASGI, sesión RLS en 1 RTT con PgBouncer y Secret Manager ADC

**Ampliación 2026-11-07 (Tech Lead):** `tests/test_database_rls.py:88` (`test_fijar_contexto_rls_enlaza_el_tenant_como_parametro`, de RM-02, ya hecha) exigía dos sentencias (`[{"tid"}, {"uid"}]`), lo que contradice `INV_LOPDP_SINGLE_RTT_RLS_PGBOUNCER`. GCP-01 la ajusta a una sola sentencia con `{"tid", "uid"}` y conserva la comprobación de que el tenant va como parámetro, sin interpolar.

## Entrega
- Sección `#GCP-01` en `app_core/db/session.py` que fusiona `set_config('app.current_tenant_id', :tid, true)` y `set_config('app.current_user_id', :uid, true)` en una única sentencia SQL por transacción (1 RTT) y configura `connect_args={'prepare_threshold': None}` cuando la URL de conexión opera tras PgBouncer (`-pooler` o Cloud SQL Proxy).
- Módulo `app_core/cloud/gcp_runtime.py` con inicialización perezosa (*Lazy Init*) de clientes de Google Cloud y lectura de secretos mediante Application Default Credentials (ADC) sin requerir archivos `.env` duplicados en worktrees.
- Manifiestos `governance/operaciones/Dockerfile.cloudrun` (imagen multi-stage con `uv`, usuario sin privilegios y `uvicorn main:app --workers 1 --loop uvloop --http httptools`) y `governance/operaciones/cloudrun_service.yaml` (`--cpu-boost`, `--concurrency=80`).

## Pruebas
- `pytest tests/test_gcp01_cloudrun_rls_single_rtt.py` comprueba que el contexto RLS fija `app.current_tenant_id` y `app.current_user_id` en una sola ejecución SQL y que `prepare_threshold` queda en `None` bajo modo pooler (`INV_LOPDP_SINGLE_RTT_RLS_PGBOUNCER`).
