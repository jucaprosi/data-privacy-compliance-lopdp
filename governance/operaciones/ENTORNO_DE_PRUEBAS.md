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

Pendiente de EP-06.
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

Pendiente de EP-07.
<!-- === fin EP-07 === -->

<!-- === EP-09 === -->
## 6. Puesta en marcha (EP-09)

Pendiente de EP-09.
<!-- === fin EP-09 === -->
