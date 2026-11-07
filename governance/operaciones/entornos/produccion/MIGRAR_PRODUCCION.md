# Migrar producción con el job `evydentia-migrate` (`¤migracion-produccion`)

## Qué es

`evydentia-migrate` es un Cloud Run Job del proyecto `evydentia`, en la región `us-central1`. Ejecuta `alembic upgrade head` contra la base de producción. Lo creó el propietario con Antigravity. La primera migración real con este job llegó hasta `20261118_merge_heads_cierre_dev`, el 6-nov-2026 a las 23:02 ECT, con el propietario presente.

Definición, leída con `gcloud run jobs describe evydentia-migrate --region us-central1 --project evydentia` (solo lectura):

| Campo | Valor |
|---|---|
| Imagen | `us-central1-docker.pkg.dev/evydentia/evydentia-containers/backend:latest` |
| Comando | `alembic upgrade head` |
| Cuenta de servicio | `sa-evydentia-backend@evydentia.iam.gserviceaccount.com` |
| Conexión a Cloud SQL | `evydentia:us-central1:evydentia-production` |
| Secretos (Secret Manager) | `DATABASE_URL`, `JWT_SECRET_KEY` |
| Variables literales | `ENVIRONMENT`, `PROJECT_ID` (sus valores no se copian aquí) |

Este documento nunca copia los valores de los secretos ni la URL de conexión.

Estado actual del job, verificado por el CTO con `gcloud` de solo lectura el 2026-11-07:

| Campo | Valor |
|---|---|
| Imagen | Se fija por digest antes de cada migración (ver «Orden») |
| `timeoutSeconds` | 600 |
| `maxRetries` | 0 |
| `taskCount` | 1 |
| Cuenta de servicio | `sa-evydentia-backend`, la misma del servicio de producción |
| Quién puede ejecutarlo | El propietario del proyecto (`roles/owner`). `sa-github-actions` ya no puede ejecutar ni modificar el job: en el proyecto solo tiene `roles/artifactregistry.writer`, en el servicio `evydentia-backend` tiene `roles/run.developer` y en la cuenta `sa-evydentia-backend` tiene `roles/iam.serviceAccountUser` |

## Riesgos y cambios propuestos

| # | Cambio | Estado |
|---|---|---|
| 1 | **Migrar con el digest que pasó el CI en lugar de `latest`.** Con `latest` se migra con la última imagen publicada, que no necesariamente es la versión revisada. | Hecho: es el procedimiento de «Orden». |
| 2 | **`maxRetries` en 0.** Un reintento automático tras un fallo a la mitad puede dejar la base en un estado mixto. Ante un fallo, revisa una persona. | Hecho por el propietario con Antigravity (2026-11-07). |
| 3 | **Separar los usuarios:** el backend con `lopdp_app` (SEC-10, permisos mínimos) y el job con `evydentia_app` y su propia cuenta de servicio. | Por confirmar: el diagnóstico de permisos sigue en curso con Antigravity. |
| 4 | **Que `sa-github-actions` no pueda ejecutar el job.** Ninguna corrida de CI debe migrar producción. | Hecho por el propietario con Antigravity (2026-11-07). |

Ninguna sesión de IA aplica estos cambios.

## Quién lo lanza

Lo lanzan Juan Carlos, Aleczandra o José, siempre después de fusionar y desde `main`. **Ninguna sesión de IA lo ejecuta.** Las sesiones solo leen, con `gcloud` de lectura. Si un cambio necesita una migración, la sesión lo avisa con un brief y lo ejecuta el propietario.

## Orden

1. Se fusiona el PR en `main`.
2. Si la fusión trae archivos en `alembic/versions/`, se migra con el digest de la imagen que pasó el CI, en dos pasos:

   Paso 1. Fijar la imagen del job en ese digest:

   ```bash
   gcloud run jobs update evydentia-migrate --image=us-central1-docker.pkg.dev/evydentia/evydentia-containers/backend@sha256:<digest del CI> --region=us-central1 --project=evydentia
   ```

   Paso 2. Ejecutarlo:

   ```bash
   gcloud run jobs execute evydentia-migrate --region=us-central1 --project=evydentia --wait
   ```

   `execute` no acepta `--image`, así que la imagen se fija siempre antes, con `update`.

3. Después se publica, lanzando `deploy-gcp.yml` con `workflow_dispatch` (PRD EVYDENTIA §5.6.5, publicación manual).

Nunca se publica antes de migrar si la versión trae migraciones.

## Cómo se comprueba la cabeza de Alembic

1. La cabeza esperada sale de `main`:

   ```bash
   alembic heads
   ```

   Tiene que devolver una sola cabeza.
2. Para saber si la ejecución terminó bien, se revisa su estado:

   ```bash
   gcloud run jobs executions list --job evydentia-migrate --region us-central1 --project evydentia --limit 1
   ```

3. Para ver hasta qué revisión llegó, se leen sus registros y se busca la última línea `Running upgrade … -> <revisión>`:

   ```bash
   gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=evydentia-migrate" --project evydentia --limit 50 --freshness 1d
   ```

4. La revisión del registro tiene que coincidir con la de `alembic heads`. Si no coincide, no se publica y se avisa al CTO.

Toda migración manual se anota también en `governance/operaciones/REGISTRO_MIGRACIONES_MANUALES.md`.
