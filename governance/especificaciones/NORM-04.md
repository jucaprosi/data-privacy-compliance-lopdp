# NORM-04 · El monitoreo de la SPDP descarga de verdad
`¤sdd` `¤vigilancia-spdp` `¤inteligencia-normativa` `¤seguridad` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Hechos medidos en `origin/main` a80da616 y con gcloud de lectura (2026-11-24):
- `services/monitoreo.py:35-41`: `almacen_por_defecto()` lanza `AlmacenNoDisponible` siempre. Su docstring espera el adaptador de EVI-04, que ya está `hecha`.
- `app_core/storage/gcs.py`:
  - `AlmacenGcs(cliente, bucket, credenciales)` tiene `subir` (escritura única con `if_generation_match=0`, que lanza `ObjetoYaExiste`) y `descargar(clave, maximo_bytes)`.
  - `almacen_por_defecto()` usa `GCP_STORAGE_BUCKET`, el de evidencias, y falla cerrado fuera de Cloud Run (`corre_en_cloud_run`).
- `inteligencia_normativa_service.py:142-144`: `_lector()` devuelve `LectorOriginalesCerrado`, que lanza `OriginalNoDisponible`.
- `api/routers/inteligencia_normativa.py:103-106`: `POST /monitoreo` exige `require_operador`, una persona con sesión. Cloud Scheduler no puede usarlo, y no hay en el repositorio ningún verificador de tokens OIDC de Google.
- GCP:
  - el bucket `evydentia-corpus-normativo` existe en `US-CENTRAL1` y está vacío;
  - la API de Cloud Scheduler no está activada;
  - `evydentia-backend` no tiene `NORMATIVA_SPDP_URL_BASE` ni `GCP_STORAGE_BUCKET_NORMATIVO`.

## 2. API

| Ruta | Cambio |
| :--- | :--- |
| `POST /api/v1/normativa/monitoreo/programado` (nueva) | 202 con `{"corrida": "aceptada"}`. Solo acepta `Authorization: Bearer <token OIDC de Google>` de la cuenta de servicio del Scheduler (R3). Si no, 401 sin detalle. Nunca acepta la sesión de una persona. |
| `POST /api/v1/normativa/monitoreo` | Sin cambios: el disparo manual del operador. |
| `GET /api/v1/normativa/resoluciones/{id}/original` | Deja de dar siempre «no disponible»: sirve el original custodiado (R2). |

Las rutas se montan con el prefijo global `/api/v1` (`main.py:189`, `registrar_routers`) más el del router, `/normativa` (`api/routers/inteligencia_normativa.py:27`). La ruta nueva entra en el contrato OpenAPI. Si GEN-05 ya está fusionada, este PR lo regenera; si no, lo hace GEN-05.

## 3. Reglas

- **R1 · Almacén real de originales.** `almacen_normativo.py` implementa `AlmacenOriginales` sobre `AlmacenGcs`:
  - toma el bucket de `GCP_STORAGE_BUCKET_NORMATIVO`, nunca de `GCP_STORAGE_BUCKET`;
  - `guardar` llama a `subir` y devuelve `True`; con `ObjetoYaExiste` devuelve `False`, porque mismo hash es mismo nombre;
  - falla cerrado con `AlmacenNoDisponible` sin conectar fuera de Cloud Run o sin la variable.

  `monitoreo.almacen_por_defecto()` lo devuelve. Su docstring y la cabecera del módulo pasan a estado final, sin «llega con EVI-04».
- **R2 · Lector real.** `_lector()` devuelve un lector sobre `descargar` del mismo bucket, con el tope de tamaño de NORM-01. `LectorOriginalesCerrado` se queda solo como respuesta cuando falta la configuración.
- **R3 · Disparo programado con identidad de servicio.** `disparo_programado.verificar(token)` usa `google.oauth2.id_token.verify_oauth2_token` y acepta el token solo si:
  - la firma es de Google;
  - `aud` es igual a `NORMATIVA_SCHEDULER_AUDIENCE`, que es la URL completa `https://<host del backend>/api/v1/normativa/monitoreo/programado`, la misma que el destino del trabajo de Scheduler;
  - `email` es igual a `NORMATIVA_SCHEDULER_CUENTA` y `email_verified` es verdadero.

  Cualquier otra cosa da 401. Con alguna variable vacía, todas las peticiones dan 401, así que falla cerrado. La ruta llama a `disparar_monitoreo("programado")` en segundo plano. No registra el token ni el correo en los logs.
- **R4 · Una corrida a la vez.** Si en `normativa_monitoreo_logs` hay una corrida con `fin IS NULL` e `inicio` de hace menos de 30 minutos, el disparo programado responde 202 sin abrir otra, y la bitácora no se duplica. La corrida se abre como `fallida` y se cierra con `ok`, `parcial` o `fallida` (`monitoreo.py:59,127`). El origen nuevo, `programado`, cabe en `origen varchar(20)`.
- **R5 · Sin la URL no hay corrida.** Sin `NORMATIVA_SPDP_URL_BASE`, la corrida queda `fallida` con `FuenteSinConfigurar` (NORM-01) y se avisa al operador (NORM-02). No cambia.
- **R-ADPA · Ortogonalidad ZERAG (`NORM-04`).** Solo los archivos de la propiedad. Las secciones `#NORM-04` del servicio y del router no tocan el código de NORM-01 ni de NORM-02. `app_core/storage` no cambia.

## 4. Interfaz

Sin cambios de texto. La pantalla del Centro de vigilancia (NORM-02) ya muestra la bitácora y el original.

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** un `AlmacenGcs` doble, **entonces** `guardar` da `True` la primera vez y `False` con `ObjetoYaExiste`, y usa el bucket de `GCP_STORAGE_BUCKET_NORMATIVO`. Mutación m1: usar `GCP_STORAGE_BUCKET` da rojo. | `test_norm04_almacen_y_disparo.py` |
| **Dado** que no corre en Cloud Run o falta la variable, **entonces** `AlmacenNoDisponible` sin crear cliente. Mutación m2: crear el cliente antes de comprobar da rojo. | ídem |
| **Dado** un original guardado, **entonces** `GET …/original` lo sirve con la misma huella. Mutación m3: volver al lector cerrado da rojo. | ídem |
| **Dado** un token con otro `aud`, otro `email`, `email_verified` falso o una sesión de persona, **entonces** 401. Mutación m4: no comprobar `email` da rojo. Mutación m5: aceptar con las variables vacías da rojo. | ídem, `verify_oauth2_token` sustituido por un doble |
| **Dado** una corrida con `fin` nulo de hace 5 minutos, **entonces** el disparo programado no abre otra. Mutación m6: quitar la comprobación da rojo. | ídem, PostgreSQL |
| **Dado** las suites de NORM-01 y NORM-02, **entonces** siguen en verde. | existentes |

## 6. Trazabilidad

- Medición del Arquitecto (2026-11-24), pedida por el CTO para BIB-403 R2.
- Depende de NORM-01 y NORM-02 (módulo y Centro de vigilancia), de EVI-04 (`subir`) y de GCP-01 (proyecto y Cloud Run).
- Brief del propietario: `C:\Users\Juan Carlos\compartido\evydentia\briefs\NORM-04-propietario-gcp.md`.
- Tras el despliegue, el propietario comprueba que hay una corrida `completada` en la bitácora y objetos en `gs://evydentia-corpus-normativo/spdp/`.
