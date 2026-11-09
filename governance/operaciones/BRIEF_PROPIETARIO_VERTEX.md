# Brief del propietario · Habilitar Vertex AI para EVYDENTIA

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

No añadas `OPENAI_API_KEY`, `DEEPSEEK_API_KEY` ni `PREANALISIS_API_KEY`: en EVYDENTIA no existen y la guardia IA-C falla si aparecen.

## Medida provisional (decisión del CTO, 2026-11-09)
Mientras las fichas IA-B1 a IA-B4 no estén fusionadas, **no configures ninguna variable `DEEPSEEK_*` ni `OPENAI_*` en los servicios de Cloud Run de EVYDENTIA** (backend, jobs ni pruebas). Con eso, los caminos que hoy llaman a OpenAI o a DeepSeek quedan apagados y no sale ningún dato de los clientes a otro proveedor. Para comprobarlo, solo lectura:
```powershell
$PROYECTO = "evydentia"
$REGION = "us-central1"
gcloud run services list --project=$PROYECTO --region=$REGION --format="value(metadata.name)"
gcloud run services describe evydentia-backend --project=$PROYECTO --region=$REGION --format="yaml(spec.template.spec.containers[0].env)"
```
En la lista de variables no debe aparecer ningún nombre que empiece por `DEEPSEEK_`, `OPENAI_` ni `PREANALISIS_API_KEY`. Si aparece alguno, avisa al CTO antes de quitarlo.

## Prueba de humo y evidencia (condición para lanzar IA-B1 a IA-B4)
Cuando IA-B0 esté fusionada y desplegada, tú ejecutas una vez la prueba de humo con `VERTEX_HUMO=1` (el ingeniero de IA-B0 te dará el comando exacto en su PR) y entregas al CTO la salida: una llamada estructurada real con el esquema del preanálisis y otra con el del plan de mitigación. **Hasta que el CTO reciba esa evidencia, no se lanzan las fichas IA-B1 a IA-B4.**

## Cómo se comprueba que funciona
La prueba de humo de la sección anterior la ejecuta el propietario; el resultado se anota en la ficha IA-B0 bajo «Evidencia de humo». Ese resultado es evidencia, no árbitro. Si falla con «permission denied» o «API not enabled», se repite el paso 1.

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
