# Brief del propietario · Bucket de la demo y comprobación de que no tiene retención

Fecha: 2026-11-09. Redactado por el Arquitecto ADPA para el Tech Lead. Lo ejecuta el propietario (o quien provisiona la demo). El resto del equipo no ejecuta nada de esto. Va junto al brief del Cloud Run Job de purga (DEMO-05 y DEMO-07).

## Qué se hace y por qué
La demo guarda sus objetos (por ejemplo, las evidencias ficticias de la plantilla) en un bucket de Cloud Storage **propio de la demo**, en el proyecto de la demo. La purga nocturna tiene que poder borrarlos. Un bucket con política de retención (como el `long-retention` de producción) no deja borrar objetos hasta que venza la retención, y los datos ficticios quedarían inmutables y la purga fallaría. Por eso:
- El bucket de la demo **no tiene política de retención ni bloqueo de objetos.**
- Tiene un ciclo de vida corto, como segunda red de seguridad si la purga fallara.
- El Almacén de la purga comprueba al construirse que el bucket no tiene retención. Si la tiene, se niega a funcionar con un mensaje claro.

Qué no hace este brief: no usa el proyecto de producción, no toca los buckets de producción y no crea claves.

## Valores (parámetros; sustituye por los tuyos antes de pegar)
- `$PROYECTO_DEMO`: el ID del proyecto de la demo. No es `evydentia` (producción).
- `$BUCKET`: el nombre del bucket de la demo. Debe ser único en todo Google Cloud.
- `$REGION`: región del bucket, por defecto `us-central1`.
- `$SA_PURGA`: la cuenta de servicio del Job de purga (la que crea el brief de DEMO-07).
- `$DIAS`: días del ciclo de vida de seguridad, por defecto 3.

## Pasos (PowerShell, copiar y pegar completos)

### 1. Comprobar que no apuntas a producción
```powershell
$PROYECTO_DEMO = "<id-del-proyecto-de-la-demo>"
if ($PROYECTO_DEMO -eq "evydentia") { throw "Este brief es solo para el proyecto de la demo." }
gcloud config get-value project
gcloud projects describe $PROYECTO_DEMO --format="value(projectId)"
```
Debe imprimir el ID de la demo. Si imprime `evydentia`, para.

### 2. Crear el bucket sin retención, con acceso uniforme y sin acceso público
```powershell
$PROYECTO_DEMO = "<id-del-proyecto-de-la-demo>"
$BUCKET = "<nombre-unico-del-bucket-de-la-demo>"
$REGION = "us-central1"
gcloud storage buckets create "gs://$BUCKET" --project=$PROYECTO_DEMO --location=$REGION --uniform-bucket-level-access --public-access-prevention --soft-delete-duration=0
```
No uses `--retention-period`, ni bloqueo de objetos, ni retención por defecto. `--soft-delete-duration=0` desactiva la papelera de recuperación del bucket: los datos son ficticios y lo borrado debe desaparecer.

### 3. Ciclo de vida corto, como segunda red
```powershell
$BUCKET = "<nombre-unico-del-bucket-de-la-demo>"
$DIAS = 3
$REGLA = '{"rule":[{"action":{"type":"Delete"},"condition":{"age":' + $DIAS + '}}]}'
$ARCHIVO = Join-Path $env:TEMP "ciclo_vida_demo.json"
Set-Content -Path $ARCHIVO -Value $REGLA -Encoding ascii
gcloud storage buckets update "gs://$BUCKET" --lifecycle-file=$ARCHIVO
Remove-Item $ARCHIVO
```

### 3b. Dar a la cuenta de purga el permiso solo sobre este bucket
```powershell
$BUCKET = "<nombre-unico-del-bucket-de-la-demo>"
$SA_PURGA = "<cuenta-de-servicio-del-job-de-purga>@<id-del-proyecto-de-la-demo>.iam.gserviceaccount.com"
gcloud storage buckets add-iam-policy-binding "gs://$BUCKET" --member="serviceAccount:$SA_PURGA" --role="roles/storage.objectAdmin"
```
Solo sobre este bucket, no sobre el proyecto. El permiso de la cuenta que escribe los objetos de la demo (la clonación de evidencias, DEMO-03e) lo da el brief de esa ficha.

### 4. Comprobación de lectura (solo lectura): que NO hay retención
```powershell
$BUCKET = "<nombre-unico-del-bucket-de-la-demo>"
gcloud storage buckets describe "gs://$BUCKET" --format="yaml(name,location,retention_policy,default_event_based_hold,lifecycle_config,uniform_bucket_level_access,public_access_prevention,soft_delete_policy,versioning)"
```
Resultado esperado:
- **No aparece** `retention_policy`.
- `default_event_based_hold` ausente o `false`.
- `lifecycle_config` con la regla `Delete` de `$DIAS` días.
- `uniform_bucket_level_access` activo y `public_access_prevention` en `enforced`.
- `soft_delete_policy` con duración 0.
- **No aparece** `versioning` (o está desactivado): con el versionado de objetos activo, borrar un objeto deja versiones no vigentes que la purga no ve, y el Job se niega a arrancar (PR #575).
Si aparece `retention_policy`, no lo desbloquees tú: avisa al CTO.

### 5. Dar el nombre del bucket al Job
El nombre va en la variable `PURGA_BUCKETS` del Cloud Run Job de la purga, sin respaldo a ninguna otra variable. La fija el brief de DEMO-07.

## Qué le dices al Tech Lead
- El nombre del bucket, el proyecto y la salida del paso 4 sin datos sensibles.
- Con eso queda cumplida la condición de que DEMO-05 pase a hecha y se despliegue el Job.

## Si algo sale mal
- «Bucket name already exists»: elige otro nombre; los nombres son globales.
- El paso 4 muestra `retention_policy`: para y avisa al CTO.
- El Job se niega a arrancar con «el bucket tiene política de retención»: es el comportamiento esperado; repite el paso 4.

## Reversión
```powershell
$BUCKET = "<nombre-unico-del-bucket-de-la-demo>"
gcloud storage rm --recursive "gs://$BUCKET"
```
Solo sobre el bucket de la demo y solo con datos ficticios.
