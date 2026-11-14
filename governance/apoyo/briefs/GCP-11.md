### BL-310 · operaciones-diagnostico-de-la-revision-00006  (tanda 68)

**Contexto.** Sala: `operaciones`. Depende de: —. Especificaciones: `governance/tareas/GCP-11.md`.

**Objetivo** (en este orden):

1. `GCP-11` — Diagnóstico del arranque de la revisión 00006 de evydentia-backend

**Rastro ¤**:

- `¤versionado-despliegue`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `governance/partes/nube/2026-11-13_DIAGNOSTICO_REVISION_00006.md`
  - `governance/operaciones/BRIEF_PROPIETARIO_REVISION_00006.md`
  - `scripts/verificar_secretos_sin_bom.py`
  - `tests/test_gcp11_secretos_sin_bom.py`
  - `tests/test_gcp11_manifiesto_secretos.py`
  - `tests/test_gcp11_brief_solo_lectura.py`
  - `app_core/config.py#SEC-17`
  - `tests/test_gcp11_bom_configuracion.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- No uses la base ni el proyecto de producción.
- No edites gobernanza reservada (`.github/workflows/`, `verificadores/` incluidos), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `GCP-11`: pytest tests/test_gcp11_secretos_sin_bom.py tests/test_gcp11_manifiesto_secretos.py tests/test_gcp11_brief_solo_lectura.py tests/test_gcp11_bom_configuracion.py + python scripts/generar_indice_tareas.py --verificar con código 0; mutaciones documentadas de cada árbitro; el parte confirma la causa con la salida de los comandos de solo lectura
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.

