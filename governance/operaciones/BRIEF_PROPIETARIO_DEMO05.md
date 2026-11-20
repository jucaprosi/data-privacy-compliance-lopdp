# Brief del propietario · Cloud Run Job de purga nocturna de la demo (DEMO-05)

Fecha: 2026-11-09. Redactado por el Tech Lead a partir del PR #570 (sesión de DEMO-05) y de las decisiones del Arquitecto ADPA y del CTO. Lo ejecuta el propietario en Google Cloud (con Antigravity o desde PowerShell). **Ninguna IA crea estos recursos ni toca la base de datos de la demo.** Va junto al brief del bucket (`BRIEF_PROPIETARIO_BUCKET_DEMO.md`); el bucket se crea primero.

## Qué se hace y por qué
La aplicación nunca borra (invariante 63). La purga física de las demos vencidas la hace un Cloud Run Job aparte, con su propia cuenta de servicio y una credencial de base de datos que la aplicación no tiene. Cada noche borra, por cada demo vencida, los objetos del bucket con prefijo `tenant_id/` y las filas del tenant, y comprueba que no queda nada; si queda algo, revierte y sale con error.

**Reglas de seguridad que el propio Job hace cumplir** (si alguna falla, el Job sale con código 1 y no purga):
- `APP_ENV=demo`, y la huella del proyecto de producción definida y distinta del proyecto donde corre;
- la URL de la base no nombra la instancia ni la huella de producción;
- la base tiene `public.entorno_marcador` con **exactamente** una fila `demo` (no `pruebas`);
- los buckets de `PURGA_BUCKETS` no tienen política de retención ni bloqueo.
- el rol de purga tiene los permisos y las políticas de `politicas_purga.sql` en todas las tablas que purga, `es_persona_ficticia` es `SECURITY DEFINER` sin `EXECUTE` para `PUBLIC`, y el rol no lee `users.email` (DEMO-05c).

**Qué no hace este brief:** no usa el proyecto de producción, no crea claves de cuentas de servicio, no activa la RLS de ninguna tabla, no toca la base de producción y no despliega la aplicación.

## Valores (parámetros; sustituye por los tuyos antes de pegar)
- `$PROYECTO_DEMO`: ID del proyecto de la demo. **No es `evydentia`.**
- `$PROYECTO_PROD`: ID del proyecto de producción (`evydentia`); solo se usa como valor de `HUELLA_PROYECTO_PRODUCCION`.
- `$REGION`: `us-central1`.
- `$SA`: cuenta de servicio del Job, propuesta `purga-demo@$PROYECTO_DEMO.iam.gserviceaccount.com`.
- `$SA_SCHEDULER`: cuenta con la que el Scheduler lanza el Job (una cuenta propia, sin otros usos).
- `$BUCKETS`: nombres de los buckets de la demo separados por coma (los del brief del bucket).
- `$INSTANCIA`: instancia de Cloud SQL de la demo (`proyecto:region:nombre`). **No es** `evydentia:us-central1:evydentia-production`.
- `$IMAGEN`: imagen del Job en el Artifact Registry del proyecto de la demo.

## Pasos (PowerShell, copiar y pegar completos)

### 1. Comprobar que no apuntas a producción (solo lectura)
```powershell
$PROYECTO_DEMO = "<id-del-proyecto-de-la-demo>"
if ($PROYECTO_DEMO -eq "evydentia") { throw "Este brief es solo para el proyecto de la demo." }
gcloud projects describe $PROYECTO_DEMO --format="value(projectId)"
gcloud sql instances list --project=$PROYECTO_DEMO --format="table(name,region,state)"
```
Debe imprimir el ID de la demo y la instancia de la demo. Si aparece `evydentia-production`, para.

### 2. Cuenta de servicio del Job, con los permisos mínimos
```powershell
$PROYECTO_DEMO = "<id-del-proyecto-de-la-demo>"
$SA = "purga-demo@$PROYECTO_DEMO.iam.gserviceaccount.com"
gcloud iam service-accounts create purga-demo --project=$PROYECTO_DEMO --display-name="Purga nocturna de la demo"
gcloud projects add-iam-policy-binding $PROYECTO_DEMO --member="serviceAccount:$SA" --role="roles/cloudsql.client" --condition=None
```
Los permisos sobre el secreto y sobre el bucket se dan en sus pasos, acotados a cada recurso. No se crea ninguna clave de la cuenta.

### 3. Secreto con la URL de conexión de la base de la demo
La URL usa el rol de purga del paso 5 y la base **de la demo**, nunca la de producción ni la de pruebas. No la pegues en un comando: se escribe en un archivo temporal y se borra.
```powershell
$PROYECTO_DEMO = "<id-del-proyecto-de-la-demo>"
$SA = "purga-demo@$PROYECTO_DEMO.iam.gserviceaccount.com"
$ARCHIVO = Join-Path $env:TEMP "purga_database_url.txt"
$ENTRADA = Read-Host "URL de conexion de la base de la DEMO con el rol de purga" -AsSecureString
$URL = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($ENTRADA))
Set-Content -Path $ARCHIVO -Value $URL -NoNewline -Encoding ascii
gcloud secrets create PURGA_DATABASE_URL --project=$PROYECTO_DEMO --replication-policy=automatic --data-file=$ARCHIVO
Remove-Item $ARCHIVO
gcloud secrets add-iam-policy-binding PURGA_DATABASE_URL --project=$PROYECTO_DEMO --member="serviceAccount:$SA" --role="roles/secretmanager.secretAccessor"
```
Es el único secreto del Job. **No hay claves de almacén:** el Job usa las credenciales por defecto de su cuenta para hablar con Cloud Storage.

### 4. Permiso sobre el bucket de la demo
Se da en el paso 3b de `BRIEF_PROPIETARIO_BUCKET_DEMO.md` (`roles/storage.objectAdmin` solo sobre ese bucket). Si prefieres un rol personalizado, necesita exactamente `storage.buckets.get`, `storage.objects.list` y `storage.objects.delete` sobre esos buckets.

### 5. Rol de purga en la base de la demo (DEMO-05c: políticas explícitas, sin BYPASSRLS)
Decisión del CTO: el rol de purga **no** tiene `BYPASSRLS` ni `SUPERUSER`. Purga con permisos y políticas `TO purga_demo` que solo valen con el marcador `demo`, y nunca lee correos: `users` solo `SELECT (id)` y `demo_sesiones` sin `vendedor_sub` ni `vendedor_email`. Todo eso lo deja `jobs/purga_demo/politicas_purga.sql`, que **no** entra en Alembic.

**5a. Crear el rol (una sola vez).** Conéctate a la base **de la demo** con tu usuario administrador (el mismo que migra) y ejecuta, con una contraseña nueva que solo irá en el secreto del paso 3:
```sql
CREATE ROLE purga_demo LOGIN PASSWORD '<contraseña-nueva>' NOSUPERUSER NOBYPASSRLS NOCREATEROLE NOCREATEDB;
```
Si el rol ya existía de una versión anterior de este brief, quítale lo que ya no necesita (la purga nunca hace `UPDATE`):
```sql
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM purga_demo;
```

**5b. Permisos y políticas: tras CADA migración de la base de la demo.** Desde un checkout actualizado de `main`, en la raíz del repositorio, con `psql` conectado a la base de la demo con tu usuario administrador (por el proxy de Cloud SQL; no pegues la contraseña en el comando):
```powershell
$PSQL_DEMO = "<cadena de conexión psql a la base de la DEMO con tu usuario administrador, sin contraseña>"
psql $PSQL_DEMO --single-transaction -v ON_ERROR_STOP=1 -f jobs/purga_demo/politicas_purga.sql
```
Es idempotente: repetirlo deja lo mismo. Se niega si falta el rol o `public.entorno_marcador`. No activa la RLS de ninguna tabla ni cambia las políticas de otros roles. Una tabla nueva con `tenant_id` queda sin permisos hasta que lo vuelvas a ejecutar, y mientras tanto el Job sale con 1 y la nombra («faltan políticas de purga en: …; ejecuta politicas_purga.sql»).

**5c. Comprobaciones de solo lectura (con la credencial del Job; tras crear el Job en el paso 8).** Ejecuta el Job en modo comprobación: no borra filas ni objetos y solo imprime números y nombres de tablas.
```powershell
$PROYECTO_DEMO = "<id-del-proyecto-de-la-demo>"
$REGION = "us-central1"
gcloud run jobs execute purga-demo --project=$PROYECTO_DEMO --region=$REGION --wait --command=python --args="-m,jobs.purga_demo,--comprobar"
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=purga-demo AND textPayload:comprobacion" --project=$PROYECTO_DEMO --limit=1 --format="value(textPayload)"
```
Resultado esperado: la ejecución termina bien y la línea dice `faltan=0` y `personas_ficticias=` con un número **mayor que 0** (la plantilla y las demos tienen personas `.invalid`). `tablas_sin_rls` cuenta las tablas que aún no tienen RLS (hoy cinco); las protegen los permisos y los filtros del código hasta que la ficha de seguridad les active la RLS.

**Si `faltan` no es 0 o `personas_ficticias=0`: detente y avisa al CTO.** No lances la purga nocturna: en la nube podría no borrar a nadie sin que se note (por ejemplo, si una tabla que lee `es_persona_ficticia` tuviera la RLS forzada y tu usuario no la salta). No des `BYPASSRLS` ni `SUPERUSER` al rol para arreglarlo.

### 6. Marcador de entorno de la base
```sql
SELECT valor FROM public.entorno_marcador;
```
Debe devolver **una sola fila** con el valor `demo`. Si falta la tabla o hay otro valor (por ejemplo `pruebas`), el Job se niega a correr. El marcador lo pone el procedimiento de SEC-20; si no existe, avisa al CTO.

### 7. Imagen del Job
Desde un checkout actualizado de `main`, en la raíz del repositorio:
```powershell
$IMAGEN = "<region>-docker.pkg.dev/<id-del-proyecto-de-la-demo>/<repositorio>/purga-demo:<etiqueta>"
docker build -f jobs/purga_demo/Dockerfile -t $IMAGEN .
gcloud auth configure-docker "<region>-docker.pkg.dev"
docker push $IMAGEN
```
La imagen corre como usuario sin privilegios (uid 10001).

### 8. Crear el Cloud Run Job
Las variables van con un separador distinto de la coma, porque `PURGA_BUCKETS` lleva comas.
```powershell
$PROYECTO_DEMO = "<id-del-proyecto-de-la-demo>"
$PROYECTO_PROD = "evydentia"
$REGION = "us-central1"
$SA = "purga-demo@$PROYECTO_DEMO.iam.gserviceaccount.com"
$IMAGEN = "<la-misma-imagen-del-paso-7>"
$BUCKETS = "<bucket1,bucket2>"
$INSTANCIA = "<proyecto-demo:region:instancia-de-la-demo>"
$VARIABLES = "^@^APP_ENV=demo@HUELLA_PROYECTO_PRODUCCION=$PROYECTO_PROD@PURGA_PROYECTO_DEMO=$PROYECTO_DEMO@PURGA_BUCKETS=$BUCKETS"
gcloud run jobs create purga-demo --project=$PROYECTO_DEMO --region=$REGION --image=$IMAGEN --service-account=$SA --tasks=1 --max-retries=0 --set-env-vars=$VARIABLES --set-secrets="PURGA_DATABASE_URL=PURGA_DATABASE_URL:latest" --set-cloudsql-instances=$INSTANCIA
```
Una sola tarea y sin reintentos: si falla, sale con código 1 y se revisa a mano. Si la URL de conexión no usa el socket de Cloud SQL, quita `--set-cloudsql-instances`.

### 9. Programarlo una vez por noche
```powershell
$PROYECTO_DEMO = "<id-del-proyecto-de-la-demo>"
$REGION = "us-central1"
$SA_SCHEDULER = "<cuenta-del-scheduler>@<id-del-proyecto-de-la-demo>.iam.gserviceaccount.com"
gcloud run jobs add-iam-policy-binding purga-demo --project=$PROYECTO_DEMO --region=$REGION --member="serviceAccount:$SA_SCHEDULER" --role="roles/run.invoker"
gcloud scheduler jobs create http purga-demo-nocturna --project=$PROYECTO_DEMO --location=$REGION --schedule="0 3 * * *" --time-zone="America/Guayaquil" --uri="https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROYECTO_DEMO/jobs/purga-demo:run" --http-method=POST --oauth-service-account-email=$SA_SCHEDULER
```
Sin GitHub Actions ni secretos en GitHub.

### 10. Comprobación (solo lectura)
```powershell
$PROYECTO_DEMO = "<id-del-proyecto-de-la-demo>"
$REGION = "us-central1"
gcloud run jobs describe purga-demo --project=$PROYECTO_DEMO --region=$REGION --format="yaml(spec.template.spec.template.spec.serviceAccountName,spec.template.spec.template.spec.maxRetries,spec.template.spec.taskCount)"
gcloud scheduler jobs describe purga-demo-nocturna --project=$PROYECTO_DEMO --location=$REGION --format="yaml(schedule,timeZone,state)"
gcloud secrets get-iam-policy PURGA_DATABASE_URL --project=$PROYECTO_DEMO --format="yaml(bindings)"
```
Resultado esperado: la cuenta `purga-demo`, `maxRetries: 0`, `taskCount: 1`, la programación `0 3 * * *` en `America/Guayaquil` con estado `ENABLED`, y el secreto leído solo por la cuenta del Job. **No ejecutes el Job** hasta tener las comprobaciones del bucket y del marcador de la base.

## Qué le dices al CTO
- Que el Job, el Scheduler y la cuenta de servicio están creados, la salida del paso 10 y la del paso 4 del brief del bucket, sin secretos ni la URL de conexión.
- La línea de la comprobación del paso 5c (`faltan=…`, `tablas_sin_rls=…`, `personas_ficticias=…`).
- Con eso queda cumplida la condición de que DEMO-05 pase a hecha.

## Si algo sale mal
- El Job sale con 1 y dice «la base no tiene el marcador de entorno exacto 'demo'»: repite el paso 6.
- Sale con 1 y dice que el bucket tiene retención u objetos bloqueados: es el comportamiento esperado; repite el paso 4 del brief del bucket y no desbloquees nada tú: avisa al CTO.
- Sale con 1 y dice que falta `PURGA_BUCKETS`: repite el paso 8.
- Sale con 1 y dice «faltan políticas de purga en: …»: repite el paso 5b (y el 5c).
- Un error de claves foráneas o de permisos de la base: repite el paso 5b; no des `SUPERUSER` ni `BYPASSRLS` al rol de purga.

## Reversión
```powershell
$PROYECTO_DEMO = "<id-del-proyecto-de-la-demo>"
$REGION = "us-central1"
gcloud scheduler jobs delete purga-demo-nocturna --project=$PROYECTO_DEMO --location=$REGION
gcloud run jobs delete purga-demo --project=$PROYECTO_DEMO --region=$REGION
```
Sin el Scheduler no corre nada; las demos vencidas se acumulan hasta que se vuelva a crear. El rol `purga_demo` de la base y el secreto pueden quedarse.
