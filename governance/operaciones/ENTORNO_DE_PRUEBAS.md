# Entorno de pruebas de EVYDENTIA en Google Cloud
`¤entorno-pruebas` `¤cloud-run-perf`

> Procedimiento operativo del entorno de pruebas. El contrato (qué es, qué lo aísla de producción y qué interfaz comparten las tareas) está en `governance/artefactos/PRD_EVYDENTIA_REVENTA_NUBE.md`, §5.5, y sus invariantes en `INVARIANTS_EVYDENTIA_REVENTA_NUBE.md`, apartado 7. Este documento no lleva identificadores de proyecto, URL de conexión, contraseñas, claves ni correos reales: los valores viven en Secret Manager del proyecto de pruebas y en los archivos locales de `herramientas`.

Cada apartado es la sección reservada de una tarea (`governance/tareas/EP-0x.md`), y cada tarea escribe solo dentro de la suya. Los manifiestos están en `governance/operaciones/entornos/pruebas/`.

<!-- === EP-04 === -->
## 1. Proyecto, servicios de Cloud Run, acceso y presupuesto (EP-04)

Pendiente de EP-04.
<!-- === fin EP-04 === -->

<!-- === EP-05 === -->
## 2. Cloud SQL, buckets y secretos (EP-05)

Pendiente de EP-05.
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

1. Comprueba que `origin/main` tiene una sola cabeza de Alembic.
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
3. Recrea la base.
4. Migra.
5. Vacía los buckets.
6. Llama a `scripts/sembrar_entorno_pruebas.py`.

Todo comando de `gcloud` lleva `--project` con el proyecto recibido.

**Si falla un paso.** El script se detiene con `DETENIDO: <motivo>` y no sigue. Esa noche no se promueve nada a producción, ni siquiera un digest verificado antes. Para corregirlo:

- Si falló la cabeza de Alembic, se fusionan las cabezas (`FUSION_ALEMBIC.md`).
- Si falló la migración o el despliegue, se corrige en `main` y se repite el ciclo con un digest nuevo.
- Si el verificador falla, se registra su código con `guardar`, y ese digest queda rechazado para la promoción.
<!-- === fin EP-06 === -->

<!-- === EP-03 === -->
## 4. Datos ficticios y cuentas de quienes prueban (EP-03)

Pendiente de EP-03.
<!-- === fin EP-03 === -->

<!-- === EP-07 === -->
## 5. Verificación (EP-07)

Pendiente de EP-07.
<!-- === fin EP-07 === -->

<!-- === EP-09 === -->
## 6. Puesta en marcha (EP-09)

Pendiente de EP-09.
<!-- === fin EP-09 === -->
