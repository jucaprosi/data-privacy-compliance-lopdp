# Brief para el propietario y Antigravity: Google Cloud (2026-11-08)

Todo lo de este brief lo aplica el propietario, con Antigravity, en el proyecto de Google Cloud. Ningún sub chat ni ninguna IA toca Google Cloud, secretos ni `.github/workflows/`: solo leen con gcloud. El orden importa: **A → B → C → D → E**.

## A. Secretos y variables del backend en Cloud Run

Origen: SEC-16 (#479) y SEC-17 (#484). En la nube (con `K_SERVICE` definida), el backend **no arranca** si falta alguno de estos valores o si es débil.

1. En Secret Manager, crear:
   - `JWT_SECRET`: aleatorio, de 32 caracteres o más.
   - `SESSION_SECRET`: aleatorio, de 32 caracteres o más y **distinto** de `JWT_SECRET`.
2. `CORS_ORIGINS` es una **variable de entorno** (`--set-env-vars`), no un secreto: no se crea en Secret Manager. Va con https, no vacía: `CORS_ORIGINS=https://app.evydentia.com` (GCP-09). Hace falta aunque el proxy de GCP-08 deje el navegador en el mismo origen.
3. `DATABASE_URL`: PostgreSQL con el rol `lopdp_app`; nunca SQLite ni el rol dueño.
4. **`.github/workflows/deploy-gcp.yml:62`** hoy monta `JWT_SECRET_KEY`, y el código lee `JWT_SECRET`. Además, no monta `SESSION_SECRET` ni `CORS_ORIGINS`. Hay que corregir `--set-secrets` para que monte `JWT_SECRET`, `SESSION_SECRET` y `DATABASE_URL`, y `--set-env-vars` para que incluya `CORS_ORIGINS`. Hasta entonces, el despliegue falla a propósito: es el cierre seguro de SEC-16 y SEC-17.
5. **Ingress en `deploy-gcp.yml` (GCP-09).** Cada `gcloud run deploy` del workflow, el del backend y el del frontend, debe pasar `--ingress internal-and-cloud-load-balancing` y `--no-invoker-iam-check`. Sin esas opciones, una publicación desde el workflow puede dejar el servicio con ingress `all` y abrir la URL `run.app`. El workflow es tuyo; ninguna ficha lo toca.

## B. Cloud SQL PostgreSQL 16

Origen: GCP-04 (#490). La guía es `governance/operaciones/MIGRACION_CLOUDSQL_POSTGRES.md`, con la instancia `evydentia-production` en `us-central1`.

- **Estado real (GCP-09):** la instancia está en la revisión `20261118_merge_heads_cierre_dev`, 5 migraciones por detrás de `main`. Por eso **B2 (Alembic desde `main`) se repite justo antes de B5**. El rol dueño real es `evydentia_app`: es el que corre Alembic y el que cuenta filas en el paso 4.
- Pasos 1 a 4: instancia, esquema por Alembic desde `main`, rol `lopdp_app` y datos. Antes de quitar FORCE, guardar la lista de tablas en `tablas_force.txt`.
- **Paso 5, obligatorio:** `python scripts/verificar_cloudsql_conexion.py` y `python scripts/verificar_revision_alembic.py` terminan con código 0. Sin eso no hay corte.
- Paso 7: el plan de vuelta atrás queda anotado antes del corte.

## C. Autenticación del proxy del frontend hacia el backend: opción 1 (decidida)

Origen: GCP-08 y decisión del propietario del 2026-11-08. **Opción 1: ingress interno, sin IAM.**

- Backend y frontend con `--ingress internal-and-cloud-load-balancing` y sin exigir `roles/run.invoker` (`--no-invoker-iam-check`, en el YAML `run.googleapis.com/invoker-iam-disabled: "true"`).
- `PROXY_AUTH_CLOUD_RUN=ninguna` en el frontend; `BACKEND_URL=https://app.evydentia.com`.
- **Motivo:** el balanceador lleva `/api/*` directo del navegador al backend. Con IAM, el navegador no lleva token de servicio y recibiría 403. Sin IAM, la puerta única es el balanceador con Cloud Armor, y el token del usuario viaja en `Authorization` sin cambios.
- Las llamadas del servidor Next al backend entran también por el balanceador (`BACKEND_URL` es el dominio), así que no hace falta conector VPC para ellas. Si algún día `BACKEND_URL` pasa a la URL `run.app`, el frontend necesita `run.googleapis.com/vpc-access-egress: all-traffic` con su red: con ingress interno, Cloud Run rechaza lo que no salga por la VPC.

## D. Corte a producción: con el balanceador, no con el proxy

Origen: nota del CTO a GCP-08 y GCP-09. Con el balanceador de GCP-04 (`cloud_load_balancer.yaml`), `/api/*` va directo al backend. Si el corte se hace solo con el proxy del frontend, todas las peticiones anónimas comparten la IP de salida del frontend, y un solo cliente puede agotar el cupo de SEC-13, incluido el login. Por eso:

1. Paso 6 de la guía: apuntar `DATABASE_URL`, publicar la revisión y crear el balanceador con el certificado administrado `evydentia-cert` para `app.evydentia.com`.
2. **Registro DNS:** en el editor de zona de **BanaHosting** (servidores ns8924 y ns8925.banahosting.com), no en IONOS, crear el registro A `app` → IP de `evydentia-ip`, TTL 300. El dominio está registrado en IONOS, pero sus DNS migran a BanaHosting.
3. Esperar a que `evydentia-cert` quede en `ACTIVE` (`gcloud compute ssl-certificates describe evydentia-cert`).
4. Comprobar, antes de anunciar el dominio:
   - `https://app.evydentia.com/api/v1/health` responde 200 y la aplicación carga;
   - la URL `run.app` directa de cada servicio responde **404**: es la prueba física de que el balanceador es la única puerta.
5. Recién entonces, anunciar el dominio. No hay subdominio de prueba: el dominio es nuevo y no tiene tráfico.

## E. Alertas de OPS-07

Origen: OPS-07 (#480). Las políticas están en `governance/operaciones/monitoreo/alertas.json`, y la guía es `governance/operaciones/OBSERVABILIDAD.md` §2. Ninguna se crea solo a mano:

| Política | Cuándo avisa |
|---|---|
| `disponibilidad` | `/health` falla 2 comprobaciones seguidas, cada 60 s |
| `errores_5xx` | Más del 2 % de respuestas 5xx en 5 minutos |
| `latencia_p95` | p95 mayor que 1500 ms durante 10 minutos |
| `presupuesto` | Gasto mensual al 50, 90 y 100 % |
| `gasto_ia` | Gasto diario de Vertex AI mayor que el tope |

El destinatario de todas es el correo del propietario.

## Comprobación final

- `python scripts/verificar_despliegue.py` contra el dominio da código 0.
- `/health` responde 200 y ningún router aparece como fallido.
- Las cinco alertas existen en Cloud Monitoring.
