# Brief del propietario · Vertex AI para EVYDENTIA en `us` y `us-central1` (IA-16)

> **Lo ejecuta el propietario** (con Antigravity o desde PowerShell), **después de fusionar IA-13 e IA-14**. Ninguna sesión de IA toca GCP.
> Este brief reemplaza al anterior (solo producción, generaba en `us-central1` y no corría el humo en `evydentia`).
> Los pasos que cambian producción (`evydentia`) requieren su autorización escrita (GCP-07).

## Qué se hace y por qué
Los modelos gemini-2.5 se retiraron y Vertex responde 404. Decisión del propietario, confirmada al CTO (2026-11-23): un solo modelo, `gemini-3.8-flash`, en la multirregión `us` para generar, y los vectores en `us-central1`. El backend lo lee de dos variables, sin ninguna clave de API (credenciales por defecto de Cloud Run):

| Variable | Valor | Uso |
| :--- | :--- | :--- |
| `VERTEX_LOCATION` | `us` | generación (preanálisis, plan de mitigación, hoja de ruta, asistente) |
| `VERTEX_LOCATION_EMBEDDING` | `us-central1` | vectores |

Entornos con inferencia:

| Entorno | Proyecto | Servicio de Cloud Run |
| :--- | :--- | :--- |
| Demo | `evydentia-demo` | `evydentia-backend-demo` |
| Pruebas | `evydentia-pruebas` | `evydentia-backend` |
| Producción | `evydentia` | `evydentia-backend` |

## Lo que ya pasó en el humo (2026-11-23, propietario, código de `main` bef495e0)
- `3 passed` en `evydentia-demo`, `evydentia-pruebas` y `evydentia` (dos esquemas de generación y uno de vectores).
- En `evydentia-pruebas` la primera corrida dio `403 SERVICE_DISABLED` porque `aiplatform.googleapis.com` no estaba habilitada. Se habilitó con `gcloud services enable aiplatform.googleapis.com --project=evydentia-pruebas` y la repetición dio `3 passed`. Por eso el paso 1 comprueba la API en los tres proyectos antes del humo.

## Pasos (PowerShell, cada bloque completo y pegable)

### 1. Comprobar que la API de Vertex AI está habilitada en los tres proyectos (solo lectura)
```powershell
foreach ($PROYECTO in "evydentia-demo", "evydentia-pruebas", "evydentia") {
  "== $PROYECTO"
  gcloud services list --enabled --project=$PROYECTO --filter="config.name:aiplatform.googleapis.com" --format="value(config.name)"
}
```
Resultado esperado: `aiplatform.googleapis.com` bajo cada proyecto. Si falta alguno, habilítala (no genera costo por sí sola):
```powershell
$PROYECTO = "evydentia-pruebas"
gcloud services enable aiplatform.googleapis.com --project=$PROYECTO
```

### 2. Variables del servicio de Cloud Run
La demo ya las declara en `governance/operaciones/entornos/demo/cloudrun_backend.yaml`: aplica ese manifiesto por la vía habitual del despliegue (el valor vivo de la revisión 00011-4s5 era `us-central1` y faltaba la segunda variable). En pruebas y producción faltan las dos; añádelas al servicio:
```powershell
$PROYECTO = "evydentia-pruebas"
$REGION = "us-central1"
gcloud run services update evydentia-backend --project=$PROYECTO --region=$REGION --update-env-vars="VERTEX_LOCATION=us,VERTEX_LOCATION_EMBEDDING=us-central1"
```
Repite con `$PROYECTO = "evydentia"` (producción, con tu autorización escrita). Comprueba lo que quedó (solo lectura):
```powershell
$PROYECTO = "evydentia-pruebas"
$REGION = "us-central1"
gcloud run services describe evydentia-backend --project=$PROYECTO --region=$REGION --format="yaml(spec.template.spec.containers[0].env)"
```
En las variables de inferencia solo deben figurar `GOOGLE_CLOUD_PROJECT`, `VERTEX_LOCATION` y `VERTEX_LOCATION_EMBEDDING`, sin claves de API.

### 3. Humo real en cada proyecto
En un worktree fijado a `origin/main` y con el `.venv` del proyecto, nunca en la carpeta principal ni con su `.env`. Repite el bloque con cada id de proyecto (`evydentia-demo`, `evydentia-pruebas`, `evydentia`):
```powershell
$REPO = "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"
$WT = "C:\Users\Juan Carlos\worktrees-evydentia\humo-vertex"
if (-not (Test-Path $WT)) { git -C $REPO fetch origin main; git -C $REPO worktree add --detach $WT origin/main } else { git -C $WT fetch origin main; git -C $WT checkout --detach origin/main }
cd $WT
& "$REPO\.venv\Scripts\Activate.ps1"
$env:GOOGLE_CLOUD_PROJECT = "evydentia-pruebas"
$env:VERTEX_LOCATION = "us"
$env:VERTEX_LOCATION_EMBEDDING = "us-central1"
$env:VERTEX_HUMO = "1"
python -m pytest tests/test_ia03_humo_vertex.py -v -rs | Tee-Object -FilePath "$env:USERPROFILE\evidencia-humo-vertex.txt"
Remove-Item Env:VERTEX_HUMO, Env:GOOGLE_CLOUD_PROJECT, Env:VERTEX_LOCATION, Env:VERTEX_LOCATION_EMBEDDING
```
Resultado esperado: `3 passed` (`test_humo_esquema[esquema_ruta0]` y `[esquema_ruta1]` generan; `test_humo_vectores` da los vectores). `skipped` significa que `VERTEX_HUMO` no quedó en `1` y la corrida no vale. Antes de enviar la salida al CTO, sustituye el id del proyecto y cualquier correo por `<proyecto>` y `<cuenta>`. El procedimiento de credencial suplantada está en `governance/operaciones/EVIDENCIA_HUMO_VERTEX.md`.

### 4. Mínimo privilegio (decisión del propietario)
Hoy `roles/editor` basta para llamar a Vertex (los 404 previos no fueron 403). Para dejar el mínimo, concede `roles/aiplatform.user` a la cuenta de servicio de cada servicio y **retira `roles/editor` solo después de que el humo del paso 3 dé `3 passed` sin él**. Obtén la cuenta y concede el rol:
```powershell
$PROYECTO = "evydentia-demo"
$REGION = "us-central1"
$SERVICIO = "evydentia-backend-demo"
$SA = gcloud run services describe $SERVICIO --project=$PROYECTO --region=$REGION --format="value(spec.template.spec.serviceAccountName)"
gcloud projects add-iam-policy-binding $PROYECTO --member="serviceAccount:$SA" --role="roles/aiplatform.user" --condition=None
```
No des `roles/aiplatform.admin` ni `roles/owner`. Repite con cada proyecto y su servicio (pruebas y producción: `evydentia-backend`).

### 5. Anotar la latencia
Anota la latencia de generación y de vectores que mide la ficha IA-13 (R5) en cada entorno y entrégala al CTO junto con la evidencia del humo.

## Si algo sale mal
- `403 SERVICE_DISABLED`: la API no está habilitada en ese proyecto; repite el paso 1.
- `403 permission denied`: falta `roles/aiplatform.user` en la cuenta de servicio, o tu cuenta necesita `roles/serviceusage.serviceUsageAdmin` para habilitar la API.
- `404 model not found`: avisa al Arquitecto antes de cambiar de región o de modelo; no se prueban otras por cuenta propia.
- «inferencia no disponible» en la demo: faltan las variables del paso 2 o el código de IA-13 e IA-14 no está desplegado.

## Reversión
```powershell
$PROYECTO = "evydentia-pruebas"
$REGION = "us-central1"
gcloud run services update evydentia-backend --project=$PROYECTO --region=$REGION --remove-env-vars="VERTEX_LOCATION,VERTEX_LOCATION_EMBEDDING"
```
La API puede quedar habilitada sin riesgo.
