# Brief del propietario · Por qué no publica `deploy-gcp.yml` y cómo publicar main

Fecha: 2026-11-13. Redactado por el CTO de EVYDENTIA. Lo ejecuta el propietario (con Antigravity o desde PowerShell). Ninguna sesión de IA escribe en Google Cloud ni en la base.

## Diagnóstico (hecho solo con lecturas)

- **El workflow no está roto: solo se lanza a mano.** Desde el commit 71636e93 (2026-11-06 22:38), `deploy-gcp.yml` tiene un único disparador, `workflow_dispatch`. Un push a main ya no lo lanza. Su única corrida es la 42301866832 (push de 9a9977c8, 2026-11-06 22:04, verde), anterior a ese cambio. Nadie lo ha lanzado a mano desde entonces.
- **Cloud Run sirve el código del 2026-11-06.** Las cuatro revisiones de `evydentia-backend` (00001 a 00004, la última del 2026-11-11) usan la misma imagen, `backend@sha256:1b16e7d2…`. Las revisiones 00002 a 00004 son cambios de configuración hechos con `gcloud`, no publicaciones de código nuevo.
- **Al servicio le faltan dos variables que el workflow ya trae.** El servicio tiene `ENVIRONMENT`, `PROJECT_ID`, `GCP_STORAGE_BUCKET`, `CORS_ORIGINS` y tres secretos (`DATABASE_URL`, `JWT_SECRET_KEY`, `INVENTARIO_CLAVE_CIFRADO`). Le faltan `APP_ENV=production` y `PROXIES_CONFIABLES=1`, que el workflow añade desde 8b2422e0 y 76bcfd60. La primera publicación las pone: eso cubre lo que pide SEC-21 (#683).
- **El workflow no migra la base.** Construye la imagen y publica la revisión, pero no ejecuta `alembic upgrade head`. Si Cloud SQL no está en la cabeza de main, el código nuevo arrancará contra un esquema viejo.

Consecuencia: ORG-22 (#675) espera dos despliegues posteriores a 6498524d. Mientras no se lance el workflow a mano, esa condición no llega nunca, y EVI-03 (#690) espera detrás.

## Qué no hace este brief

- No cambia `deploy-gcp.yml` (es del propietario). Si se quiere volver a publicar en cada push, es una decisión aparte.
- No cambia `--min-instances`: sigue en 0. El paso a 1 es GCP-05 (#689) y espera tu visto bueno.
- No escribe URL de conexión, contraseñas ni secretos en ningún archivo ni en el chat.

## Pasos (PowerShell, copiar y pegar completos)

### 1. Ver el estado (solo lectura)

```powershell
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"
$PROYECTO = "evydentia"; $REGION = "us-central1"; $SERVICIO = "evydentia-backend"
gh run list --workflow deploy-gcp.yml --limit 5
gcloud run revisions list --service $SERVICIO --region $REGION --project $PROYECTO --limit 5 --format="table(metadata.name,metadata.creationTimestamp,spec.containers[0].image.basename())"
```

Resultado esperado hoy: una sola corrida (2026-11-06) y cuatro revisiones con la misma imagen.

### 2. Comprobar que Cloud SQL está en la cabeza de main (obligatorio antes de publicar)

Desde una copia de main al día y con `CLOUDSQL_DATABASE_URL` del rol dueño cargada en la sesión, nunca escrita en un archivo:

```powershell
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"
git fetch origin main
python scripts/verificar_cloudsql_conexion.py --rol lopdp_app
```

- **Código 0:** la base está al día. Pasa al paso 3.
- **Falla la comprobación 5** (`alembic current` distinto de `alembic heads`): migra antes de publicar.
  1. Primero, un respaldo a demanda:
     ```powershell
     gcloud sql backups create --instance evydentia-production --project evydentia
     ```
  2. Después, sigue el paso 2 de `governance/operaciones/MIGRACION_CLOUDSQL_POSTGRES.md` (`python -m alembic upgrade head` desde main, con `MIGRATION_DATABASE_URL`).
  3. Anótalo en `REGISTRO_MIGRACIONES_MANUALES.md`.
  4. Repite la verificación hasta obtener código 0.

### 3. Primera publicación

```powershell
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"
gh workflow run deploy-gcp.yml --ref main
Start-Sleep -Seconds 5
$RUN = gh run list --workflow deploy-gcp.yml --limit 1 --json databaseId --jq ".[0].databaseId"
gh run watch $RUN --exit-status
```

Si el entorno `gcp-produccion` pide aprobación, apruébala en la página de la corrida.

### 4. Verificar la revisión nueva (solo lectura)

```powershell
$PROYECTO = "evydentia"; $REGION = "us-central1"; $SERVICIO = "evydentia-backend"
gcloud run revisions list --service $SERVICIO --region $REGION --project $PROYECTO --limit 2 --format="table(metadata.name,metadata.creationTimestamp,spec.containers[0].image.basename())"
gcloud run services describe $SERVICIO --region $REGION --project $PROYECTO --format="json(spec.template.spec.containers[0].env)" | ConvertFrom-Json | ForEach-Object { $_.spec.template.spec.containers[0].env.name }
$URL = gcloud run services describe $SERVICIO --region $REGION --project $PROYECTO --format="value(status.url)"
(Invoke-WebRequest "$URL/api/v1/health" -UseBasicParsing).StatusCode
```

Debe salir lo siguiente:
- Una revisión 00005 con una imagen distinta de `1b16e7d2…`.
- `APP_ENV` y `PROXIES_CONFIABLES` en la lista de variables.
- Código 200 en el health.

Si algo falla, vuelve a la revisión estable que mostró el paso 1, la más reciente antes de esta publicación (hoy `evydentia-backend-00004-dr6`). Pon su nombre en `$ESTABLE`:

```powershell
$ESTABLE = "evydentia-backend-00004-dr6"
gcloud run services update-traffic evydentia-backend --region us-central1 --project evydentia --to-revisions "$ESTABLE=100"
```

### 5. Segunda publicación

Cuando la primera esté verificada, repite los pasos 3 y 4. Debe salir una revisión 00006.

### 6. Confirmar en el chat

Pega en el chat del CTO:

> Despliegues 00005 y 00006 publicados desde main, health 200, base en la cabeza.

Con esa frase, el CTO hará lo siguiente:
1. Quitar el borrador del #675, simularlo y fusionarlo.
2. Después, ocuparse del #690.
3. Dar por cubierta la variable que pedía SEC-21 (#683).

## Rol auditor (ORG-22): condición para desplegarlo

**Decisión del propietario, 2026-11-13:** ORG-22 (#675) se fusiona en main sin esperar a los despliegues. La condición pasa de la fusión al despliegue, que es donde está el riesgo.

**Riesgo.** Una revisión del backend anterior a ORG-22a (#658, commit 6498524d) falla al leer un rol que no conoce. Si existe un usuario con rol `auditor` y una de esas revisiones recibe tráfico, esa revisión rompe al listar roles.

**Regla.**
1. El primer despliegue de este brief (main sin ORG-22, por ejemplo f6baba10) ya incluye ORG-22a. Se publica y se verifica primero (pasos 3 y 4).
2. El despliegue que incluya ORG-22 solo se lanza cuando el anterior está sirviendo el 100 % del tráfico con health 200. Antes se migra la base con el Job `evydentia-migrate`, que trae `org22b_auditor_sod_trigger`.
3. Desde ese momento **no se revierte nunca** a `evydentia-backend-00004-dr6` ni a revisiones anteriores: no conocen el rol `auditor`. La vuelta atrás solo puede ir a la revisión del punto 1 o a una posterior.
4. No se asigna el rol `auditor` a ningún usuario de producción hasta que el punto 2 esté verificado.

**Comprobación (solo lectura).** Antes del punto 2, la revisión que sirve debe ser posterior a 6498524d:
```powershell
gcloud run services describe evydentia-backend --region us-central1 --project evydentia --format="value(status.traffic)"
```

## Al entrar en la fase beta de pruebas: una instancia siempre encendida (GCP-05)

**Decisión del propietario, 2026-11-13:** `minScale 1` no se activa ahora. Se activa al empezar la fase beta de pruebas.

**Qué es la fase beta.** Empieza cuando las fichas del producto estén completas y se pase a probar la aplicación para mostrarla a los clientes. Desde ese momento la primera pantalla tiene que cargar sin espera. Lo que decide el inicio es el propietario, no el número de fichas cerradas.

**Por qué.** Con `--min-instances 0`, Cloud Run apaga el backend cuando no hay tráfico. El primer usuario que entra después espera varios segundos a que arranque (arranque en frío). Con `--min-instances 1` siempre queda una instancia encendida y nadie espera.

**Coste.** Hasta unos USD 9,86 al mes fijos (1 vCPU y 512 MiB inactivos las 730 h del mes, us-central1), menos lo que cubra el nivel gratuito. El cálculo está en el #689 (fuente: https://cloud.google.com/run/pricing, leída el 2026-11-12). Con más tráfico se siguen encendiendo instancias hasta el máximo.

**Ojo.** El workflow pasa `--min-instances 0` en cada publicación. Un cambio hecho solo con `gcloud run services update` se pierde en el siguiente despliegue. El cambio tiene que ir en el workflow.

### Pasos

1. **El CTO fusiona el #689 (GCP-05).** Trae los límites, el presupuesto de conexiones de Cloud SQL y la prueba de carga.
2. **El propietario cambia una línea de `.github/workflows/deploy-gcp.yml`:** `--min-instances 0` pasa a `--min-instances 1`. Si GCP-05 fija otro máximo, `--max-instances` pasa al valor que diga.
3. **Se publica** con los pasos 3 y 4 de este brief.
4. **Se comprueba** (solo lectura):
   ```powershell
   gcloud run services describe evydentia-backend --region us-central1 --project evydentia --format="value(spec.template.metadata.annotations['autoscaling.knative.dev/minScale'])"
   ```
   Debe imprimir `1`.
5. **Se confirma en el chat del CTO:** «minScale 1 activo desde la revisión <nombre>».

**Vuelta atrás.** Se devuelve la línea a `--min-instances 0` y se publica. No toca datos.
