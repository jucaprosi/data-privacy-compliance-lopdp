# Programa RET · Choques de propiedad y correcciones al programa

Fecha: 2026-11-13. Arquitecto ADPA, para el Tech Lead. Medido en `origin/main` 43e59ee4 contra `governance/apoyo/RETIRO_PLATAFORMAS_PMV.md` (PR #763). Solo lectura: `git grep`, `git show` y la propiedad de las fichas con estado distinto de `hecha`.

> **Convención.** «BG» es la serie de fichas del árbitro vigente de la base gestionada del PMV (BG-00 a BG-04), y «el árbitro vigente» es su prueba en `tests/`. Este documento no escribe el nombre del proveedor porque ese árbitro no admite menciones nuevas.

## Qué se entrega

Siete especificaciones en `governance/especificaciones/`: RET-00, RET-01, RET-02, RET-03, RET-05, RET-06 y RET-07.

- **No hay `RET-04.md`.** El programa dice que RET-04 no es ficha nueva: la cubren IA-04, IA-06 e IA-08. El árbitro exige que cada especificación tenga su ficha.
- **`verificar_especificaciones.py` queda en rojo en esta rama sola,** con siete hallazgos del tipo «no existe governance/tareas/RET-NN.md». Es el orden del programa: las fichas las escribe el Tech Lead a partir de estas especificaciones. Tienen que ir en el mismo PR. Con las fichas simuladas, las siete cumplen los seis apartados y cada escenario nombra su prueba.

## Choques de propiedad

| Ficha RET | Archivo | Dueña abierta | Propuesta |
| :--- | :--- | :--- | :--- |
| RET-01 | `.env.example` | IA-08 y BG-02 (pendientes) | RET-01 lo retira. Sale de la propiedad de IA-08; BG-02 se absorbe en RET-06. |
| RET-01 | `requirements.txt` | IA-08 (pendiente) | Lo tocan RET-01 (`python-dotenv`), RET-02 (`boto3`), IA-08 (`openai`) y RET-07. Ordenarlas en `depende_de`: RET-01 → RET-02 → IA-08 → RET-07. |
| RET-01 | `jobs/purga_demo/guardias.py` | DEMO-05 (en curso), DEMO-05c y DEMO-05d (pendientes) | Importa `huellas_produccion`. RET-01 no lo edita: mantiene la firma pública de `huellas_produccion` que ese archivo usa, o espera a DEMO-05. |
| RET-02 | `app_core/storage/r2.py`, `app_core/storage/gcs.py` | EVI-04 (en curso) | `depende_de = ["EVI-04"]`. EVI-04 añade `subir` en los dos archivos; RET-02 retira `r2.py` después. |
| RET-02 | `api/routers/roadmaps.py`, `features/roadmap/services/evidencia_engine.py` | RM-25b (pendiente) | Ordenar RET-02 y RM-25b. Recomiendo RM-25b después de RET-02, para que su validación final ya se escriba sobre GCS. |
| RET-02 | `features/evidencias/evidencias_service.py` | EVI-03 y EVI-04 (en curso), por sección | Importa de `app_core.storage`. Si necesita cambiar el import de límites, va en una sección propia o después de EVI-04. |
| RET-03 | `features/roadmap/services/generacion_engine.py` | IA-06 (pendiente) | Ahí viven `enqueue_generation` y `get_job`. O RET-03 va antes de IA-06 y la ordena, o IA-06 retira la cola al reescribir el motor. Recomiendo RET-03 → IA-06. |
| RET-03 | `api/routers/roadmaps.py`, `frontend/src/lib/roadmap/cliente.ts` | RM-25b; y RET-02 | **RET-02 y RET-03 no pueden ir en paralelo:** comparten el router y el cliente. Orden propuesto: RET-02 → RET-03. |
| RET-05 | `tests/test_sec16_secretos_obligatorios.py`, `tests/test_sec17_configuracion_nube.py` | SEC-21 (en curso) | Importan `api.index`. `depende_de = ["SEC-21"]`, o SEC-21 cambia el import a `main` en su propio PR. |
| RET-06 | `tests/test_diagnostico_respuestas.py`, `tests/test_diagnostico_resultados.py` | DIAG-07 (en curso) | El dominio diagnóstico de RET-06 va después de DIAG-07. |
| RET-06 | los 46 archivos de BG-02 | BG-02 (pendiente) | BG-02 se cierra como absorbida; sus archivos pasan a la propiedad de RET-06, repartidos por dominio. |

Sin dueña abierta, medido: `app_core/config.py`, `app_core/security.py`, `app_core/huellas_produccion.py`, `tests/conftest.py`, `alembic/env.py`, `.githooks/pre-push`, `scripts/arnes_local.py`, `app_core/entorno/guardias.py`, `app_core/queue/redis_client.py`, `features/roadmap/roadmap_service.py`, `vercel.json`, `frontend/vercel.json`, `api/index.py`, `frontend/next.config.ts`, `frontend/src/lib/roadmap/subirEvidencia.ts`, `mockServer.ts` y las pruebas que el programa lista para RET-01, RET-02 y RET-03.

RM-26, RM-27 y DIAG-07 no chocan con RET-02 ni RET-03: poseen archivos propios (`cifras_engine.py`, `revision_engine.py`, `roadmap_revision.py`, `objeciones_engine.py`).

## Correcciones al programa

1. **RET-05: el programa dice que `test_cabeceras_seguridad.py` «sigue verde». No es así.** Su línea 47 lee `vercel.json` y afirma `functions["api/index.py"].maxDuration == 300`. Al retirar `vercel.json` se rompe. La especificación retira esa afirmación y pasa los 300 s de RM-13 al manifiesto de Cloud Run.
2. **RET-05: `api/index.py` sí se importa.** Lo usan `test_health_routers.py` (el `/health` de emergencia en 503), `test_sec16_secretos_obligatorios.py:132` y `test_sec17_configuracion_nube.py:165`. Las cuatro pruebas cambian en la misma ficha.
3. **RET-03: el frontend sí tiene código para la ruta de trabajos.** `cliente.ts:195` define `getJob` y `mockServer.ts:400` la atiende. No medí si alguna pantalla la llama; la especificación manda comprobarlo primero y detenerse si se usa.
4. **RET-01: `/cloudsql/` no debería contar como base local.** Es el socket con el que Cloud Run se conecta a Cloud SQL, también a la de producción. La especificación lo deja fuera de la lista hasta que el CTO decida. Es una decisión de seguridad, no la cierro yo.
5. **RET-01: `huellas_produccion` tiene más usuarios que los que lista el programa:** `app_core/entorno/guardias.py`, `jobs/purga_demo/guardias.py`, `scripts/capacidades_biblioteca.py`, `scripts/crear_organizacion_dev.py`, `scripts/demo/sembrar_plantilla.py` y `scripts/sembrar_entorno_pruebas.py`. Entran en la propiedad de RET-01 o conservan la firma que usan.
6. **RET-02: los límites de tamaño los usa también la sala evidencias.** `features/evidencias/services/evidencias_engine.py:181` importa `TAMANO_MAXIMO_BYTES` y `motivo_de_rechazo` de `r2.py`. Entra en la propiedad de RET-02.
7. **RET-00: la carpeta de pendientes del árbitro vigente tiene cinco listas,** no solo la de BG-02: también FIRMA-02, BG-01, BG-03 y BG-04. Solo la de BG-02 pasa a RET-06.

## Orden propuesto

RET-00 → RET-01 → RET-02 (tras EVI-04) → RET-03 → IA-06; en paralelo con RET-02, RET-05 (tras SEC-21); RET-06 por dominios, con diagnóstico tras DIAG-07; IA-08; RET-07.

Lo que cambia frente al programa: RET-02 y RET-03 pasan de paralelo a secuencia, y RET-02 y RET-05 esperan a EVI-04 y SEC-21.

## Pendiente de decisión

- CTO: si `/cloudsql/` cuenta como base local en la guardia de RET-01.
- Tech Lead: el orden entre RET-02 y RM-25b, y entre RET-03 e IA-06.

## Adenda · segunda decisión del propietario (programa en 39dbf4b5)

RET-00 y RET-07 quedan reescritas: el árbitro va sin lista blanca de historia y RET-07 pasa a «Historia del PMV fuera de `main`» (sala gobernanza). Las otras cinco solo cambian su línea de trazabilidad. La corrección 7 de arriba sigue valiendo para el reparto de pendientes; las listas de BG-01, BG-03, BG-04 y FIRMA-02 pasan a pendientes de RET-07 cuando salgan las fichas BG.

Puntos nuevos que el programa no resuelve:

1. **Bibliografía.** Una fuente cuyo título o URL nombra al proveedor no se puede «reformular» sin falsear la cita. RET-07 no cambia títulos ni URLs: las lista y las decide el CTO (salen de `main` con lo que solo se apoya en ellas, o el propietario acepta una exclusión). Sin lista blanca, el árbitro las marcará en rojo hasta esa decisión.
2. **Partes fechados.** La regla del proyecto es que un parte fusionado no se edita. La decisión del propietario la exceptúa solo para sustituir el nombre del proveedor; RET-07 lo declara en su PR.
3. **el árbitro vigente es árbitro mínimo de cada fusión.** RET-07 solo lo retira cuando el árbitro de RET-00 ya está en `main` y en esa lista. Si la lista vive en un workflow o en un verificador, es del propietario: brief antes del PR de RET-07.
4. **Fichas BG-00 a BG-04.** Al retirarlas hay que quitar sus citas en `depende_de`, sus exenciones y sus listas de pendientes, y comprobar que ningún archivo queda con propiedad a nombre de una ficha inexistente. No medí cuántas fichas las citan.
5. **Comprobación contra `pmv/consolidacion`.** RET-07 compara por blob de git cada archivo antes de retirarlo. No lo medí: no comparé `main` con esa rama.
6. **Tamaño.** Reformular menciones en fichas `hecha`, aportes, bibliografía e informes toca muchos archivos de muchas fichas. Va en un solo PR de gobernanza, sin trocear por dueña, porque todas las dueñas están `hecha`.
