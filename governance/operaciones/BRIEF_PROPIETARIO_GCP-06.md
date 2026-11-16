# Brief del propietario · Cloud CDN para activos estáticos y Memorystore (GCP-06)

Lo ejecuta el propietario (o quien provisiona el entorno). Ninguna sesión de IA ejecuta nada de esto. Decisión del propietario (2026-11-13): **pruebas ahora, producción en la beta.**

## Qué se hace y por qué
Cloud CDN solo cachea `/_next/static/*` (activos inmutables) en `evydentia-web-bs`; `/api/v1/*` nunca entra en el CDN. Memorystore (Redis) guarda la caché de lectura del servidor con clave `cache:v1:{tenant_id}:{recurso}:{version}` (`app_core/cache`). El código funciona sin Redis: sin `REDIS_URL` usa memoria local por proceso, así que crear Memorystore no bloquea nada. La aplicación aún no se conecta a Memorystore; este paso solo lo crea.

## Valores (sustituye antes de pegar)
- `$PROYECTO`: el proyecto de **PRUEBAS** (`PROYECTO_PRUEBAS`, ver `ENTORNO_DE_PRUEBAS.md`). Nunca el de la demo.
- `$REGION`: `us-central1`. `$RED`: la red del entorno (confírmala con el paso 1).
- Los nombres de servicio backend del balanceador de pruebas: confírmalos con el paso 1; aquí se usan `evydentia-web-bs` y `evydentia-backend-bs`.

Antes de pegar cada comando, confirma las banderas con `gcloud <comando> --help`. No medí nada en vivo.

## Parte A · PRUEBAS (esta es la que se ejecuta ahora)

### 1. Lectura previa y guarda
```powershell
$PROYECTO = "<proyecto-de-pruebas>"
if ($PROYECTO -eq "evydentia" -or $PROYECTO -like "<*") { throw "Parte A es solo para PRUEBAS: pon el proyecto de pruebas, no evydentia." }
gcloud compute backend-services list --global --project=$PROYECTO --format="value(name,enableCDN)"
gcloud redis instances list --region=us-central1 --project=$PROYECTO
gcloud compute networks list --project=$PROYECTO --format="value(name)"
```

### 2. Activar Cloud CDN solo en el servicio del frontend
```powershell
$PROYECTO = "<proyecto-de-pruebas>"
if ($PROYECTO -eq "evydentia" -or $PROYECTO -like "<*") { throw "Parte A es solo para PRUEBAS." }
gcloud compute backend-services update evydentia-web-bs --global --project=$PROYECTO --enable-cdn --cache-mode=USE_ORIGIN_HEADERS
```
No lo actives en `evydentia-backend-bs`.

### 3. Crear Memorystore
```powershell
$PROYECTO = "<proyecto-de-pruebas>"
$REGION = "us-central1"
$RED = "<red-del-entorno>"
if ($PROYECTO -eq "evydentia" -or $PROYECTO -like "<*" -or $RED -like "<*") { throw "Parte A es solo para PRUEBAS: completa los valores." }
gcloud services enable redis.googleapis.com --project=$PROYECTO
gcloud redis instances create evydentia-cache --project=$PROYECTO --region=$REGION --tier=BASIC --size=1 --redis-version=redis_7_0 --network=$RED
```

### 4. Verificar
```powershell
$PROYECTO = "<proyecto-de-pruebas>"
if ($PROYECTO -eq "evydentia" -or $PROYECTO -like "<*") { throw "Parte A es solo para PRUEBAS." }
gcloud compute backend-services describe evydentia-web-bs --global --project=$PROYECTO --format="value(enableCDN,cdnPolicy.cacheMode)"
gcloud compute backend-services describe evydentia-backend-bs --global --project=$PROYECTO --format="value(enableCDN)"
gcloud redis instances describe evydentia-cache --region=us-central1 --project=$PROYECTO --format="value(state,host,port)"
```
Esperado: frontend `True`; backend vacío o `False`; Redis `READY`. Un activo de `/_next/static/` debe traer `public, max-age=31536000, immutable`; `/api/v1/*` nunca debe traer la cabecera `age`.

## Parte B · PRODUCCIÓN
**Aplica a PRODUCCIÓN. No ejecutar hasta la fase beta, igual que minScale 1.** Es la misma secuencia de la Parte A con `$PROYECTO = "evydentia"` y la guarda invertida: se detiene si el proyecto no es producción y exige confirmar a mano.

```powershell
$PROYECTO = "evydentia"
$REGION = "us-central1"
$RED = "<red-de-produccion>"
if ($PROYECTO -ne "evydentia" -or $RED -like "<*") { throw "Parte B es solo para PRODUCCION: completa la red." }
if ((Read-Host "Escribe evydentia para confirmar PRODUCCION") -ne "evydentia") { throw "Sin confirmacion explicita: no se ejecuta." }
gcloud compute backend-services update evydentia-web-bs --global --project=$PROYECTO --enable-cdn --cache-mode=USE_ORIGIN_HEADERS
gcloud services enable redis.googleapis.com --project=$PROYECTO
gcloud redis instances create evydentia-cache --project=$PROYECTO --region=$REGION --tier=BASIC --size=1 --redis-version=redis_7_0 --network=$RED
```
Verifica con los mismos comandos del paso 4 de la Parte A, pero con la guarda invertida.

## Pendiente
Cloud Run necesita alcanzar la red de Memorystore (conector VPC o Direct VPC egress) y `REDIS_URL` en Secret Manager: lo decide una ficha posterior junto con el cliente real. Hasta entonces la caché corre en memoria local.
