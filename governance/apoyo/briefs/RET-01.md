### BL-312 · pasillo-central-configuracion-solo-por-variables-de-entorno  (tanda 70)

**Contexto.** Sala: `pasillo_central`. Depende de: `RET-00`, `GCP-11`. Especificaciones: `governance/tareas/RET-01.md`.

**Objetivo** (en este orden):

1. `RET-01` — Configuración solo por variables de entorno y guardia de base local

**Rastro ¤**:

- `¤seguridad`: registrado en `VPA_MAP.md`.
- `¤arbitro`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `app_core/config.py`
  - `app_core/huellas_produccion.py`
  - `app_core/entorno/guardias.py`
  - `requirements.txt`
  - `.env.example`
  - `governance/operaciones/ENTORNO_LOCAL.md`
  - `scripts/entorno_local.ps1`
  - `tests/conftest.py`
  - `alembic/env.py`
  - `.githooks/pre-push`
  - `scripts/capacidades_biblioteca.py`
  - `scripts/crear_organizacion_dev.py`
  - `scripts/demo/sembrar_plantilla.py`
  - `scripts/sembrar_entorno_pruebas.py`
  - `tests/test_sec15_guarda_arranque.py`
  - `tests/test_ret01_configuracion.py`
  - `tests/plataforma_unica/pendientes/RET-01.txt`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- No uses la base ni el proyecto de producción.
- No edites gobernanza reservada (`.github/workflows/`, `verificadores/` incluidos), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `RET-01`: pytest tests/test_ret01_configuracion.py tests/test_sec15_guarda_arranque.py tests/test_sec16_secretos_obligatorios.py tests/test_plataforma_unica.py contra un PostgreSQL 16 local + suite completa; prueba de mutación documentada por cada prueba nueva; revisión de Seguridad
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

