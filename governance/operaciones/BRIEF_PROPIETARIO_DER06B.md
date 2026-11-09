# Brief del propietario · Activar los tipos nuevos de solicitud (DER-06b)

Fecha: 2026-11-09. Redactado por el Arquitecto ADPA para el Tech Lead. Lo ejecuta el propietario. El resto del equipo no ejecuta nada de esto. Todos los comandos son de solo lectura.

## Qué decide este brief y por qué
DER-06a añadió al tipo nativo de PostgreSQL `tiposolicitud` tres valores nuevos (suspensión, decisiones automatizadas y queja), pero el sistema todavía no deja crear solicitudes con ellos. DER-06b los activa. Si una fila con un valor nuevo existe y alguna revisión de Cloud Run que no conoce ese valor la lee, esa revisión falla al listar solicitudes. PostgreSQL no permite retirar valores de un tipo nativo, así que no hay vuelta atrás limpia.

**Condición para lanzar DER-06b:** ninguna revisión de `evydentia-backend` que pueda volver a recibir tráfico es anterior al despliegue de DER-06a. Eso incluye la revisión estable a la que revierte el despliegue progresivo (GCP-07), porque una reversión por SLO le devolvería el 100 % del tráfico.

Qué no hace este brief: no despliega, no cambia tráfico, no toca la base de datos ni ejecuta migraciones.

## Valores
- Proyecto: `evydentia`
- Región: `us-central1`
- Servicio: `evydentia-backend`

## Pasos (PowerShell, copiar y pegar completos)

### 1. Ver cómo se reparte el tráfico ahora
```powershell
$PROYECTO = "evydentia"
$REGION = "us-central1"
$SERVICIO = "evydentia-backend"
gcloud run services describe $SERVICIO --project=$PROYECTO --region=$REGION --format="yaml(status.traffic)"
```
Debe haber una sola revisión con `percent: 100`. Apunta su nombre: es la revisión que sirve hoy.

### 2. Ver las revisiones, su fecha y su imagen
```powershell
$PROYECTO = "evydentia"
$REGION = "us-central1"
$SERVICIO = "evydentia-backend"
gcloud run revisions list --service=$SERVICIO --project=$PROYECTO --region=$REGION --format="table(metadata.name,metadata.creationTimestamp,spec.containers[0].image)"
```
Compara la fecha y la imagen de cada revisión con el momento en que se desplegó DER-06a (el PR de DER-06a fusionado en `main` y su despliegue). La revisión que sirve hoy y la que usaría una reversión tienen que ser **posteriores** a ese despliegue.

### 3. Confirmar a qué revisión revierte el despliegue
La reversión del despliegue progresivo devuelve el tráfico a la «revisión estable». Pregúntale a quien ejecutó el último despliegue cuál anotó como estable, o usa la del paso 1 si el último escalón llegó al 100 %. Si la revisión estable es anterior a DER-06a, no sigas: despliega primero una revisión con DER-06a hasta el 100 % y repite.

### 4. Comprobar que el tipo de la base ya tiene los valores
Este comando lo ejecutas contra la base de pruebas (`evydentia-pruebas`) con la conexión que ya usas; no lo ejecutes contra producción si no tienes la ficha DER-06a aplicada allí:
```powershell
$CONSULTA = "SELECT unnest(enum_range(NULL::tiposolicitud));"
Write-Output $CONSULTA
```
Pégala en tu cliente de base de datos habitual. Debe listar ocho valores: ACCESO, RECTIFICACION, CANCELACION, OPOSICION, PORTABILIDAD y los tres nuevos.

## Qué le dices al Tech Lead
- «La revisión que sirve y la revisión estable son posteriores a DER-06a», con sus nombres y fechas, o «no lo son».
- Con eso, el Tech Lead libera DER-06b y marca la condición en la ficha.

## Si algo sale mal
- Hay dos revisiones con tráfico: espera a que el escalón llegue al 100 % y repite.
- La revisión estable es anterior a DER-06a: no actives los tipos; despliega primero.
- Una solicitud con un tipo nuevo ya existe antes de tiempo: avisa al Arquitecto y al CTO antes de tocar nada.
