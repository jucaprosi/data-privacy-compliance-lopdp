# Parte de nube · Diagnóstico de la revisión evydentia-backend-00006-7ks (GCP-11)

Fecha de las lecturas: 2026-11-14 (UTC). Solo lectura con `gcloud` (proyecto `evydentia`, región `us-central1`); no se leyó ningún valor de secreto, no se desplegó ni se cambió nada.

## Conclusión

**Causa: el backend murió al importar la aplicación porque `DATABASE_URL` no pasó la guardia de SEC-17; la causa del valor que no pasó es «probable: marca de orden de bytes UTF-8 (BOM) al inicio del secreto», no confirmada.** Lo medido es cierto hasta el mensaje de error; el BOM solo lo confirma el árbitro del propietario sobre la versión 1 (`python scripts/verificar_secretos_sin_bom.py --proyecto evydentia --version 1`, paso 4 del brief). No es un fallo de puerto ni de tiempo de espera: el aviso de «no escuchó en el puerto 8080» es la consecuencia de que el proceso ya había terminado.

## Evidencia (salida de cada comando de lectura, sin valores)

1. **Registro de error de la 00006** (`gcloud logging read ... severity>=ERROR`, 2026-11-13 13:55:53 UTC): el traceback termina en `app_core/config.py` línea 171 (llamada a `exigir_configuracion_en_la_nube()`), línea 165 (`raise RuntimeError(`), con el texto «INV_LOPDP_CLOUD_CONFIG_FAILS_CLOSED: el backend no arranca en la nube porque DATABASE_URL no es de PostgreSQL». A las 13:55:54 Cloud Run registra «STARTUP TCP probe failed … on port 8080. The instance was not started».
2. **Estado de la revisión** (`gcloud run revisions describe`): 00006 creada 2026-11-13 13:55:32, condición «failed to start and listen on the port defined provided by the PORT=8080». 00007-g7q creada 2026-11-14 01:35:01, «Containers became healthy in 26.37s» y «Deploying revision succeeded in 28.96s».
3. **Comparación 00006 y 00007-g7q**: `diff` de la descripción (imagen, variables de entorno y referencias a secretos) da diferencias solo en las fechas. Misma imagen (`backend@sha256:520f176e…`), mismas variables (`APP_ENV`, `ENVIRONMENT`, `PROJECT_ID`, `GCP_STORAGE_BUCKET`, `PROXIES_CONFIABLES`, `CORS_ORIGINS`) y mismos secretos (`DATABASE_URL`←`DATABASE_URL_APP`, `JWT_SECRET`, `SESSION_SECRET`, `INVENTARIO_CLAVE_CIFRADO`, todos `latest`).
4. **Versiones de los secretos** (`gcloud secrets versions list`, solo metadatos): `DATABASE_URL_APP` v1 2026-11-07 19:37 y v2 2026-11-14 01:34; `JWT_SECRET` v1 2026-11-13 09:35 y v2 01:34; `SESSION_SECRET` v1 2026-11-13 09:35 y v2 01:34. Como las revisiones apuntan a `latest`, la 00006 (13:55 del día 13) tomó la versión 1 y la 00007 (01:35 del día 14, un minuto después de crear la 2) tomó la versión 2.

## Razonamiento

Con imagen y nombres idénticos, lo único que cambió entre una revisión que muere y otra sana es el contenido de las versiones de los secretos. La guardia comprueba `url.lower().startswith("postgresql")`; Python no considera el BOM (U+FEFF) un espacio, así que `.strip()` no lo quita y el esquema deja de reconocerse. El propietario informó de que la versión 1 tenía BOM y la 2 no; es coherente con todo lo anterior, pero esta sesión no leyó los valores.

## Hallazgos adicionales

- **El manifiesto está desfasado respecto a la realidad.** `governance/operaciones/cloudrun_service.yaml` toma `DATABASE_URL` del secreto llamado `DATABASE_URL` y no declara `JWT_SECRET`, `SESSION_SECRET` ni `INVENTARIO_CLAVE_CIFRADO`; la revisión real usa `DATABASE_URL_APP` y los cuatro secretos (los carga `deploy-gcp.yml` con `--set-secrets`). Aplicar el manifiesto con `gcloud run services replace` sin corregirlo rompería el arranque. El manifiesto es de GCP-05 y la corrección va en ficha aparte; `tests/test_gcp11_manifiesto_secretos.py` fija hoy lo que sí es cierto (nada de valores en claro).
- **Complemento en el código** (`app_core/config.py#SEC-17`): `exigir_configuracion_en_la_nube` ahora dice «empieza por una marca de orden de bytes» cuando `DATABASE_URL` la lleva, sin quitarla en silencio ni imprimir el valor. La próxima vez el registro dirá la causa en lugar de «no es de PostgreSQL».

## Qué hace el propietario

Brief: `governance/operaciones/BRIEF_PROPIETARIO_REVISION_00006.md`. Lecturas primero; crear una versión sin BOM es un paso aparte, solo si el árbitro muestra CON BOM, y el árbitro y la comprobación del esquema se repiten antes de cada despliegue.

## Cierre formal (2026-11-15)

Rama `tarea/juan-carlos/gcp-11`, desde `origin/main` 844f5ebe. Sin cambios de código: solo se corrieron los árbitros, sus mutaciones y las lecturas.

### Lecturas repetidas (solo lectura, cuenta del propietario en `gcloud`, proyecto `evydentia`, `us-central1`)

| Comando | Código | Resultado |
| :-- | :-- | :-- |
| `gcloud logging read ... revision_name="evydentia-backend-00006-7ks" AND severity>=ERROR` | 0 | 13:55:54 «STARTUP TCP probe failed … on port 8080»; traceback `app_core/config.py` línea 171 → línea 165 `raise RuntimeError(`; «INV_LOPDP_CLOUD_CONFIG_FAILS_CLOSED: el backend no arranca en la nube porque DATABASE_URL no es de PostgreSQL». Igual que el 2026-11-14. |
| `gcloud run revisions describe evydentia-backend-00006-7ks --format="value(status.conditions[].message)"` | 0 | «failed to start and listen on the port defined provided by the PORT=8080 …»; «Revision retired». |
| `gcloud run revisions describe` de 00006-7ks y 00007-g7q (imagen y `env`, sin fechas) pasado por `md5sum` | 0 | El mismo resumen en las dos: `c92261a5e623bf8db80d6043dd17100e`. Misma imagen `backend@sha256:520f176e…` y mismas referencias a secretos. |
| `gcloud secrets versions list` de `DATABASE_URL_APP`, `JWT_SECRET` y `SESSION_SECRET` (solo metadatos) | 0 | v1 y v2 `enabled`; v2 de los tres creadas 2026-11-14 01:34:02, 01:34:07 y 01:34:12, antes de la 00007 (01:35:01). |
| `gcloud run revisions list --service evydentia-backend` | 0 | Nueve revisiones; la 00006 y la 00007 comparten imagen. |
| `gcloud run services describe evydentia-backend --format="value(status.traffic)"` | 0 | Hoy el 100 % del tráfico va a `evydentia-backend-00009-jk4` (la 00007-g7q ya no es la última; no cambia el diagnóstico). |
| `gcloud logging read ... revision_name="evydentia-backend-00005-77h" AND severity>=ERROR` | 0 | La 00005 también murió, por otra guardia: «INV_LOPDP_NO_DEFAULT_SECRETS_IN_CLOUD: … falta JWT_SECRET; falta SESSION_SECRET» (cargaba `JWT_SECRET_KEY`). Por eso ninguna revisión con esta guardia había leído antes la v1 de `DATABASE_URL_APP` hasta la 00006. |

No se leyó ningún valor de secreto. La conclusión no cambia: la causa medida es la guardia SEC-17 sobre `DATABASE_URL`; el BOM en la v1 sigue siendo **probable, no confirmado** por esta sesión, y lo confirma solo el árbitro del propietario (paso 4 del brief).

### Árbitros

| Árbitro | Código |
| :-- | :-- |
| `python -m pytest tests/test_gcp11_secretos_sin_bom.py tests/test_gcp11_manifiesto_secretos.py tests/test_gcp11_brief_solo_lectura.py tests/test_gcp11_bom_configuracion.py` | 0 (19 passed) |
| `python scripts/generar_indice_tareas.py --verificar` | 0 («OK: 390 tareas, independencia verificada.») |

### Mutaciones (cada una aplicada en el árbol de trabajo y revertida con `git checkout --`)

| Árbitro | Mutación | Resultado |
| :-- | :-- | :-- |
| `tests/test_gcp11_secretos_sin_bom.py` | `scripts/verificar_secretos_sin_bom.py` línea 46: `return "sin BOM"` sin comparar con el BOM | código 1; FAILED `test_un_secreto_con_bom_da_codigo_1_y_lo_nombra` (1 failed, 5 passed) |
| `tests/test_gcp11_manifiesto_secretos.py` | `cloudrun_service.yaml`: `DATABASE_URL` con `value:` literal en lugar de `secretKeyRef` | código 1; FAILED `test_el_manifiesto_toma_la_base_de_secret_manager` (1 failed, 2 passed) |
| `tests/test_gcp11_brief_solo_lectura.py` | brief: el primer `gcloud run revisions describe` pasa a `gcloud run deploy` | código 1; FAILED `test_los_bloques_de_lectura_no_cambian_recursos` (1 failed, 5 passed) |
| `tests/test_gcp11_brief_solo_lectura.py` | brief: `$Valor = gcloud secrets versions access` sin asignar | código 1; FAILED `test_ningun_bloque_imprime_el_valor_de_un_secreto` (1 failed, 5 passed) |
| `tests/test_gcp11_bom_configuracion.py` | `app_core/config.py#SEC-17` línea 111: `if False:` en lugar de `if url.startswith(MARCAS_DE_ORDEN_DE_BYTES):` | código 1; FAILED los dos casos de `test_el_bom_se_nombra_sin_imprimir_el_valor` (2 failed, 2 passed) |
| `scripts/generar_indice_tareas.py --verificar` | ficha `GCP-11`: `depende_de` con `NO-EXISTE-99` | código 1; «ERROR: GCP-11: depende de «NO-EXISTE-99», que no existe» |

Tras revertir, `git status` sin cambios en esos archivos y el índice vuelve a código 0.
