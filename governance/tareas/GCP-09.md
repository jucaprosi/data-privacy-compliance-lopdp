+++
id = "GCP-09"
titulo = "Dominio app.evydentia.com, ingress interno con el balanceador y brief del propietario actualizado"
ola = "indep"
estado = "pendiente"
sala = "operaciones"
depende_de = ["GCP-01", "GCP-03", "GCP-04", "GCP-08"]
propiedad = ["governance/operaciones/cloud_load_balancer.yaml", "governance/operaciones/cloudrun_frontend_service.yaml", "governance/operaciones/cloudrun_service.yaml", "governance/apoyo/BRIEF_PROPIETARIO_GCP_2026-11-08.md", "tests/test_gcp09_dominio_e_ingress.py"]
crea = ["tests/test_gcp09_dominio_e_ingress.py"]
arbitro = "pytest tests/test_gcp09_dominio_e_ingress.py tests/test_gcp08_proxy_e_imagen.py tests/test_gcp03_frontend_cloudrun.py + python scripts/generar_indice_tareas.py --verificar; mutación documentada"
rastros = ["¤ci-cd", "¤arbitro"]
+++

# GCP-09 · app.evydentia.com y opción 1 de autenticación

**Origen.** Decisiones del propietario del 2026-11-08, transmitidas por el CTO: «Usa app.evydentia.com, confirmo la opción 1».

## Entrega
1. `cloud_load_balancer.yaml`: `DOMINIO` → `app.evydentia.com`, con el certificado administrado `evydentia-cert`.
2. `cloudrun_frontend_service.yaml`: `run.googleapis.com/ingress` pasa de `all` a `internal-and-cloud-load-balancing` en los servicios del frontend, con `PROXY_AUTH_CLOUD_RUN=ninguna`.
3. `cloudrun_service.yaml` (backend): ingress `internal-and-cloud-load-balancing`, sin exigir `roles/run.invoker`. Si hoy no lo declara, se añade.
4. `BRIEF_PROPIETARIO_GCP_2026-11-08.md`:
   - **A2:** `CORS_ORIGINS=https://app.evydentia.com`.
   - **B:** la instancia real está en `20261118_merge_heads_cierre_dev`, 5 migraciones por detrás de main, así que B2 se repite antes de B5. El rol dueño real es `evydentia_app`.
   - **C:** decidida la opción 1. Motivo: el balanceador lleva `/api/*` directo del navegador al backend, y con IAM el navegador recibiría 403.
   - **D:** el registro A de `app.evydentia.com` apunta a `evydentia-ip`. Con el certificado en `ACTIVE`, se comprueban `/api/v1/health` y la aplicación antes de anunciar el dominio. Sin subdominio de prueba, porque el dominio es nuevo y no tiene tráfico.
5. **Llamadas del servidor Next al backend.** Con el backend en `internal-and-cloud-load-balancing`, una llamada del servidor Next (SSR, route handler, incluido el proxy de GCP-08) a la URL `run.app` del backend se rechaza, salvo que salga por la VPC (Direct VPC egress con `egress: all-traffic`). Hay que comprobar si existen esas llamadas en producción:
   - si existen, `cloudrun_frontend_service.yaml` declara la salida por VPC y el brief lo dice;
   - si no existen, porque el balanceador lleva `/api/*` directo al backend, se anota en el PR.
6. **`deploy-gcp.yml`.** Si su `gcloud run deploy` no pasa `--ingress`, una publicación desde el workflow podría dejar el ingress en `all`. El brief le pide al propietario `--ingress internal-and-cloud-load-balancing` en los dos servicios del workflow. El workflow es suyo; la ficha no lo toca.

## Pruebas (`tests/test_gcp09_dominio_e_ingress.py`)
1. Los dos servicios declaran ingress `internal-and-cloud-load-balancing`.
2. El frontend declara `PROXY_AUTH_CLOUD_RUN=ninguna`.
3. Ningún YAML ni el brief conservan `DOMINIO` sin sustituir.
4. `CORS_ORIGINS` del brief no usa `http://`.

5. El brief pide `--ingress internal-and-cloud-load-balancing` para los dos servicios de `deploy-gcp.yml`.
6. Si el frontend llama al backend desde el servidor, su YAML declara Direct VPC egress con `all-traffic`.

**Mutación:** volver el ingress del frontend a `all` hace fallar la prueba 1.

## No hagas
- Nada en Google Cloud ni en `.github/workflows/`: lo aplica el propietario con Antigravity.
