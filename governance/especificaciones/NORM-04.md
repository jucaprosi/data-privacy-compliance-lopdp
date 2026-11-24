# NORM-04 · El monitoreo de la SPDP descarga de verdad
`¤sdd` `¤vigilancia-spdp` `¤inteligencia-normativa` `¤seguridad` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Hechos medidos en `origin/main` 475f8a6a y con gcloud de lectura (2026-11-24).

**Diseño de NORM-01, ya ejecutado** (`governance/operaciones/BRIEF_PROPIETARIO_BUCKET_NORMATIVO.md`, 2026-11-12):
- Bucket propio `evydentia-corpus-normativo`, en `US-CENTRAL1`, vacío.
- Cuenta propia del monitoreo, `sa-evydentia-normativa`, con el rol `projects/evydentia/roles/corpusNormativoEscritura` (`storage.objects.create` y `storage.objects.get`, sin borrar ni sobrescribir) sobre el bucket.
- El backend (`sa-evydentia-backend`) solo lee, con `roles/storage.objectViewer` (decisión 5).
- Política leída hoy: el backend tiene además `roles/storage.objectCreator`. Lo concedió la fase 1 del brief de Antigravity de la versión anterior de esta ficha, y se revoca (brief, paso 1).

**Código.**
- `services/monitoreo.py:35-41`: `almacen_por_defecto()` lanza siempre.
- `monitoreo.py:49-54`: el monitoreo escribe en la base con `SET LOCAL ROLE lopdp_normativa`, el mismo rol que ya usa `revision.py:138` desde el backend. La conexión del Job, la de `DATABASE_URL`, puede adoptarlo.
- `inteligencia_normativa_service.py:142-144`: `_lector()` devuelve `LectorOriginalesCerrado`. `disparar_monitoreo(origen)` (`:173`) corre la corrida y avisa al operador si falla.
- `app_core/storage/gcs.py`:
  - `AlmacenGcs(cliente, bucket, credenciales)` tiene `subir` (escritura única, lanza `ObjetoYaExiste`) y `descargar`.
  - `almacen_por_defecto()` exige `corre_en_cloud_run()`, y `app_core/config.py:48-54` lo define como `K_SERVICE` presente.
  - **Un Cloud Run Job no define `K_SERVICE`, sino `CLOUD_RUN_JOB`**, así que ese guardián no sirve dentro del Job.

**Patrón de Job que ya existe.** `evydentia-migrate`:
- corre la imagen del backend, fijada por digest, con `command` sustituido;
- usa la anotación `run.googleapis.com/cloudsql-instances` y las variables `ENVIRONMENT`, `PROJECT_ID` y `DATABASE_URL`;
- tiene su propia cuenta.

`deploy-gcp.yml` solo despliega el servicio y no toca los Jobs, así que el digest del Job lo actualiza el propietario, como con `evydentia-migrate`.

## 2. API

Sin cambios. No hay ruta de disparo programado: el Scheduler ejecuta el Job por la API de Cloud Run, no por HTTP al backend. `GET /api/v1/normativa/resoluciones/{id}/original` sirve el original custodiado (R2).

## 3. Reglas

- **R1 · Almacén de escritura, solo en el Job.** `almacen_normativo.py` implementa `AlmacenOriginales` sobre `AlmacenGcs`:
  - toma el bucket de `GCP_STORAGE_BUCKET_NORMATIVO`, nunca de `GCP_STORAGE_BUCKET`;
  - `guardar` devuelve `True` tras `subir` y `False` con `ObjetoYaExiste`;
  - falla cerrado con `AlmacenNoDisponible`, sin crear el cliente, si falta la variable o si `CLOUD_RUN_JOB` no está definida. Solo escribe desde un Job.

  `monitoreo.almacen_por_defecto()` lo devuelve. Las cabeceras quedan en estado final, sin «llega con EVI-04».
- **R2 · Lector, en el backend.** `_lector()` devuelve un lector sobre `descargar` del mismo bucket, con el tope de NORM-01, y exige `K_SERVICE` y la variable. Si falta alguna, `LectorOriginalesCerrado`. No usa ningún permiso de escritura.
- **R3 · Punto de entrada del Job.** `trabajo_monitoreo.py` (`python -m features.inteligencia_normativa.trabajo_monitoreo`):
  - llama a `disparar_monitoreo("programado")`;
  - sale con 0 si la corrida queda `ok` o `parcial`, y con 1 si queda `fallida`, para que el Job registre el fallo;
  - no imprime la URL de la base ni secretos.

  El origen `programado` cabe en `origen varchar(20)`.
- **R4 · Una corrida a la vez.** Antes de abrir otra, comprueba que no haya en `normativa_monitoreo_logs` una corrida con `fin IS NULL` e `inicio` de hace menos de 30 minutos. Si la hay, sale con 0 sin abrir otra. El Job se crea con `--tasks=1 --max-retries=0` (brief).
- **R5 · Sin la URL de la SPDP no hay corrida.** Sin `NORMATIVA_SPDP_URL_BASE`, la corrida queda `fallida` con `FuenteSinConfigurar` y se avisa al operador (NORM-01 y NORM-02).
- **R-ADPA · Ortogonalidad ZERAG (`NORM-04`).** Solo los archivos de la propiedad. `app_core/storage`, `app_core/config.py`, la API y el router no cambian. La sección vacía `=== NORM-04 ===` del router que sembró la versión anterior se retira en este PR.

## 4. Interfaz

Sin cambios.

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** `CLOUD_RUN_JOB` y `GCP_STORAGE_BUCKET_NORMATIVO` y un `AlmacenGcs` doble, **entonces** `guardar` da `True` la primera vez y `False` con `ObjetoYaExiste`. Mutación m1: usar `GCP_STORAGE_BUCKET` da rojo. | `test_norm04_almacen_y_trabajo.py` |
| **Dado** solo `K_SERVICE` (el backend), o falta la variable, **entonces** `AlmacenNoDisponible` sin crear el cliente. Mutación m2: aceptar `K_SERVICE` para escribir da rojo. | ídem |
| **Dado** un original guardado, **entonces** el backend lo sirve con la misma huella. Mutación m3: volver al lector cerrado da rojo. | ídem |
| **Dado** una corrida `fallida`, **entonces** el punto de entrada sale con 1; con `ok` o `parcial`, con 0. Mutación m4: salir siempre con 0 da rojo. | ídem |
| **Dado** una corrida con `fin` nulo de hace 5 minutos, **entonces** no abre otra. Mutación m5: quitar la comprobación da rojo. | ídem, PostgreSQL |
| **Dado** la salida del punto de entrada, **entonces** no contiene la URL de la base. Mutación m6: imprimir `DATABASE_URL` da rojo. | ídem |
| **Dado** las suites de NORM-01 y NORM-02, **entonces** siguen en verde. | existentes |

## 6. Trazabilidad

- **PRD:** §4, Módulo 6.1, «Ejecución y reparto de privilegios»; ley fundacional 13.
- Diseño de NORM-01 (brief del bucket, decisiones 4, 5 y 8) y reconciliación pedida por el CTO (2026-11-24).
- Depende de NORM-01 y NORM-02, de EVI-04 (`subir` y `descargar`) y de GCP-01.
- Brief del propietario: `C:\Users\Juan Carlos\compartido\evydentia\briefs\NORM-04-propietario-gcp.v3.md`. Sustituye a la v1 y a la v2.
- El control «norma cambiada» de BIB-403 R2 se activa con la primera corrida `ok`.
