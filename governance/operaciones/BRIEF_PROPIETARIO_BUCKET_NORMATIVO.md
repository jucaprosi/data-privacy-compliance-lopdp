# Brief del propietario · Bucket del corpus normativo y cuenta del monitoreo (NORM-01)

Fecha: 2026-11-12. Redactado por el Arquitecto ADPA para el Tech Lead. Lo ejecuta el propietario (o quien provisiona el entorno). Ninguna sesión de IA ejecuta nada de esto. NORM-01 no entra en tanda hasta que el propietario confirme el paso 6.

## Qué se hace y por qué
NORM-01 descarga las resoluciones, el marco normativo y las consultas absueltas publicados por la SPDP, comprueba que cada archivo sea un PDF, calcula su SHA-256 y guarda el original intacto en Google Cloud Storage, con el hash como nombre (`gs://evydentia-corpus-normativo/spdp/<sha256>.pdf`). El original es la prueba de lo que publicó la autoridad en una fecha, así que se escribe una sola vez y no se sobrescribe ni se borra. El corpus es público y común a todas las organizaciones: no contiene datos de clientes ni datos personales de titulares.

## Lo que medí en solo lectura (proyecto `evydentia`, 2026-11-12)
- Buckets del proyecto: `gs://evydentia` y `gs://lopdp360-vault-long-retention`, los dos en us-central1. No existe `gs://evydentia-corpus-normativo`, y `describe` responde 404, así que el nombre está libre.
- Cuentas de servicio: `sa-github-actions`, `sa-evydentia-web`, `sa-evydentia-backend`, `sa-evydentia-migrator` y la de Compute por defecto. No existe una cuenta para el proceso de monitoreo.
- APIs habilitadas: `storage`, `run` e `iamcredentials`. **Cloud Scheduler no está habilitada** (`cloudscheduler.googleapis.com`).
- Cloud Run Jobs: solo `evydentia-migrate`.

## Decisiones de diseño
1. **Bucket propio** `evydentia-corpus-normativo`, separado de las evidencias de los clientes, porque tiene otro ciclo de vida y otro dueño de escritura. No se usa `gs://evydentia`, sobre el que el backend tiene `objectAdmin`.
2. **Región `us-central1`**, la misma de Cloud Run y Cloud SQL. Como el corpus es público, no hay transferencia de datos personales.
3. **Escritura única por permisos, sin retención bloqueada.** El original no se borra porque nadie tiene el permiso de borrar, no porque haya una política de retención. No hace falta retención: no hay un plazo legal que cumplir para un documento público, y bloquear es irreversible. **No actives `--retention-period` ni `--lock-retention-period`.**
4. **Cuenta propia del monitoreo,** `sa-evydentia-normativa`, con un rol personalizado `corpusNormativoEscritura` que trae solo `storage.objects.create` y `storage.objects.get`. No lleva `delete` ni `update`, así que no puede sobrescribir. La deduplicación por hash usa `get`: si el objeto existe, no se vuelve a subir. NORM-01 sube además con la condición `if_generation_match=0`, que rechaza sobrescribir aunque el permiso lo permitiera.
5. **El backend solo lee:** `sa-evydentia-backend` recibe `roles/storage.objectViewer` sobre este bucket, para que NORM-02 y NORM-03 muestren el original. No recibe ningún permiso de escritura.
6. **Papelera de 7 días, la que viene por defecto,** y sin versionado. Como nadie puede borrar, la papelera solo cubre un error del propio propietario. Y como los nombres son el hash, no hay sobrescrituras que versionar.
7. **Acceso uniforme y prevención de acceso público.** El corpus es público en su origen, pero esta copia es de custodia, no de distribución.
8. **Sin claves de cuenta de servicio.** El Job usa la identidad de su cuenta.

## Fuera de este brief (van con el despliegue de NORM-01, en otro brief)
- El Cloud Run Job del monitoreo, su programación diaria a las 05:00 en America/Guayaquil y la habilitación de la API de Cloud Scheduler.
- El rol de base de datos con el que escribe el monitoreo. `lopdp_app` solo lee las tablas normativas; ese rol lo crea la migración de NORM-01, y su credencial, si hace falta una, se trata como secreto en el brief del despliegue.
- El uso del conector frente a los términos del sitio de la SPDP: es ESTIMADO y está en las preguntas al abogado.

## Valores (sustituye antes de pegar)
- `$PROYECTO`: `evydentia` (producción) o el proyecto de pruebas. La demo no necesita su propio corpus: el corpus es común y la demo lo lee de producción.
- `$BUCKET`: `evydentia-corpus-normativo` (producción) o `evydentia-pruebas-corpus-normativo` (pruebas).
- `$REGION`: `us-central1`.
- `$SA_MONITOREO`: `sa-evydentia-normativa@<proyecto>.iam.gserviceaccount.com`.
- `$SA_BACKEND`: `sa-evydentia-backend@<proyecto>.iam.gserviceaccount.com`.

Antes de pegar un comando con banderas nuevas, confirma con `--help` que tu versión de `gcloud` las acepta.

## Pasos (PowerShell, copiar y pegar completos)

### 1. Confirmar el proyecto y que el nombre sigue libre
```powershell
$PROYECTO = "<proyecto-del-entorno>"
$BUCKET = "<evydentia-corpus-normativo o el de pruebas>"
gcloud projects describe $PROYECTO --format="value(projectId)"
gcloud storage buckets describe "gs://$BUCKET" --format="value(name)"
```
El segundo comando tiene que responder 404 («not found»). Si responde 403 o el nombre del bucket, para y avisa al CTO: el nombre es de otro.

### 2. Crear el bucket
```powershell
$PROYECTO = "<proyecto-del-entorno>"
$BUCKET = "<mismo-bucket>"
$REGION = "us-central1"
gcloud storage buckets create "gs://$BUCKET" --project=$PROYECTO --location=$REGION --default-storage-class=STANDARD --uniform-bucket-level-access --public-access-prevention
```
No añadas `--retention-period`, `--lock-retention-period` ni el versionado.

### 3. Crear la cuenta del monitoreo
```powershell
$PROYECTO = "<proyecto-del-entorno>"
gcloud iam service-accounts create sa-evydentia-normativa --project=$PROYECTO --display-name="EVYDENTIA monitoreo normativo" --description="Descarga y custodia el corpus normativo publico (NORM-01); sin acceso a datos de clientes"
```
No crees ninguna clave para esta cuenta.

### 4. Rol de escritura única y permisos sobre el bucket
```powershell
$PROYECTO = "<proyecto-del-entorno>"
$BUCKET = "<mismo-bucket>"
$SA_MONITOREO = "sa-evydentia-normativa@<proyecto>.iam.gserviceaccount.com"
$SA_BACKEND = "sa-evydentia-backend@<proyecto>.iam.gserviceaccount.com"
gcloud iam roles create corpusNormativoEscritura --project=$PROYECTO --title="Corpus normativo: escritura unica" --description="Crear y leer objetos del corpus; nunca borrar ni sobrescribir" --permissions="storage.objects.create,storage.objects.get" --stage=GA
gcloud storage buckets add-iam-policy-binding "gs://$BUCKET" --member="serviceAccount:$SA_MONITOREO" --role="projects/$PROYECTO/roles/corpusNormativoEscritura"
gcloud storage buckets add-iam-policy-binding "gs://$BUCKET" --member="serviceAccount:$SA_BACKEND" --role="roles/storage.objectViewer"
```
No uses `objectAdmin`, `objectUser` ni `objectCreator` en este bucket. `objectCreator` alcanzaría para crear, pero sin `get` la deduplicación no funciona.

### 5. Comprobación en solo lectura
```powershell
$PROYECTO = "<proyecto-del-entorno>"
$BUCKET = "<mismo-bucket>"
gcloud storage buckets describe "gs://$BUCKET" --format="yaml(name,location,default_storage_class,uniform_bucket_level_access,public_access_prevention,retention_policy,soft_delete_policy,versioning_enabled)"
gcloud storage buckets get-iam-policy "gs://$BUCKET" --format="yaml(bindings)"
gcloud iam roles describe corpusNormativoEscritura --project=$PROYECTO --format="yaml(includedPermissions,stage)"
gcloud iam service-accounts keys list --iam-account="sa-evydentia-normativa@$PROYECTO.iam.gserviceaccount.com" --managed-by=user --format="value(name)"
```
Resultado esperado:
- `location: US-CENTRAL1`, acceso uniforme, `public_access_prevention: enforced`, sin `retention_policy`, papelera de 7 días y sin versionado;
- en el bucket, solo dos asignaciones nuestras: `sa-evydentia-normativa` con `corpusNormativoEscritura` y `sa-evydentia-backend` con `objectViewer`, además de las heredadas del proyecto;
- el rol con exactamente `storage.objects.create` y `storage.objects.get`;
- ninguna clave creada por el usuario para la cuenta del monitoreo (el último comando no imprime nada).

### 6. Confirmación al Tech Lead
Pega la salida del paso 5, sin datos sensibles, en el chat del Tech Lead, con la frase «Compuerta de NORM-01 cumplida en <proyecto>». Con eso NORM-01 puede entrar en tanda.

## Si algo sale mal
- «Bucket name already exists» o 403 en el paso 1: los nombres son globales; avisa al CTO antes de elegir otro, porque el nombre está en el PRD y en la ficha.
- «Role already exists» en el paso 4: el rol es del proyecto; si ya existe, comprueba sus permisos con `gcloud iam roles describe` y sigue con las dos asignaciones.
- Una bandera no existe en tu `gcloud`: actualiza con `gcloud components update` y repite.

## Reversión
Mientras el bucket esté vacío, se puede borrar:
```powershell
$BUCKET = "<mismo-bucket>"
gcloud storage ls "gs://$BUCKET" --recursive --format="value(name)" | Measure-Object | Select-Object -ExpandProperty Count
```
Si da 0, `gcloud storage buckets delete "gs://$BUCKET"` lo retira; la cuenta y el rol se retiran con `gcloud iam service-accounts delete` y `gcloud iam roles delete`. Si ya tiene originales, **no lo borres**: avisa al CTO, porque son la custodia del corpus.
