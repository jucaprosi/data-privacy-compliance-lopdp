# Brief del propietario · Cloud Run Job de purga nocturna de la demo (DEMO-05)

Fecha: 2026-11-09. Redactado por el Tech Lead a partir del PR #570 (sesión de DEMO-05) y de las decisiones del Arquitecto ADPA y del CTO. Lo ejecuta el propietario en Google Cloud (con Antigravity o desde PowerShell). **Ninguna IA crea estos recursos ni toca la base de datos de la demo.** Va junto al brief del bucket (`BRIEF_PROPIETARIO_BUCKET_DEMO.md`); el bucket se crea primero.

## Qué se hace y por qué
La aplicación nunca borra (invariante 63). La purga física de las demos vencidas la hace un Cloud Run Job aparte, con su propia cuenta de servicio y una credencial de base de datos que la aplicación no tiene. Cada noche borra, por cada demo vencida, los objetos del bucket con prefijo `tenant_id/` y las filas del tenant, y comprueba que no queda nada; si queda algo, revierte y sale con error.

**Reglas de seguridad que el propio Job hace cumplir** (si alguna falla, el Job sale con código 1 y no purga):
- `APP_ENV=demo`, y la huella del proyecto de producción definida y distinta del proyecto donde corre;
- la URL de la base no nombra la instancia ni la huella de producción;
- la base tiene `public.entorno_marcador` con **exactamente** una fila `demo` (no `pruebas`);
- los buckets de `PURGA_BUCKETS` no tienen política de retención ni bloqueo.

**Qué no hace este brief:** no usa el proyecto de producción, no crea claves de cuentas de servicio, no toca la RLS ni la base de producción, y no despliega la aplicación.

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

### 5. Rol de purga en la base de la demo
Conéctate a la base de la demo con tu usuario administrador y ejecuta (sustituye la contraseña por una nueva, que solo irá en el secreto del paso 3):
```sql
CREATE ROLE purga_demo LOGIN PASSWORD '<contraseña-nueva>';
GRANT SELECT, DELETE ON tenants TO purga_demo;
GRANT SELECT, UPDATE, DELETE ON demo_sesiones TO purga_demo;
DO $$
DECLARE t text;
BEGIN
  FOR t IN SELECT c.table_name FROM information_schema.columns c
           JOIN information_schema.tables x ON x.table_schema = c.table_schema AND x.table_name = c.table_name
           WHERE c.table_schema = 'public' AND c.column_name = 'tenant_id' AND x.table_type = 'BASE TABLE'
  LOOP
    EXECUTE format('GRANT SELECT, DELETE ON public.%I TO purga_demo', t);
  END LOOP;
END $$;
```
Las tablas con `tenant_id` que se creen después necesitan el mismo `GRANT`: repite el bloque `DO` tras cada migración que añada una.

Cuando la ficha DEMO-05b esté hecha (borra las personas ficticias de `users`), el rol también necesitará `GRANT SELECT, DELETE ON users TO purga_demo;` y `SELECT` en `user_tenant_roles`. Hasta entonces no se concede.

**Decisión tuya, antes de lanzar el Job:** las tablas tienen RLS forzada, y el rol de purga tiene que poder borrar filas de todos los tenants. Las dos salidas son un rol con `BYPASSRLS` o una política de purga explícita para este rol. **Este brief no fija cuál**: no se ha comprobado que Cloud SQL permita `BYPASSRLS` a tu usuario administrador. Consúltalo con el Arquitecto y el CTO. Esta ficha no toca `roles.py`, `fn_utr_dpo_sod` ni la RLS.

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
- Tu decisión sobre la RLS del paso 5.
- Con eso queda cumplida la condición de que DEMO-05 pase a hecha.

## Si algo sale mal
- El Job sale con 1 y dice «la base no tiene el marcador de entorno exacto 'demo'»: repite el paso 6.
- Sale con 1 y dice que el bucket tiene retención u objetos bloqueados: es el comportamiento esperado; repite el paso 4 del brief del bucket y no desbloquees nada tú: avisa al CTO.
- Sale con 1 y dice que falta `PURGA_BUCKETS`: repite el paso 8.
- Un error de claves foráneas o de permisos de la base: repite los `GRANT` del paso 5; no des `SUPERUSER` al rol de purga.

## Reversión
```powershell
$PROYECTO_DEMO = "<id-del-proyecto-de-la-demo>"
$REGION = "us-central1"
gcloud scheduler jobs delete purga-demo-nocturna --project=$PROYECTO_DEMO --location=$REGION
gcloud run jobs delete purga-demo --project=$PROYECTO_DEMO --region=$REGION
```
Sin el Scheduler no corre nada; las demos vencidas se acumulan hasta que se vuelva a crear. El rol `purga_demo` de la base y el secreto pueden quedarse.
