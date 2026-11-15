### BL-340 · tipo-de-evidencia-acuse  (tanda 31)

**Contexto.** Sala(s): `evidencias`. Depende de: `EVI-04`, `RET-02`. Especificaciones: `governance/tareas/EVI-05.md` y `governance/especificaciones/EVI-05.md`.

**Objetivo** (en este orden):

1. `EVI-05` — Tipo de evidencia «acuse» en la custodia de documentos generados

**Rastro ¤** (verificado con `git grep -F`, sin contar `governance/tareas/`):

- `¤evidencias`: rastro de la sala de evidencias.

**Escribe** (lista exclusiva):

  - `features/evidencias/services/custodia_generados_engine.py`
  - `tests/test_evi05_tipo_acuse.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su compuerta.
- Cumple el contrato de `governance/especificaciones/EVI-05.md`; ante una contradicción con el PRD o las invariantes, detente e informa.
- No edites archivos de gobernanza reservada, el índice de `TASKS.md`, la bibliografía ni los aportes.
- No toques producción ni una base compartida.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `EVI-05`: pytest tests/test_evi05_tipo_acuse.py tests/test_evi04_custodia_generados.py contra PostgreSQL 16 local + suite de evidencias; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` y `python scripts/verificar_especificaciones.py` con código 0, y el arnés de tres pilares con su línea final.
