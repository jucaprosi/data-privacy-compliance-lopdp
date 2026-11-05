+++
id = "GCP-07"
titulo = "Despliegue progresivo por revisiones de Cloud Run con reversión por SLO y verificador de migraciones compatibles (expand/contract)"
ola = "C"
estado = "pendiente"
sala = "operaciones, pruebas"
depende_de = ["GCP-03", "GCP-04", "OPS-07"]
propiedad = ["governance/operaciones/despliegue_progresivo.yaml", "scripts/verificar_migracion_compatible.py", "tests/test_gcp07_despliegue_progresivo.py"]
arbitro = "pytest tests/test_gcp07_despliegue_progresivo.py + suite completa + vigilantes"
rastros = ["¤cloud-run-perf", "¤ci-cd"]
+++
# GCP-07 · Despliegue progresivo por revisiones de Cloud Run con reversión por SLO y verificador de migraciones compatibles (expand/contract)

## Entrega
- Manifiesto `governance/operaciones/despliegue_progresivo.yaml` con los escalones de tráfico de cada servicio de Cloud Run (10 % → 50 % → 100 %), la duración de observación por escalón y la condición de reversión ligada a las alertas de disponibilidad y errores de `OPS-07`.
- Verificador `scripts/verificar_migracion_compatible.py` que analiza las migraciones Alembic nuevas y rechaza, en un mismo paso, borrar o renombrar columnas o tablas que la revisión en servicio aún usa (patrón *expand/contract*).

## Pruebas
- `pytest tests/test_gcp07_despliegue_progresivo.py` comprueba que el manifiesto define escalones crecientes que terminan en 100 % y una condición de reversión, y que el verificador rechaza una migración destructiva de ejemplo y acepta una aditiva (`INV_PROGRESSIVE_DELIVERY_EXPAND_CONTRACT`).
