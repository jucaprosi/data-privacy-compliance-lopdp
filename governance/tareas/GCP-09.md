+++
id = "GCP-09"
titulo = "Dominio app.evydentia.com, ingress interno con el balanceador y brief del propietario actualizado"
ola = "indep"
estado = "en_curso"
sala = "operaciones"
depende_de = ["GCP-01", "GCP-03", "GCP-04", "GCP-08"]
propiedad = ["governance/operaciones/cloud_load_balancer.yaml", "governance/operaciones/cloudrun_frontend_service.yaml", "governance/operaciones/cloudrun_service.yaml", "governance/apoyo/BRIEF_PROPIETARIO_GCP_2026-11-08.md", "tests/test_gcp09_dominio_e_ingress.py"]
crea = ["tests/test_gcp09_dominio_e_ingress.py"]
arbitro = "pytest tests/test_gcp09_dominio_e_ingress.py tests/test_gcp08_proxy_e_imagen.py tests/test_gcp03_frontend_cloudrun.py + python scripts/generar_indice_tareas.py --verificar; mutación documentada"
rastros = ["¤ci-cd", "¤arbitro"]
+++

# GCP-09 · app.evydentia.com y opción 1 de autenticación

**Origen.** Decisiones del propietario del 2026-11-08, transmitidas por el CTO: «Usa app.evydentia.com, confirmo la opción 1».

**Validada por el Arquitecto ADPA (2026-11-08, 0690a43).** Comprobó que `/api/*` va a `evydentia-backend-bs` y que el proxy no hace bucle hacia el frontend.

## Entrega
1. `cloud_load_balancer.yaml`: `DOMINIO` → `app.evydentia.com`, con el certificado administrado `evydentia-cert`.
2. `cloudrun_frontend_service.yaml`: `run.googleapis.com/ingress` pasa de `all` a `internal-and-cloud-load-balancing` en los servicios del frontend, con `PROXY_AUTH_CLOUD_RUN=ninguna`.
3. `cloudrun_service.yaml` (backend): ingress `internal-and-cloud-load-balancing`.
3b. **Sin exigir `roles/run.invoker`, declarado:** los dos YAML llevan `run.googleapis.com/invoker-iam-disabled: "true"` (equivale a `--no-invoker-iam-check`). Sin esto, el balanceador recibe 403.
4. `BRIEF_PROPIETARIO_GCP_2026-11-08.md`:
   - **A2:** `CORS_ORIGINS=https://app.evydentia.com`.
   - **B:** la instancia real está en `20261118_merge_heads_cierre_dev`, 5 migraciones por detrás de main, así que B2 se repite antes de B5. El rol dueño real es `evydentia_app`.
   - **C:** decidida la opción 1. Motivo: el balanceador lleva `/api/*` directo del navegador al backend, y con IAM el navegador recibiría 403.
   - **D:** el registro A de `app.evydentia.com` («app» → IP de `evydentia-ip`, TTL 300) apunta a `evydentia-ip`. Se crea en el editor de zona de BanaHosting (ns8924 y ns8925.banahosting.com), no en IONOS, porque el dominio está registrado en IONOS pero sus DNS migran a BanaHosting. Con el certificado en `ACTIVE`, se comprueban `/api/v1/health` y la aplicación antes de anunciar el dominio, y que la URL `run.app` directa de cada servicio responde 404: es la prueba física de que el balanceador es la única puerta. Sin subdominio de prueba, porque el dominio es nuevo y no tiene tráfico.
5. **Llamadas del servidor Next al backend (decisión del Tech Lead con el Arquitecto, opción b).** Con el backend en `internal-and-cloud-load-balancing`, Cloud Run rechaza una llamada a su URL `run.app` que no salga por la VPC. Por eso `BACKEND_URL = https://app.evydentia.com`: el proxy de GCP-08 y cualquier fetch del servidor (SSR) entran por el balanceador, que ya enruta `/api/*` al backend. No hace falta VPC. Si algún día se usa la URL `run.app`, el YAML del frontend tiene que declarar `run.googleapis.com/vpc-access-egress: all-traffic` con su red o subred.
6. **`deploy-gcp.yml`.** Si su `gcloud run deploy` no pasa `--ingress`, una publicación desde el workflow podría dejar el ingress en `all`. El brief le pide al propietario `--ingress internal-and-cloud-load-balancing` en los dos servicios del workflow. El workflow es suyo; la ficha no lo toca.

**Nota del CTO (límite por IP):** las llamadas del servidor Next que entran por el balanceador llegan a Cloud Armor (600/min por IP) y a SEC-13 con la IP de salida del frontend, sin X-Forwarded-For. En el PR, lista esas llamadas y estima cuántas hace cada página. Si son relevantes, avísale al Tech Lead para abrir una ficha (excluir la ruta en Cloud Armor o reenviar la IP del cliente firmada).

## Pruebas (`tests/test_gcp09_dominio_e_ingress.py`)
1. Los dos servicios declaran ingress `internal-and-cloud-load-balancing`.
2. El frontend declara `PROXY_AUTH_CLOUD_RUN=ninguna`.
3. Ningún YAML ni el brief conservan `DOMINIO`, `evydentia.example` ni otro marcador de ejemplo.
4. `CORS_ORIGINS` del brief no usa `http://`.

5. El brief pide `--ingress internal-and-cloud-load-balancing` para los dos servicios de `deploy-gcp.yml`.
6. Con el ingress del backend en interno, `BACKEND_URL` no es una URL `*.run.app`, salvo que el YAML del frontend declare egress `all-traffic`.
7. Los dos servicios declaran `run.googleapis.com/invoker-iam-disabled: "true"`.
8. El host del certificado en `cloud_load_balancer.yaml` coincide con el de `CORS_ORIGINS`.

**Mutaciones:**
- M1: volver el ingress del frontend a `all` hace fallar la prueba 1.
- M2: `BACKEND_URL` de `run.app` sin egress hace fallar la prueba 6.

## No hagas
- Nada en Google Cloud ni en `.github/workflows/`: lo aplica el propietario con Antigravity.
