# Entorno de pruebas de EVYDENTIA en Google Cloud
`¤entorno-pruebas` `¤cloud-run-perf`

> Procedimiento operativo del entorno de pruebas. El contrato (qué es, qué lo aísla de producción y qué interfaz comparten las tareas) está en `governance/artefactos/PRD.md`, §5.5, y sus invariantes en `INVARIANTS.md`, apartado 7. Este documento no lleva identificadores de proyecto, URL de conexión, contraseñas, claves ni correos reales: los valores viven en Secret Manager del proyecto de pruebas y en los archivos locales de `herramientas`.

Cada apartado es la sección reservada de una tarea (`governance/tareas/EP-0x.md`), y cada tarea escribe solo dentro de la suya. Los manifiestos están en `governance/operaciones/entornos/pruebas/`.

<!-- === EP-04 === -->
## 1. Proyecto, servicios de Cloud Run, acceso y presupuesto (EP-04)

Los manifiestos están en `governance/operaciones/entornos/pruebas/`. Los aplica el propietario con Antigravity; ninguna sesión de IA crea proyectos, servicios ni presupuestos. `tests/test_ep04_computo_pruebas.py` los compara con los de producción y no toca Google Cloud.

| Archivo | Qué declara |
| :--- | :--- |
| `proyecto.yaml` | El proyecto propio (`PROYECTO_PRUEBAS`, marcador), la región de producción, las API y una cuenta de servicio por servicio, sin permisos en producción. |
| `cloudrun_backend.yaml` | `evydentia-backend`: ingress `all`, `APP_ENV=pruebas`, `AUTH_MODE=oidc`, `HUELLA_PROYECTO_PRODUCCION`, `ENTORNO_CORREOS_PERMITIDOS` vacío, `GOOGLE_CLIENT_ID` y la base por referencia a Secret Manager. Su política IAM deja invocar solo a la cuenta del frontend. |
| `cloudrun_frontend.yaml` | `evydentia-web`: IAP, `PROXY_AUTH_CLOUD_RUN=token_servicio` y `BACKEND_URL` de `run.app`. |
| `cloudrun_vault_worker.yaml` | `evydentia-vault-worker`, sin IAP, invocable solo por la cuenta del disparador de Eventarc; producción aún no tiene manifiesto (GOVW-01), así que es una excepción cerrada de la prueba de paridad. |
| `acceso_iap.yaml` | Opción A del §5.5 (propietario, 2026-11-08): IAP en el frontend, sin balanceador; quién accede y quién invoca cada servicio. |
| `presupuesto.yaml` | Tres presupuestos al mes (total 30 USD, Vertex AI 15 USD y Cloud Storage 5 USD; decisión del CTO, que se revisa a los 30 días con el gasto real) con avisos al 50, 90 y 100 %. Solo avisan: el tope real es el máximo de instancias y la cuota de IA (SEC-13). |

Los tres servicios llevan la imagen por digest (marcador `IMAGEN_POR_DIGEST`, que sustituye `desplegar_entorno_pruebas.ps1`), mínimo 0 instancias y máximo 2. `HUELLA_DEL_PROYECTO_DE_PRODUCCION` es otro marcador: el propietario pone el identificador de producción al aplicar, nunca en el repositorio.

### Brief para el propietario (EP-04)
Orden sugerido, todo en el proyecto de pruebas. Lo de la nube lo ejecuta quien tenga el acceso; las comprobaciones son de solo lectura.

> **Antes de aplicar nada.** La anotación `run.googleapis.com/iap-enabled` de `cloudrun_frontend.yaml` **no está documentada** por Google: su página sobre IAP en Cloud Run solo describe el indicador `--iap`. La fuente de verdad es el comando del paso 5. Tras activar IAP con `--iap`, mira con `gcloud run services describe` (solo lectura, abajo) si aparece esa anotación: si aparece, se queda; si no aparece, o si `gcloud run services replace` la rechaza, se quita de `cloudrun_frontend.yaml` y rige solo el comando. Mientras `describe` no muestre `Iap Enabled: true`, el frontend no está protegido por IAP: no lo uses ni des acceso a quienes prueban. **Es una compuerta humana: EP-04 no pasa a `hecha` sin la salida de ese comando.**

```powershell
$PROYECTO = "<id-del-proyecto-de-pruebas>"
gcloud run services describe evydentia-web --project=$PROYECTO --region=us-central1 --format="yaml(metadata.annotations)"
```

1. Crear el proyecto, vincular su facturación y habilitar las API de `proyecto.yaml`.
2. Crear las cuentas de servicio de `proyecto.yaml` con sus roles. Ninguna recibe permisos en producción.
3. Crear los secretos de EP-05 (`secretos.yaml`) y el conector de acceso a VPC; sustituir `CONECTOR_VPC_PRUEBAS`.
4. Aplicar los tres servicios con `gcloud run services replace`, tras sustituir `NUMERO_PROYECTO_PRUEBAS`, `HUELLA_DEL_PROYECTO_DE_PRODUCCION` (el identificador de producción, solo en la copia local) y la imagen por digest (lo hace `scripts/desplegar_entorno_pruebas.ps1`). El segundo documento de `cloudrun_backend.yaml` y de `cloudrun_frontend.yaml` es la política IAM: se aplica con `gcloud run services set-iam-policy`.
5. Activar IAP en `evydentia-web` con `gcloud run services update evydentia-web --iap` y conceder `roles/iap.httpsResourceAccessor` a quienes prueban.
6. Crear los tres presupuestos de `presupuesto.yaml`.
7. Comprobar, solo lectura: `gcloud run services describe evydentia-web` debe mostrar `Iap Enabled: true`, y `gcloud run services get-iam-policy evydentia-backend` solo la cuenta del frontend.
8. Correr el verificador del entorno (EP-07).

**Decisiones y dudas abiertas**
- **Anotación de IAP:** ver el aviso del inicio del brief; es una compuerta humana.
- **Worker:** no llama al backend (GOVW-01 recibe eventos de Eventarc y escribe en la base). Su único invocador es `sa-eventarc-pruebas`; si la entrega fuera por Pub/Sub, sería el agente de servicio de Pub/Sub. Producción no tiene manifiesto del worker: mientras no exista, la prueba lo compara con el backend en lo común, y si aparece falla hasta compararlo.
- **Cliente OAuth:** el backend verifica el token con `GOOGLE_CLIENT_ID`, un identificador público que va como valor (`CLIENT_ID_OAUTH_DE_PRUEBAS`, el del proyecto de pruebas). No hay `GOOGLE_CLIENT_SECRET` (`CONFIGURACION_LOGIN_GOOGLE.md`) y el cliente de IAP lo gestiona Google.
- **Imagen entre proyectos:** el Artifact Registry es el de pruebas y la imagen se copia por digest; ninguna cuenta de pruebas lee el registro de producción.
<!-- === fin EP-04 === -->

<!-- === EP-05 === -->
## 2. Cloud SQL, buckets y secretos (EP-05)

Los manifiestos están en `governance/operaciones/entornos/pruebas/`. Los aplica una persona con Antigravity; ninguna sesión de IA crea instancias, buckets ni secretos. `tests/test_ep05_datos_pruebas.py` los compara con los de producción.

**Cloud SQL (`cloud_sql.yaml`).**
- Es una instancia propia, `evydentia-pruebas`, y más pequeña: `db-g1-small` y zonal.
- Respecto de `cloud_sql_instance.yaml` (GCP-04), solo cambian el tamaño y el proyecto.
- Conserva lo demás: PostgreSQL 16, `pgvector`, el rol `lopdp_app` sin `BYPASSRLS`, `FORCE ROW LEVEL SECURITY` y las mismas copias automáticas.
- **Horario:** Siempre encendida (decisión 3 del propietario, 2026-11-08). `activationPolicy: ALWAYS`.

**Buckets (`buckets.yaml`).**
- Son los dos tiers de la bóveda: `short-ttl` (borrado al día 15, sin Autoclass) y `long-retention` (Autoclass y retención por objeto).
- Tienen la misma retención y el mismo ciclo de vida que producción, según BOV-02, y su notificación a Eventarc hacia `vault_worker`.
- La retención lleva `locked: false` explícito. **Nunca se bloquea:** bloquearla es irreversible y deja un *lien* que impide borrar el proyecto. Por eso no se usa `gcloud storage buckets update --lock-retention-period` en pruebas.

**Secretos (`secretos.yaml`).**
- Solo lleva el nombre de cada secreto y quién lo lee; los valores se cargan a mano en Secret Manager del proyecto de pruebas.
- Todos llevan el prefijo `evydentia-pruebas-`, y ninguno se comparte con producción.
- No hay secretos de correo: por decisión del propietario del 2026-11-07, el envío queda apagado y sin proveedor.

**Marcador de entorno (SEC-20, #534).** Cuando existan las instancias `evydentia-pruebas` y la de demo, el propietario crea `public.entorno_marcador` en cada una de sus bases, como pide SEC-20. Hoy no hay bases de pruebas ni de demo en Cloud SQL: la única instancia es la de producción, y en ella no se crea (CTO, 2026-11-09).
<!-- === fin EP-05 === -->

<!-- === EP-06 === -->
## 3. Ciclo de una versión y reinicio (EP-06)

Los ejecuta una persona (Juan Carlos, Aleczandra o José); ninguna sesión de IA despliega en Google Cloud. Antes de cada corrida se fija `HUELLA_PROYECTO_PRODUCCION`, y los dos scripts se niegan a correr sin ella. Conviene correrlos primero con `-SoloMostrar`, que imprime los pasos sin ejecutar ninguno. La URL de la base de pruebas se lee de `herramientas\url-base-pruebas.txt` y nunca se imprime.

**Cuándo correr cada uno.**

- `desplegar_entorno_pruebas.ps1`: con cada versión candidata, cuando el CI ya publicó la imagen y se conoce su digest.
- `digest_verificado.py guardar`: justo después del verificador (EP-07), con su código de salida.
- `reiniciar_entorno_pruebas.ps1`: cuando los datos de pruebas quedaron inservibles o antes de una ronda nueva de pruebas. Borra la base y los buckets del proyecto recibido y vuelve a sembrar (EP-03).

**Despliegue de una versión (PowerShell, desde la raíz del worktree).**

```powershell
cd "C:\Users\<usuario>\Desktop\Plataforma LOPDP 360\.claude\worktrees\<worktree>"
$env:HUELLA_PROYECTO_PRODUCCION = "<huella-del-proyecto-de-produccion>"
.\scripts\desplegar_entorno_pruebas.ps1 -Proyecto "<proyecto-de-pruebas>" -Digest "sha256:<64 hexadecimales>" -Imagen "<region>-docker.pkg.dev/<proyecto>/<repositorio>/<imagen>" -Servicios "<api>,<web>,<worker>" -InstanciaCloudSql "<proyecto>:<region>:<instancia>" -SoloMostrar
```

Sin `-SoloMostrar` el script ejecuta los pasos en este orden:

1. Comprueba que `origin/main` tiene una cabeza de Alembic por sala.
2. Aplica la guardia de la huella.
3. Migra por `cloud-sql-proxy`.
4. Despliega el mismo digest en los tres servicios con `gcloud run deploy --image ...@sha256:...`.
5. Muestra el comando del verificador.

Luego se registra el resultado del verificador:

```powershell
python scripts/verificar_entorno_pruebas.py --proyecto "<proyecto-de-pruebas>"
python scripts/digest_verificado.py guardar --digest "sha256:<64 hexadecimales>" --codigo $LASTEXITCODE
```

El registro vive en `%USERPROFILE%\.evydentia\digest_verificado.json`, fuera del repositorio. Quien promueve a producción (GCP-07) toma el digest con `python scripts/digest_verificado.py leer`, que solo entrega uno cuyo último resultado fue 0. Para un digest concreto se usa `comprobar --digest ...`.

**Reinicio del entorno.**

```powershell
.\scripts\reiniciar_entorno_pruebas.ps1 -Proyecto "<proyecto-de-pruebas>" -InstanciaCloudSql "<proyecto>:<region>:<instancia>" -BaseDeDatos "<base>" -Buckets "<bucket-evidencias>,<bucket-video>" -SoloMostrar
```

Sin `-SoloMostrar` el script ejecuta los pasos en este orden:

1. Aplica la guardia de la huella al proyecto, a la instancia y a los buckets.
2. Pide que se teclee el id del proyecto como confirmación.
3. Comprueba que cada bucket es del proyecto: el `project_number` de `gcloud storage buckets describe` debe ser igual al `projectNumber` de `gcloud projects describe`. Si alguno no coincide, se detiene sin borrar la base ni ningún bucket.
4. Recrea la base.
5. Migra.
6. Vacía los buckets.
7. Llama a `scripts/sembrar_entorno_pruebas.py`.

Todo comando de `gcloud` lleva `--project` con el proyecto recibido, pero eso no limita una URL `gs://`. Por eso existe el paso 3.

**Si falla un paso.** El script se detiene con `DETENIDO: <motivo>` y no sigue. Esa noche no se promueve nada a producción, ni siquiera un digest verificado antes. Para corregirlo:

- Si falló la cabeza de Alembic, se fusionan las cabezas (`FUSION_ALEMBIC.md`).
- Si falló la migración o el despliegue, se corrige en `main` y se repite el ciclo con un digest nuevo.
- Si el verificador falla, se registra su código con `guardar`, y ese digest queda rechazado para la promoción.
<!-- === fin EP-06 === -->

<!-- === EP-03 === -->
## 4. Datos ficticios y cuentas de quienes prueban (EP-03)

`scripts/sembrar_entorno_pruebas.py` crea o completa, sin duplicar, tres organizaciones ficticias (una micro, una mediana y una de gran escala), sus personas ficticias (`@example.test`), áreas y roles, y sube a los buckets evidencias inventadas (PDF y texto) y clips de video sintéticos (patrón de barras, sin personas ni audio). Los datos están en `scripts/datos_sinteticos/`. Los roles y las áreas pasan por `organizacion_service`.

**Archivo de quienes prueban.** Por defecto `herramientas\testers-entorno-pruebas.txt`. Nunca se sube al repositorio: la siembra se niega a leerlo si git lo rastrea. Una cuenta por línea, `correo,rol,organización`; las líneas vacías y las que empiezan por `#` se ignoran.

- Roles: `admin_organizacion`, `coordinador`, `implementador`, `responsable_area` (queda en la unidad ficticia de pruebas) o `dpo`.
- Organizaciones: `ep-org-micro`, `ep-org-mediana`, `ep-org-gran-escala`.

```text
# correo,rol,organización
persona@dominio-de-quien-prueba,coordinador,ep-org-mediana
```

Quien prueba entra con su cuenta de Google (modo `oidc`) y encuentra ese rol en esa organización.

**Comando (PowerShell, desde la raíz del worktree).** Solo con la URL de la base de pruebas, leída de un archivo local de `herramientas`:

```powershell
cd "C:\Users\<usuario>\Desktop\Plataforma LOPDP 360\.claude\worktrees\<worktree>"
$env:HUELLA_PROYECTO_PRODUCCION = "<huella-del-proyecto-de-produccion>"
$env:MIGRATION_DATABASE_URL = Get-Content "herramientas\url-base-pruebas.txt" -Raw
python scripts/sembrar_entorno_pruebas.py --testers "herramientas\testers-entorno-pruebas.txt" --bucket "<bucket-de-pruebas>"
Remove-Item Env:MIGRATION_DATABASE_URL
```

Sin `--bucket` los objetos van a la carpeta local `herramientas\siembra-local`. La siembra se detiene si falta `HUELLA_PROYECTO_PRODUCCION`, si esa huella aparece en la URL o en el bucket, o si la URL es la de la base de producción. La salida solo cuenta, por clase, lo creado y lo que ya existía; no imprime la URL ni los correos. Correrla dos veces deja la base y los buckets igual.
<!-- === fin EP-03 === -->

<!-- === EP-07 === -->
## 5. Verificación (EP-07)

`scripts/verificar_entorno_pruebas.py` comprueba el entorno contra la interfaz del §5.5 y devuelve 0 solo si pasan las seis comprobaciones. Lo corre una persona, o el flujo `entorno-pruebas.yml` cuando el propietario lo aplica (`governance/apoyo/BRIEF_PROPIETARIO_EP07_WORKFLOW.md`). No es un check obligatorio del PR.

Atraviesa IAP y la invocación del backend con tokens de identidad de una cuenta de servicio autorizada. Usa las credenciales por defecto de Google o `gcloud auth print-identity-token`, suplantando `VERIFICADOR_CUENTA_SERVICIO` si está definida. Nunca imprime los tokens ni las URL.

```powershell
cd "C:\Users\<usuario>\Desktop\Plataforma LOPDP 360\.claude\worktrees\<worktree>"
$env:HUELLA_PROYECTO_PRODUCCION = "<huella-del-proyecto-de-produccion>"
$env:IAP_AUDIENCIA = "<id-del-cliente-oauth-de-iap>"
python scripts/verificar_entorno_pruebas.py "<url-del-frontend>" "<url-del-backend>" --proyecto "<proyecto-de-pruebas>"
python scripts/digest_verificado.py guardar --digest "<digest de la línea DIGEST>" --codigo $LASTEXITCODE
```

**Cómo leer cada fallo.** Cada línea dice `OK` o `FALLA` y el nombre de la comprobación.

| Comprobación | Si falla |
|---|---|
| `credenciales` | No se pudo obtener el token de identidad: revisar `gcloud auth login` o la cuenta de servicio y su permiso `roles/iam.serviceAccountTokenCreator`. No se comprueba nada más. |
| `salud` | `/api/v1/health` no está `OPERATIONAL` o tiene routers fallidos: mirar los registros de Cloud Run del backend. |
| `entorno` | `/api/v1/entorno` no devuelve `pruebas` con `datos_ficticios = true`, o falta `X-Entorno: pruebas`: el servicio no tiene `APP_ENV=pruebas` o se desplegó otra imagen. |
| `sin_headers` | Una ruta con datos de organización no respondió 401 sin token de la aplicación. Si da 200, el modo `headers` está activo: **es un fallo de seguridad**; se corrige `AUTH_MODE` y no se promueve nada. |
| `iap` | El frontend responde sin la identidad de IAP: IAP no está activado en el servicio o se le dio acceso a `allUsers`. |
| `robots` | `robots.txt` no tiene `Disallow: /`: el frontend no tiene `NEXT_PUBLIC_APP_ENV=pruebas` (EP-02). |
| `digest` | No hay una sola revisión con el 100 % del tráfico o no informa un digest: terminar el despliegue (EP-06) y repetir. |

Con cualquier `FALLA`, el código es 1 y ese digest queda rechazado para la promoción a producción (`digest_verificado.py guardar` con ese código). Con código 2, el uso es inválido: falta `--proyecto`, o el proyecto coincide con la huella de producción.
<!-- === fin EP-07 === -->

<!-- === EP-09 === -->
## 6. Puesta en marcha (EP-09)

**Estado: bloqueada a la espera del propietario (diagnóstico de solo lectura del 2026-11-15, abajo).** Esta sección fija el orden y las comprobaciones; no copia los comandos, que viven en los apartados 1 a 5. EP-09 no pasa a `hecha` hasta que `python scripts/verificar_entorno_pruebas.py` dé 0 contra el entorno desplegado y el flujo `entorno-pruebas.yml` termine en verde en GitHub: eso solo existe cuando una persona (Juan Carlos, Aleczandra o José) lo ejecuta. Ninguna sesión de IA crea, despliega ni carga secretos; de su lado, solo `gcloud` de lectura. Todo va contra el proyecto de pruebas, nunca contra producción.

### Orden y precondiciones
| # | Paso | Dónde está el procedimiento | Comprobar antes de seguir |
| :--- | :--- | :--- | :--- |
| 0 | Variables y huella | esta sección, abajo | `$PROYECTO` es el de pruebas y distinto de `HUELLA_PROYECTO_PRODUCCION`. |
| 1 | Proyecto, servicios, IAP y presupuesto (EP-04) | §1, pasos 1 a 7 | `describe` de `evydentia-web` muestra `Iap Enabled: true` (compuerta humana de §1). |
| 2 | Cloud SQL, buckets y secretos (EP-05) | §2 | Instancia `evydentia-pruebas` encendida; buckets con retención `locked: false`; secretos con prefijo `evydentia-pruebas-` cargados. |
| 3 | Primer despliegue por digest (EP-06) | §3 | El CI ya publicó la imagen; una cabeza de Alembic por sala; los tres servicios con el mismo digest y el 100 % del tráfico. |
| 4 | Siembra y cuentas de quienes prueban (EP-03) | §4 | `herramientas\testers-entorno-pruebas.txt` existe y git no lo rastrea; la siembra no se detiene por la huella. |
| 5 | Verificador (EP-07) | §5 | Todas las líneas `OK` y código 0. |
| 6 | Flujo de GitHub | `governance/apoyo/BRIEF_PROPIETARIO_EP07_WORKFLOW.md` | `entorno-pruebas.yml` en verde. |

Los pasos 1 a 4 van en ese orden: el despliegue necesita la base y los secretos, y la siembra necesita la base migrada.

### Variables comunes (PowerShell)
```powershell
cd "C:\Users\<usuario>\Desktop\Plataforma LOPDP 360\.claude\worktrees\<worktree>"
$PROYECTO = "<proyecto-de-pruebas>"
$REGION = "us-central1"
$env:HUELLA_PROYECTO_PRODUCCION = "<huella-del-proyecto-de-produccion>"
if ($PROYECTO -eq $env:HUELLA_PROYECTO_PRODUCCION) { throw "DETENIDO: el proyecto es el de produccion" }
```

### Comprobaciones de solo lectura entre pasos
```powershell
gcloud run services list --project=$PROYECTO --region=$REGION --format="table(metadata.name)"
gcloud run services describe evydentia-web --project=$PROYECTO --region=$REGION --format="yaml(metadata.annotations)"
gcloud run services get-iam-policy evydentia-backend --project=$PROYECTO --region=$REGION
gcloud sql instances list --project=$PROYECTO --format="table(name,state,settings.activationPolicy)"
gcloud storage buckets list --project=$PROYECTO --format="table(name,retention_policy.isLocked)"
gcloud secrets list --project=$PROYECTO --format="value(name)"
```
Esperado: los servicios `evydentia-backend`, `evydentia-web` y `evydentia-vault-worker`; `Iap Enabled: true` en el frontend; en la política del backend solo la cuenta del frontend; la instancia `evydentia-pruebas` en `RUNNABLE` con `ALWAYS`; ningún bucket con la retención bloqueada (vacío o `False`); todos los secretos con prefijo `evydentia-pruebas-`.

### Verificador, salida esperada
Se corre como en §5. La salida lleva una línea por comprobación, `OK` o `FALLA` seguido del nombre: `credenciales`, `salud`, `entorno`, `sin_headers`, `iap`, `robots` y `digest`, y al final `DIGEST sha256:...`. El código de salida (`$LASTEXITCODE`) debe ser 0. Con cualquier `FALLA`, el código es 1 y se sigue la tabla de §5. Después se registra el digest con `digest_verificado.py guardar` (§5).

### Si un paso falla
- No se sigue al paso siguiente ni se promueve nada a producción.
- Cada fallo se corrige en su apartado (§1 a §5); si el error está en un comando de otra tarea, se avisa al Tech Lead en vez de corregirlo aquí.
- Un digest rechazado se repite con un digest nuevo (§3).

### Diagnóstico de solo lectura (2026-11-15)
Lo hizo una sesión de IA, solo con lecturas (`gcloud projects list`, `gcloud run services list`, `gcloud sql instances list` y `gh run list`):

- La cuenta de `gcloud` ve dos proyectos: el de producción y el de demo. **No existe el proyecto de pruebas.** Tampoco existe la instancia `evydentia-pruebas` ni los servicios de pruebas.
- `.github/workflows/entorno-pruebas.yml` **no existe en `main`**: `gh run list --workflow entorno-pruebas.yml` responde 404. El brief `BRIEF_PROPIETARIO_EP07_WORKFLOW.md` está sin aplicar.
- Por eso no hay URL del frontend de pruebas y el verificador no se ha corrido. No se inventa ningún resultado: el registro de abajo sigue vacío.

### Brief al propietario (EP-09)
Lo ejecuta Juan Carlos, Aleczandra o José, en PowerShell, desde un worktree al día con `origin/main`, nunca desde la carpeta principal ni con su `.env`. Los valores entre `<...>` se escriben una vez en el bloque de variables, y ninguno se sube al repositorio. Cada bloque se detiene si el proyecto resulta ser el de producción.

**0. Worktree y variables (se pega una vez en cada consola nueva).**
```powershell
cd "$env:USERPROFILE\worktrees-evydentia"
git -C "$env:USERPROFILE\Desktop\Plataforma LOPDP 360" fetch origin
git -C "$env:USERPROFILE\Desktop\Plataforma LOPDP 360" worktree add "$env:USERPROFILE\worktrees-evydentia\ep-09-propietario" origin/main
cd "$env:USERPROFILE\worktrees-evydentia\ep-09-propietario"
$PROYECTO = "<id-nuevo-del-proyecto-de-pruebas>"
$REGION = "us-central1"
$FACTURACION = "<id-de-la-cuenta-de-facturacion>"
$env:HUELLA_PROYECTO_PRODUCCION = "<huella-del-proyecto-de-produccion>"
$PY = "$env:USERPROFILE\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe"
if (-not $env:HUELLA_PROYECTO_PRODUCCION) { throw "DETENIDO: falta la huella de produccion" }
if ($PROYECTO.ToLower().Contains($env:HUELLA_PROYECTO_PRODUCCION.ToLower())) { throw "DETENIDO: el proyecto es el de produccion" }
```
Si el worktree ya existe, se omiten las dos líneas de `git` y se hace `git pull` dentro de él.

**1. Proyecto, API y cuentas de servicio (EP-04, §1 pasos 1 y 2; `proyecto.yaml`).**
```powershell
gcloud projects create $PROYECTO
gcloud billing projects link $PROYECTO --billing-account=$FACTURACION
gcloud services enable run.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com sqladmin.googleapis.com vpcaccess.googleapis.com iap.googleapis.com aiplatform.googleapis.com dlp.googleapis.com storage.googleapis.com eventarc.googleapis.com billingbudgets.googleapis.com --project=$PROYECTO
$CUENTAS = @{
  "sa-backend-pruebas"      = @("roles/cloudsql.client", "roles/aiplatform.user", "roles/dlp.user", "roles/storage.objectAdmin")
  "sa-frontend-pruebas"     = @()
  "sa-vault-worker-pruebas" = @("roles/cloudsql.client", "roles/storage.objectAdmin")
  "sa-eventarc-pruebas"     = @("roles/eventarc.eventReceiver")
  "sa-migraciones-pruebas"  = @("roles/cloudsql.client")
  "sa-verificador-pruebas"  = @("roles/run.viewer", "roles/iap.httpsResourceAccessor")
}
foreach ($sa in $CUENTAS.Keys) {
  gcloud iam service-accounts create $sa --project=$PROYECTO
  foreach ($rol in $CUENTAS[$sa]) {
    gcloud projects add-iam-policy-binding $PROYECTO --member="serviceAccount:$sa@$PROYECTO.iam.gserviceaccount.com" --role=$rol --condition=None
  }
}
```

**2. Cloud SQL, buckets, secretos y conector de VPC (EP-05, §2; EP-04, §1 paso 3).** Se aplican `cloud_sql.yaml`, `buckets.yaml` y `secretos.yaml` con Antigravity, con la retención de los buckets en `locked: false` y sin `--lock-retention-period`. Después se crea `public.entorno_marcador` en la base de pruebas (SEC-20) y se guarda la URL de la base solo en `herramientas\url-base-pruebas.txt`.

**3. Servicios, IAP y presupuestos (EP-04, §1 pasos 4 a 7).** Se aplican los tres manifiestos de Cloud Run y sus políticas IAM, se activa IAP y se crean los presupuestos. Antes de seguir, esta compuerta humana:
```powershell
gcloud run services describe evydentia-web --project=$PROYECTO --region=$REGION --format="yaml(metadata.annotations)"
gcloud run services get-iam-policy evydentia-backend --project=$PROYECTO --region=$REGION
```
Debe aparecer `Iap Enabled: true` y, en la política del backend, solo `sa-frontend-pruebas`.

**4. Primer despliegue por digest (EP-06, §3).** Primero con `-SoloMostrar` y luego sin él:
```powershell
$DIGEST = "sha256:<64 hexadecimales de la imagen publicada por el CI>"
$IMAGEN = "$REGION-docker.pkg.dev/$PROYECTO/<repositorio>/<imagen>"
$INSTANCIA = "${PROYECTO}:${REGION}:evydentia-pruebas"
.\scripts\desplegar_entorno_pruebas.ps1 -Proyecto $PROYECTO -Digest $DIGEST -Imagen $IMAGEN -Servicios "evydentia-backend,evydentia-web,evydentia-vault-worker" -InstanciaCloudSql $INSTANCIA -SoloMostrar
.\scripts\desplegar_entorno_pruebas.ps1 -Proyecto $PROYECTO -Digest $DIGEST -Imagen $IMAGEN -Servicios "evydentia-backend,evydentia-web,evydentia-vault-worker" -InstanciaCloudSql $INSTANCIA
```

**5. Siembra (EP-03, §4).**
```powershell
$env:MIGRATION_DATABASE_URL = Get-Content "herramientas\url-base-pruebas.txt" -Raw
& $PY scripts/sembrar_entorno_pruebas.py --testers "herramientas\testers-entorno-pruebas.txt" --bucket "<bucket-de-pruebas>"
Remove-Item Env:MIGRATION_DATABASE_URL
```

**6. Verificador (EP-07, §5): el árbitro de EP-09.**
```powershell
$FRONTEND = gcloud run services describe evydentia-web --project=$PROYECTO --region=$REGION --format="value(status.url)"
$BACKEND = gcloud run services describe evydentia-backend --project=$PROYECTO --region=$REGION --format="value(status.url)"
$env:IAP_AUDIENCIA = "<id-del-cliente-oauth-de-iap>"
$env:VERIFICADOR_CUENTA_SERVICIO = "sa-verificador-pruebas@$PROYECTO.iam.gserviceaccount.com"
& $PY scripts/verificar_entorno_pruebas.py $FRONTEND $BACKEND --proyecto $PROYECTO
$CODIGO = $LASTEXITCODE
& $PY scripts/digest_verificado.py guardar --digest $DIGEST --codigo $CODIGO
"Codigo del verificador: $CODIGO"
```
Debe dar 0, con todas las líneas en `OK`. La cuenta que corre el comando necesita `roles/iam.serviceAccountTokenCreator` sobre `sa-verificador-pruebas`.

**7. Flujo de GitHub.** Se aplica `governance/apoyo/BRIEF_PROPIETARIO_EP07_WORKFLOW.md` (archivo, variables del repositorio `PRUEBAS_*`, entorno `gcp-pruebas` y Workload Identity) y, ya fusionado, se lanza y se consulta:
```powershell
gh workflow run entorno-pruebas.yml --ref main
gh run list --workflow entorno-pruebas.yml -L 1
```

**8. Entrega.** Se llena el registro de abajo, sin identificadores, URL ni correos, y se pasa al CTO la salida de los pasos 3, 6 y 7. EP-09 la cierra el coordinador en un PR de cierre.

### Registro de la puesta en marcha (se llena al ejecutar)
Sin identificadores de proyecto, URL ni correos.

- Fecha y quién lo hizo:
- Decisión 1, borde (opción A o B):
- Decisión 2, Memorystore (mínima o ninguna):
- Decisión 3, horario de Cloud SQL (siempre encendida, 2026-11-08):
- Decisión 4, firma (respuesta de ANF):
- Resultado del verificador (código y líneas):
- Resultado del flujo `entorno-pruebas.yml`:
- Comprobación a mano por rol:
  - [ ] El aviso «Entorno de pruebas · datos ficticios» se ve.
  - [ ] IAP deja pasar solo a quienes prueban.
  - [ ] El inicio de sesión con Google funciona.
  - [ ] Un correo a un destinatario no permitido queda retenido.
  - [ ] La retención de los buckets aparece como no bloqueada en la consola.
- Siguiente versión: llega a producción con el digest verificado en pruebas (GCP-07).
<!-- === fin EP-09 === -->
