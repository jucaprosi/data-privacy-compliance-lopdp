# Brief del propietario · Habilitar Vertex AI para EVYDENTIA

> **Aplica a PRODUCCIÓN. No ejecutar hasta el despliegue real (GCP-07) y con autorización del propietario. Para el humo de IA-03b use `EVIDENCIA_HUMO_VERTEX.md` (proyecto de pruebas con guarda).**
>
> Guarda invertida obligatoria antes de cualquier comando de este brief: si el proyecto es el de producción, la ejecución se detiene salvo confirmación escrita del propietario.
>
> ```powershell
> $PROYECTO = "evydentia"
> if ($PROYECTO -eq "evydentia") { throw "PRODUCCIÓN: no ejecutar sin autorización escrita del propietario (GCP-07)." }
> ```

Fecha: 2026-11-09. Redactado por el Arquitecto ADPA para el Tech Lead. Lo ejecuta el propietario (con Antigravity o desde PowerShell). El Arquitecto y los ingenieros no ejecutan nada de esto.

## Qué se hace y por qué
La IA de EVYDENTIA (preanálisis, plan de mitigación, roadmap y asistente) debe correr solo sobre Gemini en Vertex AI, sin ninguna clave de API. El backend se identifica con la cuenta de servicio `sa-evydentia-backend` (credenciales por defecto de Cloud Run). Hoy la API de Vertex AI no está habilitada y esa cuenta no tiene ningún rol de Vertex, así que hay que hacer dos cosas.

Qué no hace este brief: no crea claves, no cambia el ingress, no toca la base de datos ni las demás cuentas de servicio.

## Valores
- Proyecto: `evydentia`
- Cuenta de servicio: `sa-evydentia-backend@evydentia.iam.gserviceaccount.com`
- Región de la inferencia: `us-central1`

## Pasos (PowerShell, copiar y pegar completos)

### 1. Comprobar el estado actual (solo lectura)
```powershell
$PROYECTO = "evydentia"
$SA = "sa-evydentia-backend@evydentia.iam.gserviceaccount.com"
gcloud services list --enabled --project=$PROYECTO --filter="config.name:aiplatform.googleapis.com" --format="value(config.name)"
gcloud projects get-iam-policy $PROYECTO --flatten="bindings[].members" --filter="bindings.members:serviceAccount:$SA" --format="table(bindings.role)"
```
Resultado esperado hoy: el primer comando no imprime nada y el segundo no lista `roles/aiplatform.user`.

### 2. Habilitar la API de Vertex AI
```powershell
$PROYECTO = "evydentia"
gcloud services enable aiplatform.googleapis.com --project=$PROYECTO
```

### 3. Dar el rol mínimo a la cuenta de servicio del backend
```powershell
$PROYECTO = "evydentia"
$SA = "sa-evydentia-backend@evydentia.iam.gserviceaccount.com"
gcloud projects add-iam-policy-binding $PROYECTO --member="serviceAccount:$SA" --role="roles/aiplatform.user" --condition=None
```
`roles/aiplatform.user` basta para llamar a los modelos. No des `roles/aiplatform.admin` ni `roles/owner`.

### 4. Comprobar que quedó
```powershell
$PROYECTO = "evydentia"
$SA = "sa-evydentia-backend@evydentia.iam.gserviceaccount.com"
gcloud services list --enabled --project=$PROYECTO --filter="config.name:aiplatform.googleapis.com" --format="value(config.name)"
gcloud projects get-iam-policy $PROYECTO --flatten="bindings[].members" --filter="bindings.members:serviceAccount:$SA AND bindings.role:roles/aiplatform.user" --format="value(bindings.role)"
```
Resultado esperado: `aiplatform.googleapis.com` y `roles/aiplatform.user`.

### 5. Variables del servicio de Cloud Run
Dos variables, sin ninguna clave. Las aplica el propietario por la vía habitual del despliegue (el brief de GCP):
- `GOOGLE_CLOUD_PROJECT=evydentia`
- `VERTEX_LOCATION=us-central1`

Las únicas variables de inferencia requeridas en Cloud Run son `GOOGLE_CLOUD_PROJECT` y `VERTEX_LOCATION`, usando Application Default Credentials (ADC) de la cuenta de servicio.

## Verificación de variables de inferencia en Cloud Run
Todos los servicios de inferencia de EVYDENTIA (backend, jobs y pruebas) operan únicamente mediante Vertex AI y `features/inferencia`. Para inspeccionar las variables declaradas en solo lectura:
```powershell
$PROYECTO = "evydentia"
$REGION = "us-central1"
gcloud run services list --project=$PROYECTO --region=$REGION --format="value(metadata.name)"
gcloud run services describe evydentia-backend --project=$PROYECTO --region=$REGION --format="yaml(spec.template.spec.containers[0].env)"
```
En la lista de variables solo deben figurar `GOOGLE_CLOUD_PROJECT` y `VERTEX_LOCATION` para inferencia, sin claves API estáticas.

## Prueba de humo y evidencia (IA-03b)
La prueba de humo de la compuerta (`tests/test_ia03_humo_vertex.py`, de IA-03) se corre **en el proyecto de pruebas, no en `evydentia`**. El procedimiento completo (API, rol, credencial suplantada sin clave JSON, prueba y limpieza) está en `governance/operaciones/EVIDENCIA_HUMO_VERTEX.md`, pasos 1 a 7. Requisito previo: la credencial de Application Default suplantando la cuenta de servicio de pruebas (paso 5 de ese documento).

Comando completo para pegar tal cual en PowerShell. Corre en un worktree propio fijado a `origin/main` (lo crea si no existe), nunca en la carpeta principal ni con su `.env`; activa el `.venv` del proyecto y solo pide el id del proyecto de pruebas, que no se escribe en el repositorio:

```powershell
$REPO = "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"
$WT = "C:\Users\Juan Carlos\worktrees-evydentia\humo-vertex"
if (-not (Test-Path $WT)) { git -C $REPO fetch origin main; git -C $REPO worktree add --detach $WT origin/main }
cd $WT
& "$REPO\.venv\Scripts\Activate.ps1"
$PROYECTO = Read-Host "Id del proyecto de pruebas (nunca evydentia)"
if ([string]::IsNullOrWhiteSpace($PROYECTO) -or $PROYECTO -eq "evydentia") { throw "Proyecto vacío o de producción: no sigas." }
$env:GOOGLE_CLOUD_PROJECT = $PROYECTO
$env:VERTEX_LOCATION = "us-central1"
$env:VERTEX_HUMO = "1"
python -m pytest tests/test_ia03_humo_vertex.py -v -rs | Tee-Object -FilePath "$env:USERPROFILE\evidencia-humo-vertex.txt"
Remove-Item Env:VERTEX_HUMO, Env:GOOGLE_CLOUD_PROJECT, Env:VERTEX_LOCATION
```

Resultado esperado: `2 passed`. `test_humo_esquema[esquema_ruta0]` es `PropuestaModelo` (preanálisis) y `test_humo_esquema[esquema_ruta1]` es `PlanMitigacionResponse` (plan de mitigación). `2 skipped` significa que `VERTEX_HUMO` no quedó en `1` y la corrida no vale. La salida queda en `%USERPROFILE%\evidencia-humo-vertex.txt`. Antes de enviarla al CTO, sustituye el id del proyecto y cualquier correo por `<proyecto-de-pruebas>` y `<cuenta>`.

**Hasta que el CTO reciba esa evidencia, `IA-04` a `IA-11` no se usan con Vertex real en producción** (ficha `governance/tareas/IA-03b.md`).

## Cómo se comprueba que funciona
La prueba de humo de la sección anterior la ejecuta el propietario. El Tech Lead anota el resultado en la sección «Registro» de `governance/operaciones/EVIDENCIA_HUMO_VERTEX.md`. Ese resultado es evidencia, no árbitro. Si falla con «permission denied» o «API not enabled», se repite el paso 1 de ese documento.

## Si algo sale mal
- «Permission denied» al habilitar la API: la cuenta del propietario necesita `roles/serviceusage.serviceUsageAdmin` o ser propietaria del proyecto.
- «Model not found» en la prueba de humo: avisa al Arquitecto antes de cambiar la región; no se prueban otras regiones por cuenta propia.

## Reversión
```powershell
$PROYECTO = "evydentia"
$SA = "sa-evydentia-backend@evydentia.iam.gserviceaccount.com"
gcloud projects remove-iam-policy-binding $PROYECTO --member="serviceAccount:$SA" --role="roles/aiplatform.user"
```
La API puede quedar habilitada sin riesgo: no genera costo por sí sola.
