+++
id = "GCP-05"
titulo = "Escalado verificable en Cloud Run: límites de instancias, presupuesto de conexiones y prueba de carga"
ola = "C"
estado = "en_curso"
sala = "operaciones"
depende_de = ["GCP-01", "GCP-03", "GCP-04", "GCP-08", "GCP-09", "CI-21", "EP-04"]
propiedad = ["governance/operaciones/cloudrun_service.yaml", "governance/operaciones/cloudrun_frontend_service.yaml", "governance/operaciones/PRUEBA_DE_CARGA.md", "scripts/prueba_carga.py", "tests/test_gcp05_escalado.py", "app_core/db/session.py#GCP-05", "governance/operaciones/presupuesto_conexiones.yaml", "tests/test_ci21_sin_import_yaml.py", "governance/operaciones/entornos/pruebas/cloudrun_backend.yaml", "tests/test_ep04_computo_pruebas.py"]
crea = ["governance/operaciones/presupuesto_conexiones.yaml"]
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
- Backend: mínimo 0 instancias en pruebas y 1 en producción (evita el arranque en frío del primer usuario; cuesta una instancia permanente); máximo 10. Frontend: mínimo 0, máximo 5. El máximo también es un tope de gasto. El propietario los ajusta.
- Meta inicial de la prueba de carga: 200 usuarios simultáneos en lectura con p95 menor que 800 ms y ningún 5xx.

## Pruebas
- `pytest tests/test_gcp05_escalado.py` comprueba que ambos manifiestos declaran mínimo, máximo y concurrencia, y que `max_instancias × tamaño_del_pool ≤ conexiones_de_PgBouncer`.
- `python scripts/prueba_carga.py --entorno pruebas` y su informe; el script se niega a correr contra el host de producción y exige que `GET /api/v1/entorno` responda `pruebas` (`EP-01`).

**Entorno de pruebas (2026-11-05).** El entorno lo definen `PRD_EVYDENTIA_REVENTA_NUBE.md` §5.5 y las tareas `EP-01`…`EP-09`, y sus manifiestos de `governance/operaciones/entornos/pruebas/` fijan allí el mínimo 0 de instancias. La prueba de carga necesita la puesta en marcha (`EP-09`). Como esa ficha va en una tanda posterior, no figura en `depende_de`: si `EP-09` no está hecha cuando se toma esta tarea, la prueba de carga espera.

**Ampliación 2026-11-11 (Arquitecto, a petición de la sesión de GCP-05):** (1) `app_core/db/session.py#GCP-05` (marca sembrada): función pura con rango cerrado (pool de 1 a 20, overflow de 0 a 20), que lee `DB_POOL_SIZE` y `DB_MAX_OVERFLOW`, falla cerrado ante un valor inválido, con las variables obligatorias en la nube, sin tocar RLS. (2) El límite de la base no va como anotación de Cloud Run: va en `governance/operaciones/presupuesto_conexiones.yaml` (nuevo; `provisional: true`, las conexiones reservadas y cada consumidor, incluidos los Jobs); la compuerta humana es el `gcloud sql instances describe` del propietario (solo lectura). No hay PgBouncer en los manifiestos de GCP: el presupuesto es contra `max_connections` de Cloud SQL. Con 10 × (5+5) no cabe en 100 − 10: se ajusta `maxScale` o el pool. (3) `tests/test_ci21_sin_import_yaml.py`: solo el «10» por «5» de `_WEB_PRODUCCION` (maxScale del frontend de producción).
- **Dos archivos de EP-04 que cambian con este escalado (propiedad ampliada por el Tech Lead, 2026-11-12, a petición de la sesión; EP-04 hecha, GCP-05 pasa a depender de ella):** producción pasa a `minScale` 1 y a las variables `DB_POOL_SIZE` y `DB_MAX_OVERFLOW`, y `tests/test_ep04_computo_pruebas.py::…[cloudrun_backend]` falla porque `governance/operaciones/entornos/pruebas/cloudrun_backend.yaml` y la lista `CLAUDES_ADMITIDAS` del test no las conocen. Cambio: añadir las dos variables al YAML de pruebas y `minScale` a las claves admitidas. Lo de `app_core/db/session.py` (mover la sección `#GCP-05` antes de `create_async_engine` y editar la llamada al motor, que está fuera de la sección) está en consulta al Arquitecto.
