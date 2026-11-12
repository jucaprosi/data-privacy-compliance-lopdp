# Brief para el propietario · Balanceador HTTPS de app.evydentia.com (GCP-04)

Lo ejecuta Juan Carlos con Antigravity. Ninguna IA crea recursos en Google Cloud.
Especificación: `governance/operaciones/cloud_load_balancer.yaml` y `governance/operaciones/cloudrun_frontend_service.yaml` (en main).

## Estado actual (consulta de solo lectura, 2026-11-08)

| Recurso | Estado |
|---|---|
| IP `evydentia-ip` | reservada; el DNS `app` ya apunta a ella |
| Certificado `evydentia-cert` | PROVISIONING / FAILED_NOT_VISIBLE: es normal, se activa solo cuando exista la regla de reenvío del paso 5 |
| Cloud Run `evydentia-backend` | existe; ingress `all` y `allUsers` como invocador: hoy es público por su URL run.app |
| Cloud Run `evydentia-web` | **no existe** |
| Imagen del frontend | **no existe** (en Artifact Registry solo está `backend`) |
| Cuenta de servicio del frontend | **no existe** |
| Conector VPC | **no existe** (la API Serverless VPC Access está desactivada) |
| Cloud Armor, NEG, servicios de backend, mapa de URLs, proxies, reglas de reenvío | ninguno existe |

### Decisión antes de empezar: el conector VPC del frontend

`cloudrun_frontend_service.yaml` pide un conector VPC (`CONECTOR_VPC`), pero no existe y el frontend no lo necesita: llama al backend por `https://app.evydentia.com`, es decir, entra por el balanceador, que el ingress `internal-and-cloud-load-balancing` sí acepta. En el paso 1 se quitan esas dos líneas al desplegar. Si el Arquitecto prefiere el conector, hay que crearlo antes (API, red y rango /28), y eso es otro brief.

## Paso 0 · Variables (PowerShell; se pegan en cada ventana nueva)

```powershell
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"; git pull; gcloud config set project evydentia; $R="us-central1"; $IMG="us-central1-docker.pkg.dev/evydentia/evydentia-containers/web"
```

## Paso 1 · Frontend en Cloud Run

1.1 Cuenta de servicio del frontend (sin roles: el frontend no toca la base ni los secretos):

```powershell
gcloud iam service-accounts create sa-evydentia-web --display-name "EVYDENTIA frontend"
```

1.2 Construir y subir la imagen con Cloud Build (unos 5 a 8 minutos):

```powershell
@"
steps:
- name: gcr.io/cloud-builders/docker
  args: ['build','-f','Dockerfile.cloudrun','-t','$IMG`:inicial','.']
images: ['$IMG`:inicial']
"@ | Out-File -Encoding utf8 "$env:TEMP\cloudbuild-web.yaml"; gcloud builds submit frontend --config "$env:TEMP\cloudbuild-web.yaml"
```

1.3 Crear el servicio desde la especificación (solo el bloque de producción, con los marcadores sustituidos y sin el conector VPC):

```powershell
$y = (Get-Content governance\operaciones\cloudrun_frontend_service.yaml -Raw) -split "(?m)^---\s*$" | Select-Object -First 1; $y = $y -replace "image: IMAGEN","image: $IMG`:inicial" -replace "CUENTA_DE_SERVICIO","sa-evydentia-web@evydentia.iam.gserviceaccount.com" -replace "(?m)^\s*run\.googleapis\.com/vpc-access-.*\r?\n",""; $y | Out-File -Encoding utf8 "$env:TEMP\web-produccion.yaml"; gcloud run services replace "$env:TEMP\web-produccion.yaml" --region $R
```

Comprobación: `gcloud run services describe evydentia-web --region $R --format="value(status.conditions[0].status)"` debe dar `True`.

## Paso 2 · Cloud Armor `evydentia-waf`

```powershell
gcloud compute security-policies create evydentia-waf --description "EVYDENTIA WAF"
```

```powershell
gcloud compute security-policies rules create 1000 --security-policy evydentia-waf --expression "evaluatePreconfiguredWaf('sqli-v33-stable')" --action deny-403
```

```powershell
gcloud compute security-policies rules create 1001 --security-policy evydentia-waf --expression "evaluatePreconfiguredWaf('xss-v33-stable')" --action deny-403
```

```powershell
gcloud compute security-policies rules create 2000 --security-policy evydentia-waf --src-ip-ranges "*" --action rate-based-ban --rate-limit-threshold-count 600 --rate-limit-threshold-interval-sec 60 --ban-duration-sec 300 --conform-action allow --exceed-action deny-429 --enforce-on-key IP
```

La regla 2147483647 (`allow`) la crea Google por defecto.

## Paso 3 · NEG sin servidor y servicios de backend

```powershell
gcloud compute network-endpoint-groups create evydentia-backend-neg --region $R --network-endpoint-type serverless --cloud-run-service evydentia-backend; gcloud compute network-endpoint-groups create evydentia-web-neg --region $R --network-endpoint-type serverless --cloud-run-service evydentia-web
```

```powershell
gcloud compute backend-services create evydentia-backend-bs --global --load-balancing-scheme EXTERNAL_MANAGED --security-policy evydentia-waf; gcloud compute backend-services add-backend evydentia-backend-bs --global --network-endpoint-group evydentia-backend-neg --network-endpoint-group-region $R
```

```powershell
gcloud compute backend-services create evydentia-web-bs --global --load-balancing-scheme EXTERNAL_MANAGED --security-policy evydentia-waf; gcloud compute backend-services add-backend evydentia-web-bs --global --network-endpoint-group evydentia-web-neg --network-endpoint-group-region $R
```

## Paso 4 · Mapa de URLs: `/api/v1/*` al backend y todo lo demás al frontend

```powershell
gcloud compute url-maps create evydentia-url-map --default-service evydentia-web-bs; gcloud compute url-maps add-path-matcher evydentia-url-map --path-matcher-name rutas --default-service evydentia-web-bs --path-rules "/api/v1/*=evydentia-backend-bs" --new-hosts app.evydentia.com
```

## Paso 5 · HTTPS en 443 y redirección de 80 a HTTPS

```powershell
gcloud compute target-https-proxies create evydentia-https-proxy --url-map evydentia-url-map --ssl-certificates evydentia-cert; gcloud compute forwarding-rules create evydentia-https --global --load-balancing-scheme EXTERNAL_MANAGED --address evydentia-ip --target-https-proxy evydentia-https-proxy --ports 443
```

```powershell
@"
name: evydentia-redireccion
defaultUrlRedirect:
  httpsRedirect: true
  redirectResponseCode: MOVED_PERMANENTLY_DEFAULT
"@ | Out-File -Encoding utf8 "$env:TEMP\redireccion.yaml"; gcloud compute url-maps import evydentia-redireccion --global --source "$env:TEMP\redireccion.yaml" --quiet; gcloud compute target-http-proxies create evydentia-http-proxy --url-map evydentia-redireccion; gcloud compute forwarding-rules create evydentia-http --global --load-balancing-scheme EXTERNAL_MANAGED --address evydentia-ip --target-http-proxy evydentia-http-proxy --ports 80
```

## Paso 6 · Esperar el certificado (de 15 a 60 minutos)

```powershell
gcloud compute ssl-certificates describe evydentia-cert --global --format="value(managed.status,managed.domainStatus)"
```

Debe llegar a `ACTIVE  app.evydentia.com=ACTIVE`. Luego, `https://app.evydentia.com` abre el frontend y `https://app.evydentia.com/api/v1/entorno` devuelve el JSON del entorno.

## Paso 7 · Cerrar la puerta lateral del backend (solo después del paso 6)

Hasta aquí el backend sigue respondiendo por su URL run.app. Con el balanceador ya funcionando:

```powershell
gcloud run services update evydentia-backend --region $R --ingress internal-and-cloud-load-balancing
```

Comprobación: la URL run.app del backend responde 404, y `https://app.evydentia.com/api/v1/entorno` sigue respondiendo.
Queda pendiente aparte el ajuste ya conocido de `deploy-gcp.yml` (flags de ingress), para que un despliegue futuro no reabra el acceso.

## Paso 8 · Proxies de confianza del backend: `PROXIES_CONFIABLES` (cuando SEC-21 esté en main)

La ficha SEC-21 limita por IP la ruta pública `/api/v1/entorno`. Para saber cuál es la IP real del cliente, el backend necesita saber cuántos proxies de confianza tiene delante. La variable se llama `PROXIES_CONFIABLES` (un entero ≥ 0) y es **obligatoria en la nube**: si falta o no es válida, el arranque falla.

| Situación | Valor |
|---|---|
| Local, CI, arnés | 0 (la cabecera `X-Forwarded-For` se ignora) |
| Cloud Run **hoy**, sin balanceador | **1** (la infraestructura de Google añade la IP real como última entrada) |
| Cloud Run **detrás del balanceador** | **2**, pendiente de confirmar con evidencia (el balanceador añade una entrada propia) |

`deploy-gcp.yml` despliega con `--set-env-vars`, que reemplaza todas las variables del servicio. Por eso la variable va **dentro del workflow**, no puesta a mano:

1. **Hecho:** `deploy-gcp.yml` ya lleva `PROXIES_CONFIABLES=1` dentro de `--set-env-vars` (PR #619). Es el comportamiento de hoy, sin balanceador.
2. **Después del paso 6** (el balanceador responde) y del paso 7 (ingress `internal-and-cloud-load-balancing`, requisito de Seguridad): confirma con evidencia cuántas entradas trae `X-Forwarded-For` en una petición real, y entonces cambia el valor en el workflow (probablemente a `2`) y despliega. Para aplicarlo de inmediato mientras tanto:

```powershell
gcloud run services update evydentia-backend --region $R --update-env-vars PROXIES_CONFIABLES=2
```

Si pones solo el comando y no cambias el workflow, el siguiente despliegue lo vuelve a 1.

**Evidencia que debes darme:** tras el paso 6, mira en los registros de Cloud Run una petición real a través de `app.evydentia.com` y dime cuántas direcciones trae `X-Forwarded-For` y en qué orden. Con eso se confirma el valor, y ahí se cierra la parte del balanceador de SEC-21.

**Por qué el ingress es requisito:** si el backend sigue público por su dirección `run.app`, cualquiera puede llamarlo directo y escribir la cabecera a su gusto, y el límite por IP deja de servir.

## Si algo falla

No borres nada. Copia el mensaje de error al chat del CTO; el diagnóstico lo hago en modo lectura.
