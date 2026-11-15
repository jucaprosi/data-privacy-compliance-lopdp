+++
id = "CI-28b"
titulo = "Comprobación de la revisión de Alembic en todas las cabezas"
ola = "backlog"
estado = "hecha"
sala = "gobernanza"
depende_de = ["CI-18", "CI-28", "GCP-04"]
propiedad = ["scripts/verificar_cloudsql_conexion.py", "tests/test_gcp04_cloudsql_migration_cutover.py"]
arbitro = "pytest tests/test_gcp04_cloudsql_migration_cutover.py tests/test_alembic_cabeza_por_sala.py (con TEST_DATABASE_URL de PostgreSQL 16) + python scripts/generar_indice_tareas.py --verificar; mutación m1"
rastros = ["¤arbitro", "¤revision-alembic"]
+++

# CI-28b · Comprobación de la revisión de Alembic en todas las cabezas

**Contrato:** `governance/especificaciones/CI-28b.md` (manda sobre esta ficha).

**Origen.** Pedido del CTO (2026-11-15). Con una cabeza por sala (CI-28), `comprobar_revision` sigue con la comprobación de una sola cabeza. La segunda cabeza (CCTV-01, #825) hace fallar `test_verificador_contra_postgres_16_con_lopdp_app`.

## Entrega
- `comprobar_revision` usa `motivo_revision_por_conjuntos`.
- `motivo_revision` y sus pruebas desaparecen; las pruebas CI-18 de la comprobación 5 se reescriben por conjuntos.
- Docstring: «0 si la base está en todas las cabezas del repositorio; 1 si no.»

## Límites
- Sin migración. Ningún workflow ni arnés llama a `motivo_revision` (medido en `origin/main` 9ad68eb6).
