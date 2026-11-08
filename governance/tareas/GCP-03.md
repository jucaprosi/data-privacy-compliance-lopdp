+++
id = "GCP-03"
titulo = "Migración del Frontend a Cloud Run: empaquetado standalone de Next.js, Dockerfile multi-stage y proxy regional"
ola = "C"
estado = "en_curso"
sala = "frontend, operaciones"
depende_de = ["GCP-01", "FE-21", "FE-22"]
propiedad = ["frontend/Dockerfile.cloudrun", "frontend/next.config.cloudrun.ts", "governance/operaciones/cloudrun_frontend_service.yaml", "tests/test_gcp03_frontend_cloudrun.py", "tests/test_gcp03_app_env_por_servicio.py"]
arbitro = "pytest tests/test_gcp03_frontend_cloudrun.py tests/test_gcp03_app_env_por_servicio.py + suite completa + vigilantes; la imagen de producción sirve robots.txt con Allow: /"
rastros = ["¤cloud-run-perf", "¤frontend-ide", "¤seguridad"]
+++
# GCP-03 · Migración del Frontend a Cloud Run: empaquetado standalone de Next.js, Dockerfile multi-stage y proxy regional

## Entrega
- Configuración `frontend/next.config.cloudrun.ts` con `output: 'standalone'` y trazabilidad de activos estáticos para Cloud Run regional en `us-east1`.
- Manifiesto `frontend/Dockerfile.cloudrun` multi-stage con imagen base Node.js Alpine/Distroless, usuario `nextjs` sin privilegios (UID 1001) y exclusión de `node_modules` de desarrollo.
- Definición de servicio `governance/operaciones/cloudrun_frontend_service.yaml` con variables de conexión interna hacia el backend `lopdp360-api` vía VPC Connector de Google Cloud.
- **Una sola imagen del frontend por digest** (§5.5, decisión del CTO del 2026-11-07, nace de EP-02). El Dockerfile no recibe el entorno como argumento de compilación ni usa `NEXT_PUBLIC_APP_ENV`. `APP_ENV` se fija **por servicio** en Cloud Run, igual que en el backend, y el frontend la lee en el servidor en tiempo de ejecución (EP-02). Sin `APP_ENV`, o con un valor inválido, robots responde `disallow`.
- `cloudrun_frontend_service.yaml` declara `APP_ENV` por entorno: `production`, `pruebas` o `demo`.

- **Login en la nube (dato del CTO, 2026-11-07):** Cloud Run no tiene `GOOGLE_CLIENT_ID`, así que `/mis-organizaciones` con Bearer responde 503 y nadie puede iniciar sesión. Cuando el propietario lo configure, tiene que estar también en `deploy-gcp.yml`, porque su `--set-env-vars` reemplaza todas las variables y la borraría en la publicación siguiente. Lo mismo vale para `APP_ENV` y cualquier otra variable por servicio.

## Pruebas
- `pytest tests/test_gcp03_app_env_por_servicio.py` comprueba que el Dockerfile no declara `NEXT_PUBLIC_APP_ENV` ni un `ARG` de entorno; que, para cada entorno, el frontend y el backend declaran el mismo `APP_ENV`; y que la misma imagen, con `APP_ENV=production`, sirve `robots.txt` con `Allow: /`.
- `pytest tests/test_gcp03_frontend_cloudrun.py` comprueba que la configuración `next.config.cloudrun.ts` especifica `output: 'standalone'`, que el Dockerfile define usuario non-root y que el servicio de Cloud Run expone el puerto 3000 con health check (`INV_LOPDP_STANDALONE_FRONTEND_CONTAINER`).
