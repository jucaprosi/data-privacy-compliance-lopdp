# CI sin Neon: Pruebas de GitHub contra contenedor PostgreSQL 16

> **Histórico · PMV congelado; vigente solo para la rama `produccion`.** Movido desde su ruta anterior por NEON-04 (2026-11-12) con `git mv`; `main` es solo EVYDENTIA.
>
> **Nota sobre el PMV (2026-11-09):** la rama `pmv/consolidacion` se creó a partir de `produccion` (6cf7131d). El trabajo de Aleczandra sobre el PMV va en ramas `pmv/aleczandra/<tema>` con PR hacia `pmv/consolidacion`, probado contra la base de pruebas del PMV `test-aleczandra`; `main` queda solo para EVYDENTIA. Publicar al PMV es un PR de `pmv/consolidacion` hacia `produccion` con aprobación de otra persona, decisión del propietario.

`¤ci-cd` `¤arbitro`

> **Documento operativo de la tarea CI-17 (2026-11-07).**  
> Retiro definitivo de Neon del pipeline de integración continua de GitHub Actions, unificando PRs y push a `main` sobre contenedores locales de PostgreSQL 16 en el runner.

---

## 1. Situación anterior (Antes)

- **Pull Requests (ramas de colaboradores):**
  - Corren contra un servicio en contenedor temporal `postgres:16` (`pgvector/pgvector:pg16`) en el runner, con base vacía migrada en el job y `pytest -n auto`.
- **Push a `main` (fusiones):**
  - Corría en serie contra la rama remota de Neon `test-main`.
  - Serialización forzada mediante espera de turno (`scripts/esperar_turno_neon.py`) para evitar colisiones entre corridas concurrentes.
  - Sincronización de esquema mediante el flujo `.github/workflows/migrar-bases-neon.yml` (`scripts/migrar_bases_neon.py`), que migraba las bases tras cada fusión en `main`.
  - **Duraciones medidas:** El arnés completo en serie contra Neon tardaba habitualmente de 20 a 40 minutos (mediciones documentadas en `VARIACION_NEON_CI.md` registraron entre 7.1 y 35.9 minutos según la región de Azure asignada al runner, debido a la latencia de red hacia Neon). Las fusiones frecuentes en `main` quedaban encoladas o tardaban decenas de minutos en completarse.

---

## 2. Situación actual (Después)

- **Unificación de infraestructura de CI:**
  - Tanto los PRs como el push a `main` ejecutan contra el servicio local en contenedor `pgvector/pgvector:pg16` dentro del propio job de GitHub Actions.
  - La base de datos nace vacía en cada corrida y se migra con `python -m alembic upgrade head` en un paso literal `MIGRATION_DATABASE_URL: postgresql://lopdp_beta_owner:solo-en-este-runner@localhost:5432/lopdp`.
  - Pytest corre siempre en paralelo con `-n auto` (`pytest-xdist`), clonando bases de trabajo aisladas desde la plantilla migrada (`tests/conftest.py`).
  - **Concurrencia sin bloqueos:** Cada corrida del push a `main` tiene su propio contenedor y su propio grupo de concurrencia por `run_id` (`group: ${{ github.workflow }}-${{ github.event_name }}-${{ github.head_ref || github.run_id }}`), eliminando filas de espera y bloqueos mutuos.
- **Retiro de componentes superfluos:**
  - Eliminados: `.github/workflows/migrar-bases-neon.yml`, `scripts/migrar_bases_neon.py` y sus pruebas.
  - Eliminados: `scripts/esperar_turno_neon.py` y sus pruebas.

---

## 3. Costo

- **Costo en Neon:** **0 USD.** No hay consumo de cómputo ni almacenamiento en Neon para la integración continua.
- **Costo en GitHub Actions:** **0 USD adicionales** (los minutos consumidos son iguales o significativamente menores, al reducir el «Arnés completo» del push a `main` de 20–40 minutos en serie a unos 3 minutos y medio en paralelo dentro del runner; pytest solo tarda 69 s). La corrida completa de `main` dura unos 10 minutos y la marca «Playwright Frontend», que no dependía de Neon.

---

## 4. Espera de turno en Neon (CI-14)

La tarea `CI-14` evaluaba si mantener, ajustar o retirar la espera de turno en Neon (`scripts/esperar_turno_neon.py`). Queda absorbida y resuelta con la **salida (a): retirar la espera de turno**. Al eliminar Neon del CI, cada corrida dispone de su propia base efímera en su contenedor dedicado, por lo que no existe base compartida por la que hacer fila.

---

## 5. Cómo se comprueba

1. **Prueba unitaria automatizada:** `pytest tests/test_ci17_ci_sin_neon.py -q` pasa en verde verificando ausencia de referencias a Neon en workflows, eliminación de scripts antiguos y presencia de la configuración del contenedor.
2. **Inspección de workflows:** `git grep -i neon -- .github/workflows/` no devuelve ninguna ocurrencia (código de salida 1).
3. **Primera corrida verde del push a `main`:**
   - Corrida `42422811800` (merge del PR #453, commit `a6c7598`, 2026-11-07): éxito. «Arnés completo» de 22:55:06 a 22:58:25 UTC con `2440 passed, 62 skipped` en 69 s contra el contenedor `pgvector/pgvector:pg16`; «Playwright Frontend» de 22:55:06 a 23:04:35; «Arnés Físico Determinista» en verde. Sin pasos de Neon.

---

## 6. Limpieza pendiente (a realizar por el propietario)

Tras confirmar la primera corrida verde del push a `main` sin Neon:

1. **En la consola de Neon ([console.neon.tech](https://console.neon.tech)):**
   - Borrar la rama `test-main`.
   - Borrar las ramas `test-juan-carlos-sec16` y `test-juan-carlos-gcp01`.
2. **En GitHub:**
   - En *Settings* → *Environments*: borrar el entorno `neon-pruebas`.
   - En *Settings* → *Secrets and variables* → *Actions*: borrar el secreto `TEST_DATABASE_URL` (si no es utilizado por flujos fuera de Actions).
