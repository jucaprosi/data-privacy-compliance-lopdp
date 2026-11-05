+++
id = "GCP-06"
titulo = "Escalado acotado de Cloud Run, Cloud CDN para activos estáticos, caché de lectura por tenant y prueba de carga reproducible"
ola = "C"
estado = "pendiente"
sala = "pasillo_central, operaciones"
depende_de = ["GCP-01", "GCP-03", "GCP-04"]
propiedad = ["app_core/cache/__init__.py", "app_core/cache/cache_lectura.py", "governance/operaciones/cloudrun_escalado.yaml", "governance/operaciones/cloud_cdn.yaml", "scripts/prueba_carga.py", "tests/test_gcp06_escalabilidad_cache.py"]
arbitro = "pytest tests/test_gcp06_escalabilidad_cache.py + suite completa + vigilantes"
rastros = ["¤cloud-run-perf", "¤seguridad-tenant"]
+++
# GCP-06 · Escalado acotado de Cloud Run, Cloud CDN para activos estáticos, caché de lectura por tenant y prueba de carga reproducible

## Entrega
- Manifiesto `governance/operaciones/cloudrun_escalado.yaml` con `minScale`, `maxScale` y `containerConcurrency` por servicio (frontend, backend, `vault_worker`) y el dimensionamiento del pool de PgBouncer frente al límite de conexiones de Cloud SQL.
- Manifiesto `governance/operaciones/cloud_cdn.yaml` que activa Cloud CDN solo para `/_next/static/*` en el balanceador de `GCP-04`.
- Módulo `app_core/cache/cache_lectura.py` con caché de lectura en Memorystore cuya clave incluye siempre `tenant_id` y versión del recurso, para catálogos y paquetes normativos, con invalidación al cambiar la versión.
- Script `scripts/prueba_carga.py` que ejecuta un escenario reproducible de 1 000 usuarios concurrentes contra un entorno de prueba y guarda el informe (p50, p95, errores); con `--verificar` contrasta el último informe con el objetivo p95 de lectura < 800 ms.

## Pruebas
- `pytest tests/test_gcp06_escalabilidad_cache.py` comprueba que cada servicio declara sus límites de escalado, que el pool cabe en Cloud SQL, que Cloud CDN solo cubre activos estáticos, que las respuestas con datos de organización llevan `Cache-Control: no-store` y que la clave de caché incluye `tenant_id` (`INV_CLOUD_RUN_BOUNDED_AUTOSCALING`, `INV_EDGE_CACHE_PUBLIC_STATIC_ONLY`).
