### BL-321 · adpa-compuerta-modular-roadmap  (tanda 74)

**Contexto.** Sala: `roadmap`. Depende de: `RM-01`, `RET-03`. Especificaciones: `governance/tareas/ADPA-12.md`, `governance/especificaciones/ADPA-12.md`.

**Objetivo** (en este orden):

1. `ADPA-12` — Compuerta pública y pasillo modular por ficha en la sala roadmap

**Rastro ¤**:

- `¤adpa`: registrado en `VPA_MAP.md`.
- `¤arbitro`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `governance/especificaciones/ADPA-12.md`
  - `features/roadmap/roadmap_service.py#ADPA-12`
  - `features/roadmap/compuerta/**`
  - `app_core/pasillo/roadmap.py#ADPA-12`
  - `app_core/pasillo/roadmap_fichas/**`
  - `tests/test_adpa_bulkhead.py`
  - `tests/test_adpa12_compuerta_modular.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- Nunca uses la base ni el proyecto de producción, ni el `.env` de la carpeta principal.
- No edites gobernanza reservada (`.github/workflows/`, `verificadores/` incluidos), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `ADPA-12`: python -m pytest tests/test_adpa12_compuerta_modular.py tests/test_adpa_bulkhead.py tests/test_adpa_bulkheads.py tests/test_adpa_dependencias.py tests/test_adpa06_pasillos_secciones.py; mutaciones M1 a M4 documentadas
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.
