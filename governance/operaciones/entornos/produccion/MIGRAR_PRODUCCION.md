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

**Por confirmar con el propietario:**
- La imagen usa la etiqueta `latest`. Hay que confirmar si antes de cada migración se fija el digest que se va a publicar, para que la migración y la revisión publicada salgan de la misma imagen.
- Los límites de tiempo, los reintentos y la cuenta que tiene permiso para ejecutar el job solo se ven en la consola.

## Quién lo lanza

Lo lanzan Juan Carlos, Aleczandra o José, siempre después de fusionar y desde `main`. **Ninguna sesión de IA lo ejecuta.** Las sesiones solo leen, con `gcloud` de lectura. Si un cambio necesita una migración, la sesión lo avisa con un brief y lo ejecuta el propietario.

## Orden

1. Se fusiona el PR en `main`.
2. Si la fusión trae archivos en `alembic/versions/`, se migra:

   ```bash
   gcloud run jobs execute evydentia-migrate --region us-central1 --project evydentia --wait
   ```

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
