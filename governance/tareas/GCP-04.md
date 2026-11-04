+++
id = "GCP-04"
titulo = "Migración de Base de Datos y Enrutamiento Unificado: Cloud SQL PostgreSQL 16 con RLS forzado y Cloud Load Balancing"
ola = "C"
estado = "pendiente"
sala = "pasillo_central, operaciones"
depende_de = ["GCP-01", "SEC-10"]
propiedad = ["governance/operaciones/MIGRACION_CLOUDSQL_POSTGRES.md", "governance/operaciones/cloud_sql_instance.yaml", "governance/operaciones/cloud_load_balancer.yaml", "scripts/verificar_cloudsql_conexion.py", "tests/test_gcp04_cloudsql_migration_cutover.py"]
arbitro = "pytest tests/test_gcp04_cloudsql_migration_cutover.py + suite completa + vigilantes"
rastros = ["¤cloud-run-perf", "¤seguridad-tenant", "¤ci-cd"]
+++
# GCP-04 · Migración de Base de Datos y Enrutamiento Unificado: Cloud SQL PostgreSQL 16 con RLS forzado y Cloud Load Balancing

## Entrega
- Guía de migración DDL y datos `governance/operaciones/MIGRACION_CLOUDSQL_POSTGRES.md` con el procedimiento seguro de corte de Neon a Cloud SQL PostgreSQL 16.
- Definición `governance/operaciones/cloud_sql_instance.yaml` con parámetros de base de datos (PostgreSQL 16, flags de seguridad, backups automáticos de Google y usuario `lopdp_app` con `FORCE ROW LEVEL SECURITY`).
- Manifiesto `governance/operaciones/cloud_load_balancer.yaml` para enrutamiento unificado de dominio bajo una sola IP con Cloud Armor WAF y certificados SSL administrados de Google.
- Script de verificación notarial `scripts/verificar_cloudsql_conexion.py` para validar conectividad con rol `lopdp_app` y RLS forzado.

## Pruebas
- `pytest tests/test_gcp04_cloudsql_migration_cutover.py` comprueba que la especificación de Cloud SQL exige PostgreSQL 16, que `lopdp_app` carece de `BYPASSRLS`, y que el Load Balancer enruta `/api/*` al backend y `/*` al frontend (`INV_LOPDP_CLOUD_SQL_AUTOPROXY`).
