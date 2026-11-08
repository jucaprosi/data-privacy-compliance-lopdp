# Brief para el propietario y Antigravity: Google Cloud (2026-11-08)

Todo lo de este brief lo aplica el propietario, con Antigravity, en el proyecto de Google Cloud. Ningún sub chat ni ninguna IA toca Google Cloud, secretos ni `.github/workflows/`: solo leen con gcloud. El orden importa: **A → B → C → D → E**.

## A. Secretos y variables del backend en Cloud Run

Origen: SEC-16 (#479) y SEC-17 (#484). En la nube (con `K_SERVICE` definida), el backend **no arranca** si falta alguno de estos valores o si es débil.

1. En Secret Manager, crear:
   - `JWT_SECRET`: aleatorio, de 32 caracteres o más.
   - `SESSION_SECRET`: aleatorio, de 32 caracteres o más y **distinto** de `JWT_SECRET`.
2. `CORS_ORIGINS` es una **variable de entorno** (`--set-env-vars`), no un secreto: no se crea en Secret Manager. Va con https, no vacía, con el dominio del frontend. Hace falta aunque el proxy de GCP-08 deje el navegador en el mismo origen.
3. `DATABASE_URL`: PostgreSQL con el rol `lopdp_app`; nunca SQLite ni el rol dueño.
4. **`.github/workflows/deploy-gcp.yml:62`** hoy monta `JWT_SECRET_KEY`, y el código lee `JWT_SECRET`. Además, no monta `SESSION_SECRET` ni `CORS_ORIGINS`. Hay que corregir `--set-secrets` para que monte `JWT_SECRET`, `SESSION_SECRET` y `DATABASE_URL`, y `--set-env-vars` para que incluya `CORS_ORIGINS`. Hasta entonces, el despliegue falla a propósito: es el cierre seguro de SEC-16 y SEC-17.

## B. Cloud SQL PostgreSQL 16

Origen: GCP-04 (#490). La guía es `governance/operaciones/MIGRACION_CLOUDSQL_POSTGRES.md`, con la instancia `evydentia-production` en `us-central1`.

- Pasos 1 a 4: instancia, esquema por Alembic desde `main`, rol `lopdp_app` y datos. Antes de quitar FORCE, guardar la lista de tablas en `tablas_force.txt`.
- **Paso 5, obligatorio:** `python scripts/verificar_cloudsql_conexion.py` y `python scripts/verificar_revision_alembic.py` terminan con código 0. Sin eso no hay corte.
- Paso 7: el plan de vuelta atrás queda anotado antes del corte.

## C. Autenticación del proxy del frontend hacia el backend (decisión pendiente)

Origen: GCP-08, punto 4 de la revisión de Seguridad. **Elige una:**

| Opción | Qué implica |
|---|---|
| **1. Ingress interno, sin IAM** | El backend acepta solo tráfico interno y del balanceador (`--ingress internal-and-cloud-load-balancing`) y no exige `roles/run.invoker`. Es más simple, y el token del usuario viaja en `Authorization` sin cambios. |
| **2. Token de servicio** | El backend exige IAM. La cuenta de servicio del frontend tiene `roles/run.invoker`, y el proxy envía su token en `X-Serverless-Authorization`, sin tocar `Authorization`. Es más estricto, pero hay que configurar la cuenta. |

El ingeniero de GCP-08 deja el código listo para las dos. Hasta que decidas, la configuración del servicio no se cierra.

## D. Corte a producción: con el balanceador, no con el proxy

Origen: nota del CTO a GCP-08. Con el balanceador de GCP-04 (`cloud_load_balancer.yaml`), `/api/*` va directo al backend. Si el corte se hace solo con el proxy del frontend, todas las peticiones anónimas comparten la IP de salida del frontend, y un solo cliente puede agotar el cupo de SEC-13, incluido el login. Por eso:

1. Paso 6 de la guía: apuntar `DATABASE_URL`, publicar la revisión y crear el balanceador.
2. Comprobar `/api/v1/health` a través del dominio.
3. Recién entonces, apuntar el dominio público.

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
