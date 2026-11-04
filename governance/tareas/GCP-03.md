+++
id = "GCP-03"
titulo = "Migración del Frontend a Cloud Run: empaquetado standalone de Next.js, Dockerfile multi-stage y proxy regional"
ola = "C"
estado = "pendiente"
sala = "frontend, operaciones"
depende_de = ["GCP-01", "FE-21", "FE-22"]
propiedad = ["frontend/Dockerfile.cloudrun", "frontend/next.config.cloudrun.ts", "governance/operaciones/cloudrun_frontend_service.yaml", "tests/test_gcp03_frontend_cloudrun.py"]
arbitro = "pytest tests/test_gcp03_frontend_cloudrun.py + suite completa + vigilantes"
rastros = ["¤cloud-run-perf", "¤frontend-ide", "¤seguridad"]
+++
# GCP-03 · Migración del Frontend a Cloud Run: empaquetado standalone de Next.js, Dockerfile multi-stage y proxy regional

## Entrega
- Configuración `frontend/next.config.cloudrun.ts` con `output: 'standalone'` y trazabilidad de activos estáticos para Cloud Run regional en `us-east1`.
- Manifiesto `frontend/Dockerfile.cloudrun` multi-stage con imagen base Node.js Alpine/Distroless, usuario `nextjs` sin privilegios (UID 1001) y exclusión de `node_modules` de desarrollo.
- Definición de servicio `governance/operaciones/cloudrun_frontend_service.yaml` con variables de conexión interna hacia el backend `lopdp360-api` vía VPC Connector de Google Cloud.

## Pruebas
- `pytest tests/test_gcp03_frontend_cloudrun.py` comprueba que la configuración `next.config.cloudrun.ts` especifica `output: 'standalone'`, que el Dockerfile define usuario non-root y que el servicio de Cloud Run expone el puerto 3000 con health check (`INV_LOPDP_STANDALONE_FRONTEND_CONTAINER`).
