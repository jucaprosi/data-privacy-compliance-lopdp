# Brief del propietario · Bucket de evidencias y firma de URLs V4 (EVI-01)

Fecha: 2026-11-09. Redactado por el Arquitecto ADPA para el Tech Lead. Lo ejecuta el propietario (o quien provisiona el entorno). Ninguna sesión de IA ejecuta nada de esto.

## Qué se hace y por qué
EVI-01 guarda los documentos de evidencia de cada organización en Google Cloud Storage. El navegador los sube y los baja con **URLs firmadas V4**; el servidor descarga el archivo después, calcula su SHA-256 y registra el documento. Un documento registrado no se edita ni se borra, así que el almacén es de **escritura única**.

## Lo que medí en solo lectura (proyecto `evydentia`, 2026-11-09)
- El único bucket del proyecto es `gs://evydentia` (us-central1, STANDARD). Tiene acceso uniforme, prevención de acceso público, papelera de 7 días y **ninguna política de retención**. El backend (`sa-evydentia-backend`) tiene `storage.objectAdmin` sobre él, es decir, puede sobrescribir y borrar. `deploy-gcp.yml` fija hoy `GCP_STORAGE_BUCKET` al ID del proyecto, o sea a ese bucket.
- No existe `lopdp360-vault-long-retention`, el bucket de retención larga del PRD.
- La API `iamcredentials.googleapis.com` ya está habilitada.
- `sa-evydentia-backend` **no** tiene `roles/iam.serviceAccountTokenCreator` sobre sí misma, que hace falta para firmar URLs con credenciales por defecto.
- No hay CORS configurado en ningún bucket.

## Decisiones de diseño
1. **Bucket:** las evidencias van al bucket de retención larga del PRD y de BOV-02, `lopdp360-vault-long-retention` en producción y `lopdp360-pruebas-vault-long-retention` en pruebas (EP-05), con Autoclass, acceso uniforme, sin acceso público y **retención por objeto activada**. **No** se usa `gs://evydentia`, porque el permiso `objectAdmin` del backend sobre él permite sobrescribir y borrar.
2. **Retención por objeto, no una política única del bucket.** El plazo depende del tipo de documento y del paquete contratado: el PRD §2.2 habla de hasta 5, 7 o 10 años según el paquete, y el invariante del pool `long-retention` fija de 3 a 10 años. Por eso el bucket **no lleva política de retención de bucket** (nada de `--retention-period`): la fija la aplicación objeto por objeto, en modo desbloqueado, con **1825 días por defecto** (5 años, el mínimo) y el valor del paquete contratado cuando exista BOV-01. El 1825 vive en un solo lugar del código (`retencion_dias(tenant_id)` de EVI-01a), no en este brief ni en la configuración del bucket. Si la aplicación no logra fijar la retención de un objeto, EVI-01a no registra el documento (falla cerrada).
3. **Sin bloquear.** El modo de retención de cada objeto es **desbloqueado**, y `INV_TEST_ENV_NO_LOCKED_RETENTION` lo exige además en pruebas. Bloquear es irreversible y deja un gravamen que impide borrar el proyecto. **No bloquees nada**, ni por objeto ni por bucket (`--lock-retention-period`). El bloqueo en producción espera la lista de comprobación del final de este brief.
3b. **Escritura única por permisos.** Medí en solo lectura que `storage.objects.setRetention` solo lo incluye el rol predefinido `objectAdmin`, que también incluye `delete` y `update`; `objectCreator` solo trae `create` y `objectViewer` solo `get`. Para fijar la retención sin dar poder de borrar, el backend recibe un **rol personalizado** `evidenciasEscrituraUnica` con `storage.objects.create`, `storage.objects.get` y `storage.objects.setRetention`, y **nada más**: sin `delete`, sin `update`. Si la prueba de EVI-01a en el bucket de pruebas muestra que fijar la retención tras la subida exige otro permiso, se ajusta el rol, y el brief se corrige antes de producción. Además, EVI-01a firma las URLs de subida con la cabecera `x-goog-if-generation-match: 0`, que rechaza sobrescribir un objeto existente.
4. **Firma V4 desde Cloud Run, sin claves:** con la API IAM Credentials (`signBlob`). Para eso la cuenta del backend necesita `roles/iam.serviceAccountTokenCreator` sobre sí misma, concedido sobre el recurso de la cuenta y no sobre el proyecto. No se crea ninguna clave de cuenta de servicio.
5. **Versionado desactivado y papelera en 0.** La retención ya impide borrar antes de tiempo, el versionado duplicaría el almacenamiento y la papelera de 7 días dejaría copias de lo ya purgado, lo que contradice un acta de purga.
6. **Región `us-central1`**, la misma de Cloud Run y Cloud SQL. Los documentos de los clientes quedan en Estados Unidos. Eso se puede declarar como hecho, sacado de la misma configuración; no hay encuadre legal, porque el dictamen del abogado sobre transferencias sigue pendiente.

## Valores (sustituye antes de pegar)
- `$PROYECTO`: `evydentia` (producción) o el proyecto de pruebas. Nunca el de la demo: la demo tiene su propio bucket.
- `$BUCKET`: `lopdp360-vault-long-retention` (producción) o `lopdp360-pruebas-vault-long-retention` (pruebas).
- `$REGION`: `us-central1`.
- `$SA`: `sa-evydentia-backend@<proyecto>.iam.gserviceaccount.com`.
- `$ORIGENES`: los orígenes exactos del frontend de ese entorno, con `https://` y sin comodines.

Antes de pegar cada comando con banderas nuevas, confirma con `gcloud storage buckets create --help` que tu versión las acepta. Las banderas de retención por objeto y de papelera son recientes.

## Pasos (PowerShell, copiar y pegar completos)

### 1. Confirmar el proyecto
```powershell
$PROYECTO = "<proyecto-del-entorno>"
gcloud projects describe $PROYECTO --format="value(projectId)"
gcloud storage buckets list --project=$PROYECTO --format="value(name,location)"
```

### 2. Crear el bucket
```powershell
$PROYECTO = "<proyecto-del-entorno>"
$BUCKET = "<lopdp360-vault-long-retention o el de pruebas>"
$REGION = "us-central1"
gcloud storage buckets create "gs://$BUCKET" --project=$PROYECTO --location=$REGION --default-storage-class=STANDARD --enable-autoclass --uniform-bucket-level-access --public-access-prevention --enable-per-object-retention --soft-delete-duration=0
```
No añadas `--retention-period` ni `--lock-retention-period`, y no actives el versionado.

### 3. CORS para subir y bajar desde el navegador
```powershell
$BUCKET = "<mismo-bucket>"
$ORIGENES = '["https://<origen-exacto-del-frontend>"]'
$CORS = '[{"origin":' + $ORIGENES + ',"method":["PUT","GET","HEAD"],"responseHeader":["Content-Type","x-goog-content-length-range","x-goog-if-generation-match"],"maxAgeSeconds":3600}]'
$ARCHIVO = Join-Path $env:TEMP "cors_evidencias.json"
Set-Content -Path $ARCHIVO -Value $CORS -Encoding ascii
gcloud storage buckets update "gs://$BUCKET" --cors-file=$ARCHIVO
Remove-Item $ARCHIVO
```
Un solo origen por entorno; si hay más, añádelos exactos al arreglo. Sin `*`.

### 4. Permisos del backend sobre el bucket (rol personalizado, sin delete ni update)
```powershell
$PROYECTO = "<proyecto-del-entorno>"
$BUCKET = "<mismo-bucket>"
$SA = "sa-evydentia-backend@<proyecto>.iam.gserviceaccount.com"
gcloud iam roles create evidenciasEscrituraUnica --project=$PROYECTO --title="Evidencias: escritura unica" --description="Crear, leer y fijar la retencion de objetos; nunca borrar ni sobrescribir" --permissions="storage.objects.create,storage.objects.get,storage.objects.setRetention" --stage=GA
gcloud storage buckets add-iam-policy-binding "gs://$BUCKET" --member="serviceAccount:$SA" --role="projects/$PROYECTO/roles/evidenciasEscrituraUnica"
```
El rol es del proyecto: créalo una vez por proyecto y aplícalo a cada bucket de evidencias. No uses `objectAdmin` ni `objectUser`.

### 5. Permiso para firmar URLs con la cuenta del backend
```powershell
$PROYECTO = "<proyecto-del-entorno>"
$SA = "sa-evydentia-backend@<proyecto>.iam.gserviceaccount.com"
gcloud iam service-accounts add-iam-policy-binding $SA --project=$PROYECTO --member="serviceAccount:$SA" --role="roles/iam.serviceAccountTokenCreator"
```
La API `iamcredentials.googleapis.com` ya está habilitada en `evydentia`; en pruebas, compruébalo con `gcloud services list --enabled --project=$PROYECTO --filter="config.name:iamcredentials.googleapis.com"`.

### 6. Comprobación de lectura
```powershell
$BUCKET = "<mismo-bucket>"
$PROYECTO = "<proyecto-del-entorno>"
$SA = "sa-evydentia-backend@<proyecto>.iam.gserviceaccount.com"
gcloud storage buckets describe "gs://$BUCKET" --format="yaml(name,location,default_storage_class,autoclass,uniform_bucket_level_access,public_access_prevention,retention_policy,soft_delete_policy,cors_config,versioning_enabled)"
gcloud storage buckets get-iam-policy "gs://$BUCKET" --format="yaml(bindings)"
gcloud iam service-accounts get-iam-policy $SA --project=$PROYECTO --format="yaml(bindings)"
```
Resultado esperado:
- **sin** `retention_policy` de bucket, y retención por objeto activada (`per_object_retention` o equivalente en tu versión);
- `autoclass` activado, acceso uniforme y `public_access_prevention: enforced`;
- papelera con duración 0 y sin versionado;
- `cors_config` con el origen exacto y los métodos PUT, GET y HEAD;
- el backend con el rol `evidenciasEscrituraUnica` sobre el bucket y sin `objectAdmin` ni `objectUser`;
- el backend con `serviceAccountTokenCreator` sobre su propia cuenta.

### 7. Variable del servicio de Cloud Run (al desplegar EVI-01, no antes)
`GCP_STORAGE_BUCKET` debe valer `$BUCKET`. Hoy `deploy-gcp.yml` la fija al ID del proyecto, que es `gs://evydentia`. Ese cambio de workflow es del propietario y va con el despliegue de EVI-01, no antes. En pruebas y demo cada entorno usa su propio bucket.

### 8. Pendiente sobre `gs://evydentia` (solo después de desplegar EVI-01 con el bucket nuevo)
Hoy el backend tiene `objectAdmin` sobre `gs://evydentia`, que no tiene retención: puede sobrescribir y borrar. Primero comprueba, en solo lectura, que nada lo usa:
```powershell
gcloud storage ls "gs://evydentia" --recursive --format="value(name)" | Measure-Object | Select-Object -ExpandProperty Count
```
Si da 0 o solo trae objetos que ya no se usan, avisa al CTO: él decide si se retira el permiso `objectAdmin` o se cambia a solo lectura. No lo quites tú sin esa confirmación.

## Lista de comprobación antes de BLOQUEAR la retención en producción
No se bloquea nada hasta que se cumplan las tres, y la decisión final es del CTO con el propietario:
- [ ] (a) El abogado confirma el plazo por tipo de documento (3 a 10 años según el invariante; el PRD habla de hasta 5, 7, 10 o personalizado por paquete).
- [ ] (b) El abogado confirma cómo convive una retención inmutable con el derecho de eliminación de la LOPDP cuando una evidencia contenga datos personales de un titular.
- [ ] (c) El propietario decide el momento de salida con clientes reales.
Las preguntas (a) y (b) van al dictamen del abogado, junto con las de Vertex.

## Qué le dices al Tech Lead
- El nombre del bucket de cada entorno y la salida del paso 6 sin datos sensibles. Con eso EVI-01 puede pasar a `hecha`.

## Si algo sale mal
- «Bucket name already exists»: los nombres son globales; avisa al CTO antes de cambiar el nombre.
- Una bandera no existe en tu `gcloud`: actualiza con `gcloud components update` y repite.
- La subida desde el navegador falla con un error de CORS: repite el paso 3 con el origen exacto, sin barra final.
- Aparece `isLocked: true` en la retención: para y avisa al CTO; no se puede deshacer.

## Reversión
No borres el bucket con objetos retenidos: la retención lo impide. En pruebas, la retención de cada objeto está en modo desbloqueado: para vaciarlo hay que retirar antes la retención de cada objeto (con `gcloud storage objects update --clear-retention` sobre los objetos afectados, tras comprobar la bandera con `--help`), y solo si no está bloqueada. Un objeto con retención bloqueada no se puede liberar.
