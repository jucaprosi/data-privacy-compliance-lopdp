# Guía y Operación de la Demostración Comercial (DEMO-07)

**Entorno:** `evydentia-demo` (Google Cloud).  
**Sala responsable:** `operaciones`.  
**Contrato y Arquitectura:** `PRD.md` §5.6, `INVARIANTS.md` (60–63) y ficha `governance/tareas/DEMO-07.md`.

---

## 1. Arquitectura y Componentes Desplegados

El entorno comercial de demostración opera de manera estrictamente aislada del entorno de producción (`evydentia`):

| Componente | Recurso en Google Cloud | Configuración / Rol |
| :--- | :--- | :--- |
| **Proyecto** | `evydentia-demo` (`517105327086`) | Región `us-central1`. `APP_ENV=demo`. |
| **Base de Datos** | `evydentia-demo-db` (Cloud SQL) | PostgreSQL 16, tier `db-f1-micro`, `activationPolicy=ALWAYS`. Migrada a las 12 cabezas Alembic. |
| **Rol de Aplicación** | `evydentia_demo_app` | `NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE`. RLS activo en todas las tablas. |
| **Rol de Purga** | `purga_demo` | Solo permisos de DELETE definidos en `jobs/purga_demo/politicas_purga.sql` y función `purga_demo_borrar_inmutables`. |
| **Bucket de Evidencias** | `gs://lopdp360-demo-evidencias` | Acceso uniforme, sin prevención de borrado, sin política de retención ni bloqueo WORM, OLM a 3 días. |
| **Backend API** | `evydentia-backend-demo` | Cloud Run gen2, Ingress `all` protegido por IAM. Invocable únicamente por la cuenta del frontend. |
| **Frontend Web** | `evydentia-web-demo` | Cloud Run, Ingress `all`, acceso público. Proxy autenticado con token de servicio (`PROXY_AUTH_CLOUD_RUN=token_servicio`). |
| **Job de Purga** | `purga-demo` (Cloud Run Job) | Contenedor `purga-demo:v1` con guardias de seguridad activas (`APP_ENV=demo`, `HUELLA_PROYECTO_PRODUCCION=evydentia-production`). |
| **Scheduler Nocturno** | `purga-demo-nocturna` (Cloud Scheduler) | Disparo automático diario a las `03:00` America/Guayaquil (`0 3 * * *`). |

---

## 2. Gestión de Vendedores (Altas y Bajas)

Para garantizar que únicamente el personal comercial autorizado pueda clonar y operar instancias de demostración, el acceso se controla a través de dos mecanismos:

### 2.1 Lista de Vendedores Autorizados (`DEMO_VENDEDORES`)
El backend valida que el correo autenticado pertenezca a la lista del secreto `DEMO_VENDEDORES` en Secret Manager antes de permitir la creación de un nuevo tenant demo.

- **Para consultar los vendedores actuales:**
  ```powershell
  gcloud secrets versions access latest --secret=DEMO_VENDEDORES --project=evydentia-demo
  ```

- **Para dar de alta a un vendedor:**
  1. Descarga o prepara la lista actualizada separada por comas (sin espacios):
     ```powershell
     $VENDEDORES = "juancarlosproanios@gmail.com,evydentia@gmail.com,nuevo_vendedor@empresa.com"
     $ARCHIVO = Join-Path $env:TEMP "demo_vendedores.txt"
     Set-Content -Path $ARCHIVO -Value $VENDEDORES -NoNewline -Encoding ascii
     gcloud secrets versions add DEMO_VENDEDORES --data-file=$ARCHIVO --project=evydentia-demo
     Remove-Item $ARCHIVO
     ```
  2. Reinicia o actualiza el backend para tomar la nueva versión si fuera necesario:
     ```powershell
     gcloud run services update evydentia-backend-demo --project=evydentia-demo --region=us-central1 --update-env-vars="TIMESTAMP=$(Get-Date -Format s)"
     ```

- **Para dar de baja a un vendedor:**
  Genera una nueva versión del secreto `DEMO_VENDEDORES` excluyendo el correo del vendedor revocado. La siguiente petición del usuario será rechazada con `403 Prohibido`.

### 2.2 Control de Acceso al Servicio Web (IAP / IAM)
- Cuando IAP está habilitado en Cloud Run, se añade al vendedor mediante:
  ```powershell
  gcloud iap web add-iam-policy-binding --resource-type=cloud-run --service=evydentia-web-demo --region=us-central1 --project=evydentia-demo --member="user:vendedor@empresa.com" --role="roles/iap.httpsResourceAccessor"
  ```
- Para revocar acceso:
  ```powershell
  gcloud iap web remove-iam-policy-binding --resource-type=cloud-run --service=evydentia-web-demo --region=us-central1 --project=evydentia-demo --member="user:vendedor@empresa.com" --role="roles/iap.httpsResourceAccessor"
  ```

---

## 3. Registro del Recorrido de Aceptación (Árbitro DEMO-07)

**Fecha:** 2026-11-21  
**Ejecutores:** Juan Carlos Proaño (verificación técnica y despliegue), Aleczandra Proaño / José (recorrido de negocio).  
**URL Demo:** `https://evydentia-web-demo-517105327086.us-central1.run.app`

### 3.1 Puntos de Comprobación
1. **Entrada y Autenticación:**
   - La pantalla de login muestra el banner contextual: `Demostración · datos ficticios` (`aviso-entorno`).
   - El inicio de sesión se realiza mediante Google OAuth (`943042355099-um6ieu8s1s8kettg253g9v5ms8ag7k4l.apps.googleusercontent.com`).
   - La consulta a `/api/v1/entorno` devuelve `{ "entorno": "demo", "datos_ficticios": true }`.
2. **Siembra y Clonación:**
   - Creación de sesión demo a partir de la plantilla cooperativa (`demo-plantilla-cooperativa`).
   - Se crean las personas ficticias vinculadas al tenant efímero del vendedor.
3. **Selector «Ver como»:**
   - El vendedor puede alternar entre perfiles ficticios (DPO, Oficial de Seguridad, Responsable de Tratamiento) verificando la vista de cada rol sin alterar la persistencia de producción.
4. **Finalización («Terminar demo»):**
   - El vendedor presiona el botón «Terminar demo», marcando la sesión como finalizada y dejando el tenant listo para su recolección.
5. **Purga Nocturna:**
   - El Job `purga-demo` ejecutado en Cloud Run (`purga-demo-9trtv`) procesa los tenants vencidos y limpia físicamente:
     - Objetos en `gs://lopdp360-demo-evidencias` con prefijo del tenant.
     - Filas en tablas inmutables mediante `purga_demo_borrar_inmutables`.
     - Filas en tablas con RLS mediante las políticas de `politicas_purga.sql`.
   - Se preserva intacta la plantilla base `demo-plantilla-cooperativa` y cualquier demo activa no vencida.

---

## 4. Evidencia de Ejecución de la Purga

Ejecución auditada del Job `purga-demo`:

```text
[PURGA_DEMO] Iniciando purga determinista en entorno demo (evydentia-demo)
[PURGA_DEMO] Conectando a evydentia-demo-db con rol purga_demo...
[PURGA_DEMO] Guardias superadas: entorno=demo, huella_prod=evydentia-production
[PURGA_DEMO] Bucket verificado: lopdp360-demo-evidencias (sin retencion, sin bloqueo)
[PURGA_DEMO] Tenants procesados: 14 vencidos
[PURGA_DEMO] Filas eliminadas: 1474
[PURGA_DEMO] Objetos eliminados de GCS: 0
[PURGA_DEMO] Plantilla 'demo-plantilla-cooperativa' preservada con exito.
[PURGA_DEMO] Purga completada con codigo de salida 0.
```

El Cloud Scheduler `purga-demo-nocturna` queda habilitado con la expresión `0 3 * * *` para mantener el almacenamiento y la base de datos limpios diariamente.

---

## 5. Publicar la web de demo (DEMO-09)

La web de demo (`evydentia-web-demo`) corre la **misma imagen web de producción del mismo commit**, por digest, leída del repositorio `us-central1-docker.pkg.dev/evydentia/evydentia-containers/web`. Nada del bundle depende del entorno al compilar, salvo el client id de Google, que es el mismo en los dos entornos (`frontend/cloudbuild.yaml`). Por eso este procedimiento nunca compila una imagen aparte: si falta la imagen del commit, usa la construcción de producción (GCP-03b). Contrato: `governance/especificaciones/DEMO-09.md`.

### 5.1 Prerrequisito único (una sola vez)

El agente de servicio de Cloud Run de la demo (`service-517105327086@serverless-robot-prod.iam.gserviceaccount.com`) necesita `roles/artifactregistry.reader` **solo sobre el repositorio** `evydentia-containers`, nunca sobre el proyecto `evydentia`. Sin él, la revisión nueva no puede descargar la imagen. Los pasos, con su comprobación, están en `C:\Users\Juan Carlos\compartido\evydentia\briefs\DEMO-09-propietario.md` (fuera del repositorio). El supuesto sobre el nombre de esa cuenta se confirma allí con `gcloud projects get-iam-policy evydentia-demo`.

### 5.2 Procedimiento

Lo ejecuta el propietario en PowerShell. Cada bloque es independiente de la sesión: define sus variables.

```powershell
# 0. Comprobar el permiso de lectura del repositorio (5.1). Sin él, no se publica nada.
$NUMERO = (gcloud projects describe evydentia-demo --format="value(projectNumber)").Trim()
$AGENTE = "service-$NUMERO@serverless-robot-prod.iam.gserviceaccount.com"
$POLITICA = gcloud artifacts repositories get-iam-policy evydentia-containers --project=evydentia --location=us-central1 --format=json | ConvertFrom-Json
$TIENE = $POLITICA.bindings | Where-Object { $_.role -eq "roles/artifactregistry.reader" -and $_.members -contains "serviceAccount:$AGENTE" }
if (-not $TIENE) { throw "Falta roles/artifactregistry.reader para $AGENTE sobre evydentia-containers: haz primero el prerrequisito de 5.1. No se publica nada." }

# 1. Imagen del commit: localizarla o construirla una sola vez con la construcción de producción.
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"
git fetch origin
$COMMIT = (git rev-parse --short origin/main).Trim()
$IMAGEN = "us-central1-docker.pkg.dev/evydentia/evydentia-containers/web"
gcloud artifacts docker images describe "${IMAGEN}:${COMMIT}" --project=evydentia
# Si la orden anterior responde que no la encuentra, construirla desde el commit de origin/main
# (la misma construcción de producción, GCP-03b):
#   git switch --detach origin/main
#   cd frontend
#   gcloud builds submit --config cloudbuild.yaml --substitutions=_ETIQUETA=$COMMIT --project=evydentia .
$DIGEST = (gcloud artifacts docker images describe "${IMAGEN}:${COMMIT}" --project=evydentia --format="value(image_summary.digest)").Trim()
"Imagen del commit: ${IMAGEN}@${DIGEST}"

# 2. Guardar la revisión actual en el servicio, como etiqueta de tráfico "anterior" (5.3 vuelve con ella).
$ANTERIOR = (gcloud run services describe evydentia-web-demo --project=evydentia-demo --region=us-central1 --format="value(status.latestReadyRevisionName)").Trim()
"Revisión anterior: $ANTERIOR"
gcloud run services update-traffic evydentia-web-demo --project=evydentia-demo --region=us-central1 --update-tags="anterior=$ANTERIOR"

# 3. Publicar la revisión nueva sin tráfico, con una etiqueta. Variables y cuenta del servicio no cambian.
gcloud run deploy evydentia-web-demo --project=evydentia-demo --region=us-central1 --image="${IMAGEN}@${DIGEST}" --no-traffic --tag="c${COMMIT}"
```

**4. Verificar en la URL de la etiqueta** (`https://c<commit>---evydentia-web-demo-<hash>-uc.a.run.app`, la imprime el paso 3):

- `/login` responde 200 y ofrece el acceso con Google.
- El aviso de entorno dice «demo» y una fecha sale en es-EC (GCP-08c).
- Con IA-15 fusionada, el consentimiento del preanálisis nombra «Estados Unidos (región us)».

```powershell
# 5. Pasar el tráfico a la revisión nueva y repetir la comprobación en la URL pública.
gcloud run services update-traffic evydentia-web-demo --project=evydentia-demo --region=us-central1 --to-latest
```

### 5.3 Volver atrás

```powershell
# La etiqueta "anterior" la dejó el paso 2 de 5.2 en Cloud Run; este bloque no hereda nada de aquel.
gcloud run services update-traffic evydentia-web-demo --project=evydentia-demo --region=us-central1 --to-tags="anterior=100"
```

### 5.4 Qué comprueba el repositorio

`tests/test_demo09_web_demo.py` verifica, sin red, que la imagen del manifiesto `entornos/demo/cloudrun_frontend.yaml`, la de este procedimiento y la de `frontend/cloudbuild.yaml` son la misma; que el client id es uno solo; que este procedimiento no compila aparte; y que solo ese id entra al compilar. La aceptación final es del propietario: la revisión nueva sirve `/login` con `$IMAGEN@<digest del commit>`.

## 6. Backend y migración de la demo (DEMO-11)

El backend de demo (`evydentia-backend-demo`) corre la imagen `us-central1-docker.pkg.dev/evydentia-demo/evydentia-demo-containers/backend` del **mismo commit que la web de §5.2**, por digest. La base `evydentia-demo-db` se migra con el job `migrar-demo` (`entornos/demo/job_migracion.yaml`). Ese job se declara como `evydentia-migrate` de producción (`entornos/produccion/MIGRAR_PRODUCCION.md`): `alembic upgrade heads`, `maxRetries: 0`, una cuenta propia y `DATABASE_URL` desde Secret Manager. Contrato: `governance/especificaciones/DEMO-11.md`.

**Quién.** Lo ejecuta el propietario en PowerShell, desde `main` y tras fusionar. Ninguna sesión de IA migra ni publica la demo. Crear el job, su cuenta, el secreto `DATABASE_URL` y la membresía de `evydentia_demo_app` en `lopdp_app` también le toca al propietario. Cada bloque define sus variables. Ningún bloque contiene valores de secretos.

**Orden.** 6.1 → 6.2 → 6.3. Nunca se publica el backend antes de migrar.

### 6.1 Imagen

```powershell
# Imagen del backend del mismo commit que la web de §5.2: localizarla o construirla una sola vez en evydentia-demo.
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"
git fetch origin
$COMMIT = (git rev-parse --short origin/main).Trim()
$IMAGEN = "us-central1-docker.pkg.dev/evydentia-demo/evydentia-demo-containers/backend"
gcloud artifacts docker images describe "${IMAGEN}:${COMMIT}" --project=evydentia-demo
# Si la orden anterior responde que no la encuentra, construirla desde ese commit, con el Dockerfile raíz,
# como se construyó backend:b56f39c3:
#   git switch --detach $COMMIT
#   gcloud builds submit --tag "${IMAGEN}:${COMMIT}" --project=evydentia-demo .
#   git switch main
$DIGEST = (gcloud artifacts docker images describe "${IMAGEN}:${COMMIT}" --project=evydentia-demo --format="value(image_summary.digest)").Trim()
"Imagen del commit: ${IMAGEN}@${DIGEST}"
```

### 6.2 Migración, antes de publicar el backend

```powershell
# 1. Copia previa de evydentia-demo-db. Sin la copia terminada, no se migra.
gcloud sql backups create --instance=evydentia-demo-db --project=evydentia-demo --description="antes de migrar-demo"
gcloud sql backups list --instance=evydentia-demo-db --project=evydentia-demo --limit=1
```

**2. Comprobación de solo lectura de la membresía** (`cloud_sql.yaml`, R3). La hace el propietario con Antigravity, por `cloud-sql-proxy` contra `evydentia-demo:us-central1:evydentia-demo-db`, dentro de una transacción de solo lectura. Como alternativa sirve Cloud SQL Studio, en la consola de Google Cloud (proyecto `evydentia-demo`, base `evydentia_demo`). Ninguna contraseña se escribe en este documento.

```sql
BEGIN TRANSACTION READ ONLY;
SELECT pg_has_role('evydentia_demo_app','lopdp_app','MEMBER');
ROLLBACK;
```

Si responde `f`, **el procedimiento se detiene aquí** y se avisa al propietario: la membresía no está concedida y el backend no podría usar los permisos que las migraciones conceden a `lopdp_app`.

```powershell
# 3. Fijar el job en el digest de 6.1 y ejecutarlo. execute no acepta --image: la imagen se fija antes, con update.
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"
$COMMIT = (git rev-parse --short origin/main).Trim()
$IMAGEN = "us-central1-docker.pkg.dev/evydentia-demo/evydentia-demo-containers/backend"
$DIGEST = (gcloud artifacts docker images describe "${IMAGEN}:${COMMIT}" --project=evydentia-demo --format="value(image_summary.digest)").Trim()
gcloud run jobs update migrar-demo --image="${IMAGEN}@${DIGEST}" --region=us-central1 --project=evydentia-demo
gcloud run jobs execute migrar-demo --region=us-central1 --project=evydentia-demo --wait
```

```powershell
# 4. Las cabezas del grafo de main: una por rama (CI-28). Se leen en un worktree temporal, que se quita al terminar.
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"
git fetch origin
$ARBOL = "C:\Users\Juan Carlos\worktrees-evydentia\cabezas-demo"
git worktree add --detach $ARBOL origin/main
cd $ARBOL
$CABEZAS = @(& "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" -m alembic heads | ForEach-Object { ($_ -split " ")[0] } | Sort-Object)
"Cabezas del grafo: $($CABEZAS.Count)"
$CABEZAS
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"
git worktree remove $ARBOL
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=migrar-demo" --project=evydentia-demo --limit=200 --freshness=1d --format="value(textPayload)" | Select-String "Running upgrade"
```

Las revisiones que dejó el job tienen que ser las mismas que `$CABEZAS`, y en el mismo número. Se leen de dos maneras: la última `-> <revisión>` de cada rama en el registro, o con la consulta siguiente, por la misma vía del paso 2 (Antigravity por `cloud-sql-proxy`, o Cloud SQL Studio). Si no coinciden, no se publica y se avisa al CTO.

```sql
BEGIN TRANSACTION READ ONLY;
SELECT version_num FROM alembic_version ORDER BY 1;
ROLLBACK;
```

### 6.3 Publicación del backend

```powershell
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"
$COMMIT = (git rev-parse --short origin/main).Trim()
$IMAGEN = "us-central1-docker.pkg.dev/evydentia-demo/evydentia-demo-containers/backend"
$DIGEST = (gcloud artifacts docker images describe "${IMAGEN}:${COMMIT}" --project=evydentia-demo --format="value(image_summary.digest)").Trim()

# 1. Guardar la revisión actual como etiqueta de tráfico "anterior" (6.4 vuelve con ella).
$ANTERIOR = (gcloud run services describe evydentia-backend-demo --project=evydentia-demo --region=us-central1 --format="value(status.latestReadyRevisionName)").Trim()
"Revisión anterior: $ANTERIOR"
gcloud run services update-traffic evydentia-backend-demo --project=evydentia-demo --region=us-central1 --update-tags="anterior=$ANTERIOR"

# 2. Publicar la revisión nueva sin tráfico, con una etiqueta. Variables y cuenta del servicio no cambian.
gcloud run deploy evydentia-backend-demo --project=evydentia-demo --region=us-central1 --image="${IMAGEN}@${DIGEST}" --no-traffic --tag="c${COMMIT}"

# 3. Comprobar /health en la URL de la etiqueta. El servicio exige IAM: se llama con un token de identidad.
$URL = (gcloud run services describe evydentia-backend-demo --project=evydentia-demo --region=us-central1 --format=json | ConvertFrom-Json).status.traffic | Where-Object { $_.tag -eq "c$COMMIT" } | Select-Object -ExpandProperty url
$TOKEN = (gcloud auth print-identity-token).Trim()
Invoke-WebRequest -Uri "$URL/health" -Headers @{ Authorization = "Bearer $TOKEN" } -UseBasicParsing | Select-Object StatusCode, Content
```

Si `/health` no responde 200, el tráfico no se pasa. Si responde 200:

```powershell
# 4. Pasar el tráfico a la revisión nueva.
gcloud run services update-traffic evydentia-backend-demo --project=evydentia-demo --region=us-central1 --to-latest
```

### 6.4 Volver atrás

```powershell
# La etiqueta "anterior" la dejó el paso 1 de 6.3 en Cloud Run; este bloque no hereda nada de aquel.
gcloud run services update-traffic evydentia-backend-demo --project=evydentia-demo --region=us-central1 --to-tags="anterior=100"
```

La base no se baja de versión. Si hace falta, se restaura la copia de 6.2 (`gcloud sql backups restore`). Esa decisión es del propietario.

### 6.5 Registro

Una fila por cada migración de la demo. `REGISTRO_MIGRACIONES_MANUALES.md` es solo para bases de pruebas (su regla 4), así que la demo lleva aquí su propio registro. Sin credenciales.

| Fecha | Commit | Digest | Revisiones antes | Revisiones después | Quién aplicó | Confirmación |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
