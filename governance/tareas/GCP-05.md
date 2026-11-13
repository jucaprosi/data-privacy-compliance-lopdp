+++
id = "GCP-05"
titulo = "Escalado verificable en Cloud Run: límites de instancias, presupuesto de conexiones y prueba de carga"
ola = "C"
estado = "en_curso"
sala = "operaciones"
depende_de = ["GCP-01", "GCP-03", "GCP-04", "GCP-08", "GCP-09", "CI-21", "EP-04"]
propiedad = ["governance/operaciones/cloudrun_service.yaml", "governance/operaciones/cloudrun_frontend_service.yaml", "governance/operaciones/PRUEBA_DE_CARGA.md", "scripts/prueba_carga.py", "tests/test_gcp05_escalado.py", "app_core/db/session.py#GCP-05", "governance/operaciones/presupuesto_conexiones.yaml", "tests/test_ci21_sin_import_yaml.py", "governance/operaciones/entornos/pruebas/cloudrun_backend.yaml", "tests/test_ep04_computo_pruebas.py", "app_core/db/pool.py"]
crea = ["governance/operaciones/presupuesto_conexiones.yaml", "app_core/db/pool.py"]
arbitro = "pytest tests/test_gcp05_escalado.py + suite completa + vigilantes; prueba de carga contra el entorno de pruebas con su informe en PRUEBA_DE_CARGA.md"
rastros = ["¤cloud-run-perf", "¤arbitro"]
+++
# GCP-05 · Escalado verificable en Cloud Run: límites de instancias, presupuesto de conexiones y prueba de carga

**Origen.** Revisión de la constitución de la reventa en la nube contra los diez requisitos de una aplicación vendible, 2026-11-04. GCP-01 fija `--concurrency=80`, pero ni el PRD ni las tareas fijan el mínimo y el máximo de instancias ni exigen medir que la plataforma escala.

**Contrato:** `governance/especificaciones/GCP-05.md`.

## Entrega
- Mínimo y máximo de instancias y concurrencia explícitos en `governance/operaciones/cloudrun_service.yaml` (backend, creado por GCP-01) y `governance/operaciones/cloudrun_frontend_service.yaml` (frontend, creado por GCP-03). Va después de ambas, así que no comparte archivo con una tarea simultánea.
- Prueba `tests/test_gcp05_escalado.py` que lee los manifiestos y comprueba el presupuesto de conexiones contra el límite de PgBouncer y Cloud SQL de GCP-04.
- Script `scripts/prueba_carga.py`: usuarios simultáneos simulados contra el **entorno de pruebas** (nunca producción); escribe percentiles de latencia y errores.
- Informe `governance/operaciones/PRUEBA_DE_CARGA.md` con la fecha, el entorno, la configuración y los resultados de la corrida.

## Decisiones asumidas
- Backend: mínimo 0 instancias en pruebas y en producción hasta la fase beta (PRD §5.4, pilar 9; PR #737); al llegar la beta, el propietario cambia `--min-instances` en `deploy-gcp.yml`. Máximo 10. Frontend: mínimo 0, máximo 5. El máximo también es un tope de gasto. El propietario los ajusta.
- Meta inicial de la prueba de carga: 200 usuarios simultáneos en lectura con p95 menor que 800 ms y ningún 5xx.

## Pruebas
- `pytest tests/test_gcp05_escalado.py` comprueba que ambos manifiestos declaran mínimo, máximo y concurrencia, y que `max_instancias × tamaño_del_pool ≤ conexiones_de_PgBouncer`.
- `python scripts/prueba_carga.py --entorno pruebas` y su informe; el script se niega a correr contra el host de producción y exige que `GET /api/v1/entorno` responda `pruebas` (`EP-01`).

**Entorno de pruebas (2026-11-05).** El entorno lo definen `PRD.md` §5.5 y las tareas `EP-01`…`EP-09`, y sus manifiestos de `governance/operaciones/entornos/pruebas/` fijan allí el mínimo 0 de instancias. La prueba de carga necesita la puesta en marcha (`EP-09`). Como esa ficha va en una tanda posterior, no figura en `depende_de`: si `EP-09` no está hecha cuando se toma esta tarea, la prueba de carga espera.

**Ampliación 2026-11-11 (Arquitecto, a petición de la sesión de GCP-05):** (1) `app_core/db/session.py#GCP-05` (marca sembrada): función pura con rango cerrado (pool de 1 a 20, overflow de 0 a 20), que lee `DB_POOL_SIZE` y `DB_MAX_OVERFLOW`, falla cerrado ante un valor inválido, con las variables obligatorias en la nube, sin tocar RLS. (2) El límite de la base no va como anotación de Cloud Run: va en `governance/operaciones/presupuesto_conexiones.yaml` (nuevo; `provisional: true`, las conexiones reservadas y cada consumidor, incluidos los Jobs); la compuerta humana es el `gcloud sql instances describe` del propietario (solo lectura). No hay PgBouncer en los manifiestos de GCP: el presupuesto es contra `max_connections` de Cloud SQL. Con 10 × (5+5) no cabe en 100 − 10: se ajusta `maxScale` o el pool. (3) `tests/test_ci21_sin_import_yaml.py`: solo el «10» por «5» de `_WEB_PRODUCCION` (maxScale del frontend de producción).
- **Dos archivos de EP-04 que cambian con este escalado (propiedad ampliada por el Tech Lead, 2026-11-12, a petición de la sesión; EP-04 hecha, GCP-05 pasa a depender de ella):** producción declara `minScale` 0 (corrección del propietario, 2026-11-13: sin instancia permanente hasta la fase beta; PRD §5.4, pilar 9) y las variables `DB_POOL_SIZE` y `DB_MAX_OVERFLOW`, y `tests/test_ep04_computo_pruebas.py::…[cloudrun_backend]` falla porque `governance/operaciones/entornos/pruebas/cloudrun_backend.yaml` y la lista `CLAUDES_ADMITIDAS` del test no las conocen. Cambio: añadir las dos variables al YAML de pruebas y `minScale` a las claves admitidas. El **pool por entorno (Arquitecto, 2026-11-12, opción C)**: archivo nuevo, entero de GCP-05, `app_core/db/pool.py`, con `opciones_pool() -> dict` (`pool_size`, `max_overflow` y `pool_timeout` si lo usa). Lee `DB_POOL_SIZE` y `DB_MAX_OVERFLOW` del entorno, que se fijan por servicio en `governance/operaciones/cloudrun_service.yaml`; un valor inválido (0, negativo o no entero) → `RuntimeError` al arrancar, sin volver en silencio al valor por defecto; sin variables → valores por defecto explícitos y documentados. En `app_core/db/session.py` la sección `GCP-05` se mueve para **envolver el bloque `try`/`create_async_engine`** (l. 65-70 en `main`): dentro van el import de `opciones_pool` y la llamada con `**opciones_pool()`, y se retiran las marcas vacías de la l. 155; el nombre de la sección no cambia, así que la línea de propiedad sigue siendo `app_core/db/session.py#GCP-05`. Las marcas se mueven en el mismo PR del código. Ninguna ficha viva posee `session.py` entero (GCP-01, RM-02 y SEC-17 están hechas). **Pruebas en `tests/test_gcp05_escalado.py`, cada una con su mutación:** m1 con `DB_POOL_SIZE=3` y `DB_MAX_OVERFLOW=2`, recargar `session.py` da `engine.pool.size() == 3` y overflow 2 (quitar `**opciones_pool()` → rojo); m2 `DB_POOL_SIZE` en 0, «-1» o «x» → `RuntimeError` al importar (devolver el valor por defecto ante uno inválido → rojo); m3 para cada servicio de los `cloudrun_*.yaml`, `max_instances × (pool_size + max_overflow)` ≤ el tope de `presupuesto_conexiones.yaml`, leído con `tests/_lector_yaml.py` sin `import yaml` (subir `max_instances` o `DB_POOL_SIZE` → rojo); m4 sin variables → los valores por defecto documentados (cambiarlos sin cambiar el documento → rojo). Correr `generar_indice_tareas.py --verificar` y `verificar_reparto.py` con el movimiento de la sección.

## Partición (propietario, 2026-11-13)
GCP-05 cierra con lo que entrega el #689: límites, pool por entorno, presupuesto de conexiones, script y pruebas con un servidor local simulado. La corrida real de carga contra el entorno de pruebas y la confirmación de `max_connections` pasan a `GCP-05b`. GCP-06 depende solo de GCP-05.
