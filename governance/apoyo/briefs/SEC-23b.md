### BL-324 · ai-copilot-el-asistente-pasa-la-organizacion-autenticada-al-tope  (tanda 74)

**Contexto.** Sala: `ai_copilot`. Depende de: `SEC-23`, `IA-07`. Especificaciones: `governance/tareas/SEC-23b.md`, `governance/especificaciones/SEC-23b.md`.

**Objetivo** (en este orden):

1. `SEC-23b` — El asistente pasa la organización autenticada al tope de inferencia

**Rastro ¤**:

- `¤seguridad-tenant`: registrado en `VPA_MAP.md`.

**Escribe** (lista exclusiva):

  - `api/routers/implementation_assistant.py`
  - `features/ai_copilot/services/implementation_assistant.py`
  - `tests/test_sec23b_asistente_org.py`

**No hagas:**

- No escribas fuera de la lista anterior ni en otra sala; no importes de otra sala salvo por su pasillo y compuerta.
- No uses la base ni el proyecto de producción.
- No edites gobernanza reservada (`.github/workflows/`, `verificadores/` incluidos), el índice de `TASKS.md`, la bibliografía ni los aportes; si hace falta un parche, entrégalo en el informe.
- No despliegues: el despliegue lo hacen personas.
- No marques la tarea como hecha ni retires tu bloque.

**Hecho si** (árbitro exógeno):

- `SEC-23b`: pytest tests/test_sec23b_asistente_org.py + suites del asistente; mutación documentada
- `python scripts/generar_indice_tareas.py --verificar` con código 0, y el arnés de tres pilares con su línea final.
